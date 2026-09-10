"""TED² public API and owner/admin/researcher workspace.

Run through manage.py / start.py. SQLite and uploads are outside the web root.
All mutating management routes enforce authentication, Origin, CSRF and roles.
"""
from __future__ import annotations
import io,json,os,re,secrets,sqlite3,time,uuid
from pathlib import Path
from urllib.parse import urlsplit
from PIL import Image,ImageOps,UnidentifiedImageError
from fastapi import FastAPI,Request,HTTPException
from fastapi.responses import HTMLResponse,JSONResponse,FileResponse,RedirectResponse,Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .db import Store,ROOT,now
from .schema import SCHEMAS,RESEARCHER_EDIT,validate
from .security import (COOKIE,HASHER,DUMMY,digest,password_hash,verify,user_for,write_user,same_origin,is_admin,require_admin,require_owner,assigned)
from .public import project_public

MAX_BODY=22*1024*1024
class BodyLimit:
    def __init__(self,app): self.app=app
    async def __call__(self,scope,receive,send):
        if scope['type']!='http': return await self.app(scope,receive,send)
        count=0; too_big=False
        headers=dict(scope.get('headers',[]))
        try: declared=int(headers.get(b'content-length',b'0'))
        except ValueError: declared=MAX_BODY+1
        if declared>MAX_BODY:
            return await JSONResponse({'detail':'Upload exceeds 22 MB request limit.'},status_code=413)(scope,receive,send)
        async def limited():
            nonlocal count,too_big
            m=await receive()
            if m['type']=='http.request':
                count+=len(m.get('body',b''))
                if count>MAX_BODY:
                    too_big=True; raise HTTPException(413,'Request body too large.')
            return m
        await self.app(scope,limited,send)

async def object_body(request,limit=200000):
    if request.headers.get('content-type','').split(';')[0]!='application/json': raise HTTPException(415,'Use application/json.')
    raw=await request.body()
    if len(raw)>limit: raise HTTPException(413,'JSON payload is too large.')
    try: data=json.loads(raw)
    except (ValueError,UnicodeError): raise HTTPException(400,'Malformed JSON.')
    if not isinstance(data,dict): raise HTTPException(400,'A JSON object is required.')
    return data

def clean_error(exc): raise HTTPException(422,str(exc))
def ensure_collection(c):
    if c not in SCHEMAS: raise HTTPException(404,'Collection not found.')
def get_record(store,c,rid):
    ensure_collection(c); p=store.get(c,rid)
    if not p: raise HTTPException(404,'Record not found.')
    return p

def check_references(store,c,p):
    for f in SCHEMAS[c]['fields']:
        if not f['relation']: continue
        vals=p.get(f['key']) or []
        if f['type']!='multi': vals=[vals] if vals else []
        for rid in vals:
            if not store.get(f['relation'],rid): raise HTTPException(422,'A linked '+f['label']+' record no longer exists.')
    if c in ('milestones','updates') and p.get('project_id'):
        project=store.get('projects',p['project_id'])
        members=set(project.get('people',[]))|{project.get('lead_id')}
        if p.get('researcher_id') not in members: raise HTTPException(422,'Add this researcher to the project team before assigning its activity.')
    with store.connect() as con:
        for key,mime in [('photo_upload_id','image/'),('document_id','application/pdf')]:
            if not p.get(key): continue
            up=con.execute('SELECT * FROM uploads WHERE id=?',(p[key],)).fetchone()
            if not up or up['collection']!=c or up['record_id']!=p['id'] or not up['mime'].startswith(mime): raise HTTPException(422,'Upload is not attached to this record or has an incompatible type.')
    if c=='settings' and p['id']!='laboratory': raise HTTPException(422,'The website has one settings record: laboratory.')

def researcher_write(store,u,c,p,old=None):
    if is_admin(u): return
    if c not in RESEARCHER_EDIT: raise HTTPException(403,'Researchers can update their own manuscripts, milestones and activity. Administrators manage the website.')
    if old and (not assigned(store,u,c,old) or old['visibility']=='public'): raise HTTPException(403,'Published content is locked for administrator review. Submit a private update instead.')
    if p['visibility']!='private' or not assigned(store,u,c,p): raise HTTPException(403,'Researchers can save assigned private records only.')
    if c=='manuscripts':
        if old and p.get('people')!=old.get('people'): raise HTTPException(403,'Only an administrator can change the author assignment.')
        if not old and p.get('people')!=[u['researcher_id']]: raise HTTPException(403,'Create a private draft assigned to yourself; an administrator can add coauthors.')
    if old and c in ('milestones','updates') and p.get('researcher_id')!=old.get('researcher_id'): raise HTTPException(403,'Only an administrator can reassign a record.')
    if p.get('project_id'):
        project=store.get('projects',p['project_id'])
        if not project or not assigned(store,u,'projects',project): raise HTTPException(403,'This project is not assigned to you.')

def create_app(db_path=None,base_url=None,production=None):
    production=(os.getenv('TED2_PRODUCTION','0')=='1') if production is None else production
    base_url=(base_url or os.getenv('TED2_BASE_URL','http://127.0.0.1:8000')).rstrip('/')
    parsed=urlsplit(base_url)
    if parsed.scheme not in ('http','https') or not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username:
        raise RuntimeError('TED2_BASE_URL must be an origin such as https://lab.example.org, without a path.')
    if production and parsed.scheme!='https': raise RuntimeError('Production requires an HTTPS TED2_BASE_URL.')
    path=Path(db_path or os.getenv('TED2_DB',str(ROOT/'var/ted2.sqlite3'))).resolve()
    if path.is_relative_to(ROOT/'web'): raise RuntimeError('The database must not be inside the public web directory.')
    store=Store(path); store.initialize()
    uploads=path.parent/'uploads'; uploads.mkdir(parents=True,exist_ok=True)
    try: os.chmod(path.parent,0o700); os.chmod(uploads,0o700)
    except OSError: pass
    app=FastAPI(title='TED² Research Workspace',docs_url=None,redoc_url=None,openapi_url=None)
    app.state.store=store; app.state.origin=base_url; app.state.uploads=uploads; app.state.production=production
    app.add_middleware(BodyLimit)
    hosts=[parsed.hostname]
    if not production: hosts+=['localhost','127.0.0.1','testserver']
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=hosts)
    origins=set(s.strip().rstrip('/') for s in os.getenv('TED2_PUBLIC_ORIGINS','https://mphill-lab-tracker.github.io').split(',') if s.strip())
    @app.middleware('http')
    async def headers(request,call_next):
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
        response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
        if production: response.headers['Strict-Transport-Security']='max-age=31536000'
        if request.url.path.startswith(('/api/','/admin','/workspace','/login','/media/')): response.headers['Cache-Control']='no-store'
        if request.url.path in ('/api/public','/api/health') or request.url.path.startswith('/media/'):
            origin=request.headers.get('origin')
            if origin in origins:
                response.headers['Access-Control-Allow-Origin']=origin
                response.headers['Vary']='Origin'
                # Never enable cross-origin credentials. Private requests remain same-origin.
        if request.url.path in ('/admin','/workspace','/login'):
            response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' https: data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        return response
    app.mount('/assets',StaticFiles(directory=ROOT/'web/assets'),name='assets')
    app.mount('/images',StaticFiles(directory=ROOT/'web/images'),name='images')

    @app.get('/api/health')
    def health(): return {'status':'ok'}
    @app.get('/api/public')
    def public():
        return project_public({c:store.list(c,True) for c in SCHEMAS},base_url)
    @app.get('/')
    def homepage():
        from .build import compile_public
        return HTMLResponse(compile_public({},live=True,api_base=''))
    @app.get('/login')
    def login_page(): return FileResponse(ROOT/'web/admin.html',media_type='text/html')
    @app.get('/admin')
    def admin_page(request:Request):
        u=user_for(request,False)
        if not u: return RedirectResponse('/login?next=admin',303)
        require_admin(u); return FileResponse(ROOT/'web/admin.html',media_type='text/html')
    @app.get('/workspace')
    def workspace_page(request:Request):
        if not user_for(request,False): return RedirectResponse('/login?next=workspace',303)
        return FileResponse(ROOT/'web/admin.html',media_type='text/html')
    @app.get('/api/session')
    def session(request:Request): return {'user':user_for(request,False)}

    @app.post('/api/login')
    async def login(request:Request):
        same_origin(request); body=await object_body(request,5000)
        username=body.get('username',''); password=body.get('password','')
        if not isinstance(username,str) or not isinstance(password,str) or len(username)>80 or len(password)>1024: raise HTTPException(422,'Invalid credentials format.')
        username=username.strip().lower(); ip=request.client.host if request.client else 'unknown'
        key_user='user:'+digest(username); key_ip='ip:'+digest(ip); current=time.time()
        with store.connect(write=True) as c:
            c.execute('DELETE FROM attempts WHERE at<?',(current-900,))
            if c.execute('SELECT COUNT(*) FROM attempts WHERE key=?',(key_user,)).fetchone()[0]>=8 or c.execute('SELECT COUNT(*) FROM attempts WHERE key=?',(key_ip,)).fetchone()[0]>=40:
                raise HTTPException(429,'Too many attempts. Wait 15 minutes before trying again.')
            c.executemany('INSERT INTO attempts VALUES(?,?)',[(key_user,current),(key_ip,current)])
            row=c.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
        valid=verify(row['password_hash'] if row else DUMMY,password)
        if not row or not valid or not row['active']: raise HTTPException(401,'Username or password is incorrect.')
        token=secrets.token_urlsafe(48); csrf=secrets.token_urlsafe(32)
        with store.connect(write=True) as c:
            # Recheck active status after hashing; a revoked account cannot race a new session.
            if not c.execute('SELECT active FROM users WHERE id=?',(row['id'],)).fetchone()[0]: raise HTTPException(401,'Username or password is incorrect.')
            c.execute('DELETE FROM attempts WHERE key=?',(key_user,))
            c.execute('DELETE FROM sessions WHERE expires<?',(current,))
            c.execute('DELETE FROM sessions WHERE token_hash=?',(digest(request.cookies.get(COOKIE,'')),))
            c.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?)',(digest(token),row['id'],csrf,current,current,current+28800))
            if HASHER.check_needs_rehash(row['password_hash']): c.execute('UPDATE users SET password_hash=? WHERE id=?',(HASHER.hash(password),row['id']))
            store.audit(c,row['username'],'login','users',row['id'])
        response=JSONResponse({'ok':True,'role':row['role'],'next':'/workspace' if row['role']=='researcher' else '/admin'})
        response.set_cookie(COOKIE,token,httponly=True,secure=production,samesite='strict',max_age=28800,path='/')
        return response
    @app.post('/api/logout')
    def logout(request:Request):
        u=write_user(request)
        with store.connect(write=True) as c:
            c.execute('DELETE FROM sessions WHERE token_hash=?',(digest(request.cookies.get(COOKIE,'')),))
            store.audit(c,u['username'],'logout','users',u['id'])
        response=JSONResponse({'ok':True}); response.delete_cookie(COOKIE,path='/',secure=production,httponly=True,samesite='strict'); return response
    @app.post('/api/password')
    async def change_password(request:Request):
        u=write_user(request); b=await object_body(request,5000)
        with store.connect() as c: row=c.execute('SELECT password_hash FROM users WHERE id=?',(u['id'],)).fetchone()
        if not verify(row['password_hash'],b.get('current','')): raise HTTPException(403,'Current password is incorrect.')
        try: encoded=password_hash(b.get('password',''))
        except ValueError as e: clean_error(e)
        with store.connect(write=True) as c:
            c.execute('UPDATE users SET password_hash=? WHERE id=?',(encoded,u['id']))
            c.execute('DELETE FROM sessions WHERE user_id=?',(u['id'],))
            store.audit(c,u['username'],'password-change','users',u['id'])
        res=JSONResponse({'ok':True}); res.delete_cookie(COOKIE,path='/'); return res

    @app.get('/api/bootstrap')
    def bootstrap(request:Request):
        u=user_for(request)
        records={c:[p for p in store.list(c) if assigned(store,u,c,p)] for c in SCHEMAS}
        choices={}
        for c in ('people','projects','collaborations','funders'):
            choices[c]=[{'id':p['id'],'name':p.get('name') or p.get('title')} for p in store.list(c) if (c!='projects' and p['visibility']=='public') or assigned(store,u,c,p)]
        return {'user':u,'schemas':SCHEMAS,'records':records,'choices':choices,'origin':base_url}
    @app.get('/api/records/{collection}/{rid}')
    def record(request:Request,collection:str,rid:str):
        u=user_for(request); p=get_record(store,collection,rid)
        if not assigned(store,u,collection,p): raise HTTPException(403,'This record is not assigned to you.')
        return p
    @app.post('/api/records/{collection}')
    async def create_record(request:Request,collection:str):
        u=write_user(request); ensure_collection(collection); body=await object_body(request)
        try: p=validate(collection,body)
        except ValueError as e: clean_error(e)
        researcher_write(store,u,collection,p); check_references(store,collection,p)
        with store.connect(write=True) as c:
            if c.execute('SELECT 1 FROM records WHERE collection=? AND id=?',(collection,p['id'])).fetchone(): raise HTTPException(409,'This record ID already exists.')
            c.execute('INSERT INTO records VALUES(?,?,?,?,1,?,?)',(collection,p['id'],json.dumps(p,ensure_ascii=False),p['visibility'],u['id'],now()))
            store.audit(c,u['username'],'create',collection,p['id'],after=p)
        return store.get(collection,p['id'])
    @app.put('/api/records/{collection}/{rid}')
    async def update_record(request:Request,collection:str,rid:str):
        u=write_user(request); old=get_record(store,collection,rid); body=await object_body(request)
        version=body.pop('_version',None)
        if type(version) is not int: raise HTTPException(428,'The current record version is required.')
        if body.get('id')!=rid: raise HTTPException(422,'Record IDs cannot be changed after creation.')
        try: p=validate(collection,body)
        except ValueError as e: clean_error(e)
        researcher_write(store,u,collection,p,old); check_references(store,collection,p)
        if collection=='settings' and p['visibility']!='public': raise HTTPException(422,'Website settings must remain public.')
        with store.connect(write=True) as c:
            # Recheck the current payload inside the write transaction as well as its version.
            latest=store.record(c.execute('SELECT * FROM records WHERE collection=? AND id=?',(collection,rid)).fetchone())
            if latest['_version']!=version: raise HTTPException(409,'Someone updated this record. Reload it before saving; your unsaved text has been kept on screen.')
            researcher_write(store,u,collection,p,latest)
            c.execute('UPDATE records SET payload=?,visibility=?,version=version+1,updated_at=? WHERE collection=? AND id=?',(json.dumps(p,ensure_ascii=False),p['visibility'],now(),collection,rid))
            store.audit(c,u['username'],'update',collection,rid,before=latest,after=p)
        return store.get(collection,rid)
    # Records are unpublished/archived rather than hard-deleted, retaining their audit history.

    @app.post('/api/uploads/{collection}/{rid}')
    async def upload(request:Request,collection:str,rid:str):
        u=write_user(request); p=get_record(store,collection,rid)
        if not assigned(store,u,collection,p): raise HTTPException(403,'This record is not assigned to you.')
        if not is_admin(u) and (collection not in RESEARCHER_EDIT or p['visibility']=='public'): raise HTTPException(403,'Uploads to published content require an administrator.')
        supported={f['type'] for f in SCHEMAS[collection]['fields']}
        async with request.form(max_files=1,max_fields=2,max_part_size=MAX_BODY) as form:
            file=form.get('file')
            if not file or not hasattr(file,'read'): raise HTTPException(422,'Choose an image or PDF file.')
            original=Path(file.filename or 'upload').name[:160]
            raw=await file.read(20*1024*1024+1)
            if len(raw)>20*1024*1024: raise HTTPException(413,'Maximum document size is 20 MB.')
        uid=uuid.uuid4().hex
        if raw.startswith(b'%PDF-'):
            if 'document' not in supported: raise HTTPException(422,'This form only accepts a portrait image.')
            if b'%%EOF' not in raw[-4096:]: raise HTTPException(422,'This does not appear to be a complete PDF.')
            if any(x in raw for x in (b'/JavaScript',b'/JS ',b'/Launch',b'/EmbeddedFile',b'/OpenAction')): raise HTTPException(422,'PDFs containing active actions or embedded files are not accepted.')
            mime='application/pdf'; ext='.pdf'; output=raw
        else:
            if 'image' not in supported: raise HTTPException(422,'This form accepts a PDF, not an image.')
            if len(raw)>5*1024*1024: raise HTTPException(413,'Maximum portrait size is 5 MB.')
            try:
                image=Image.open(io.BytesIO(raw))
                if image.format not in ('JPEG','PNG','WEBP') or image.width*image.height>20_000_000: raise ValueError('Unsupported image or too many pixels.')
                image.load(); image=ImageOps.exif_transpose(image).convert('RGB'); image.thumbnail((1200,1200))
                buffer=io.BytesIO(); image.save(buffer,format='JPEG',quality=88,optimize=True)
                output=buffer.getvalue(); mime='image/jpeg'; ext='.jpg'
            except (UnidentifiedImageError,OSError,ValueError,Image.DecompressionBombError) as e: raise HTTPException(422,'Use a valid JPEG, PNG or WebP portrait under 20 megapixels.') from e
        target=uploads/(uid+ext); target.write_bytes(output)
        try: os.chmod(target,0o600)
        except OSError: pass
        try:
            with store.connect(write=True) as c:
                c.execute('INSERT INTO uploads VALUES(?,?,?,?,?,?,?,?,?)',(uid,target.name,original,mime,len(output),collection,rid,u['id'],now()))
                store.audit(c,u['username'],'upload',collection,rid,after={'upload_id':uid,'original_name':original,'mime':mime,'bytes':len(output)})
        except Exception:
            target.unlink(missing_ok=True); raise
        return {'id':uid,'mime':mime,'url':'/media/'+uid,'name':original,'bytes':len(output)}
    @app.get('/media/{uid}')
    def media(request:Request,uid:str):
        if not re.fullmatch(r'[0-9a-f]{32}',uid): raise HTTPException(404,'File not found.')
        with store.connect() as c: row=c.execute('SELECT * FROM uploads WHERE id=?',(uid,)).fetchone()
        if not row: raise HTTPException(404,'File not found.')
        p=store.get(row['collection'],row['record_id']); accessible=False
        if p and p['visibility']=='public':
            accessible=(row['mime'].startswith('image/') and p.get('photo_upload_id')==uid and p.get('photo_permission')=='approved') or (row['collection']=='publications' and p.get('document_id')==uid and p.get('document_public') is True)
        if not accessible:
            u=user_for(request)
            if not p or not assigned(store,u,row['collection'],p): raise HTTPException(403,'You do not have access to this file.')
        path=uploads/row['path']
        if not path.is_file() or path.parent!=uploads: raise HTTPException(404,'File not found.')
        return FileResponse(path,media_type=row['mime'],filename=row['original_name'] if row['mime']=='application/pdf' else None,headers={'Content-Security-Policy':"sandbox; default-src 'none'"})

    @app.get('/api/users')
    def users(request:Request):
        u=user_for(request); require_owner(u)
        with store.connect() as c: return [dict(x) for x in c.execute('SELECT id,username,role,researcher_id,active,created_at FROM users ORDER BY username')]
    @app.post('/api/users')
    async def add_user(request:Request):
        u=write_user(request); require_owner(u); b=await object_body(request,5000)
        name=b.get('username',''); role=b.get('role','researcher'); researcher=b.get('researcher_id','')
        if not isinstance(name,str) or not re.fullmatch(r'[a-z0-9][a-z0-9._-]{2,59}',name): raise HTTPException(422,'Use a lowercase username of 3–60 letters, numbers, dots, underscores or hyphens.')
        if role not in ('owner','admin','researcher'): raise HTTPException(422,'Invalid account role.')
        if not isinstance(researcher,str): raise HTTPException(422,'Invalid researcher profile ID.')
        if role=='researcher' and not store.get('people',researcher): raise HTTPException(422,'Link this researcher account to a profile.')
        try: encoded=password_hash(b.get('password',''))
        except ValueError as e: clean_error(e)
        uid=uuid.uuid4().hex
        with store.connect(write=True) as c:
            if c.execute('SELECT 1 FROM users WHERE username=?',(name,)).fetchone(): raise HTTPException(409,'This username already exists.')
            c.execute('INSERT INTO users VALUES(?,?,?,?,?,1,?)',(uid,name,encoded,role,researcher if role=='researcher' else '',now()))
            store.audit(c,u['username'],'account-create','users',uid,after={'username':name,'role':role,'researcher_id':researcher})
        return {'id':uid,'username':name,'role':role}
    @app.put('/api/users/{uid}')
    async def edit_user(request:Request,uid:str):
        u=write_user(request); require_owner(u); b=await object_body(request,5000)
        role=b.get('role'); active=b.get('active'); researcher=b.get('researcher_id','')
        if role not in ('owner','admin','researcher') or type(active) is not bool: raise HTTPException(422,'Invalid role or account status.')
        if not isinstance(researcher,str): raise HTTPException(422,'Invalid researcher profile ID.')
        if role=='researcher' and not store.get('people',researcher): raise HTTPException(422,'Link this account to a researcher profile.')
        encoded=None
        if b.get('password'):
            try: encoded=password_hash(b['password'])
            except ValueError as e: clean_error(e)
        with store.connect(write=True) as c:
            old=c.execute('SELECT id,username,role,researcher_id,active FROM users WHERE id=?',(uid,)).fetchone()
            if not old: raise HTTPException(404,'Account not found.')
            if old['role']=='owner' and old['active'] and (not active or role!='owner') and c.execute("SELECT COUNT(*) FROM users WHERE role='owner' AND active=1").fetchone()[0]<=1: raise HTTPException(409,'At least one active owner must remain.')
            c.execute('UPDATE users SET role=?,active=?,researcher_id=? WHERE id=?',(role,int(active),researcher if role=='researcher' else '',uid))
            if encoded: c.execute('UPDATE users SET password_hash=? WHERE id=?',(encoded,uid))
            c.execute('DELETE FROM sessions WHERE user_id=?',(uid,))
            store.audit(c,u['username'],'account-update','users',uid,before=dict(old),after={'role':role,'active':active,'researcher_id':researcher,'password_reset':bool(encoded)})
        return {'ok':True}
    @app.get('/api/audit')
    def audit(request:Request):
        u=user_for(request); require_admin(u)
        with store.connect() as c: return [dict(x) for x in c.execute('SELECT id,actor,action,collection,record_id,created_at FROM audit ORDER BY id DESC LIMIT 200')]
    @app.get('/api/history/{collection}/{rid}')
    def history(request:Request,collection:str,rid:str):
        u=user_for(request); require_admin(u); get_record(store,collection,rid)
        with store.connect() as c:
            return [dict(x) for x in c.execute('SELECT id,actor,action,before_json,after_json,created_at FROM audit WHERE collection=? AND record_id=? ORDER BY id DESC LIMIT 50',(collection,rid))]
    @app.get('/api/export/{mode}')
    def export(request:Request,mode:str):
        u=user_for(request); require_admin(u)
        if mode not in ('snapshot','connected'): raise HTTPException(404,'Export mode not found.')
        from .build import compile_public
        data=project_public({c:store.list(c,True) for c in SCHEMAS},base_url)
        # A snapshot embeds only already-public, approved local images, never private manuscripts.
        if mode=='snapshot':
            import base64
            for person in data['people']:
                link=person.get('photo_url','')
                if link and link.startswith(base_url+'/media/'):
                    uid=link.rsplit('/',1)[-1]
                    with store.connect() as c: row=c.execute("SELECT * FROM uploads WHERE id=? AND mime LIKE 'image/%'",(uid,)).fetchone()
                    if row and (uploads/row['path']).is_file(): person['photo_url']='data:'+row['mime']+';base64,'+base64.b64encode((uploads/row['path']).read_bytes()).decode()
        html=compile_public({} if mode=='connected' else data,live=mode=='connected',api_base=base_url)
        return Response(html,media_type='text/html',headers={'Content-Disposition':f'attachment; filename="TED2-{mode}-index.html"','Cache-Control':'no-store'})
    return app
