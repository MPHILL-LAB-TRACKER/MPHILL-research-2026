"""V4 media/publishing endpoints; every mutation retains CSRF, roles and Origin checks."""
from __future__ import annotations
import json,mimetypes,time,uuid
from pathlib import Path
from fastapi import Request,HTTPException
from fastapi.responses import FileResponse
from .db import now
from .security import user_for,write_user,require_admin,verify
from .schema import validate
from .media_v4 import MAX_UPLOAD,persist
from .publisher import Publisher

def install_routes(app):
    from .app import object_body
    store=app.state.store;uploads=app.state.uploads
    app.state.publisher=Publisher(store,uploads)
    def publisher():return app.state.publisher
    @app.post('/api/media/upload')
    async def library_upload(request:Request):
        actor=write_user(request);require_admin(actor)
        async with request.form(max_files=1,max_fields=2,max_part_size=MAX_UPLOAD+1048576) as form:
            file=form.get('file')
            if not file or not hasattr(file,'read'):raise HTTPException(422,'Choose a media file.')
            raw=await file.read(MAX_UPLOAD+1);name=file.filename or 'upload'
        rid='media-'+uuid.uuid4().hex
        result=persist(store,uploads,raw,name,actor,'media',rid)
        p=validate('media',{'id':rid,'title':Path(name.replace('\\','/')).stem[:200] or 'Uploaded file','kind':result['kind'],'file_id':result['id'],'visibility':'private','approved':False})
        try:
            with store.connect(write=True) as c:
                c.execute('INSERT INTO records VALUES(?,?,?,?,1,?,?)',('media',rid,json.dumps(p),p['visibility'],actor['id'],now()))
                store.audit(c,actor['username'],'create','media',rid,after=p)
        except BaseException:
            with store.connect(write=True) as c:
                row=c.execute('SELECT path FROM uploads WHERE id=?',(result['id'],)).fetchone()
                c.execute('DELETE FROM uploads WHERE id=?',(result['id'],))
            if row:(uploads/row['path']).unlink(missing_ok=True)
            raise
        return {'record':store.get('media',rid),'upload':result}
    @app.get('/api/publish/status')
    def status(request:Request):
        actor=user_for(request);require_admin(actor)
        try:return {'ready':True,**publisher().configuration()}
        except HTTPException as error:return {'ready':False,'detail':error.detail}
    @app.post('/api/publish/prepare')
    def prepare(request:Request):
        actor=write_user(request);require_admin(actor)
        return publisher().prepare(actor)
    @app.get('/api/publish/preview/{rid}/{filename:path}')
    def preview(request:Request,rid:str,filename:str):
        actor=user_for(request);require_admin(actor);meta=publisher().manifest(rid,actor)
        if filename not in meta['files']:raise HTTPException(404,'Preview file not found.')
        path=publisher().directory/rid/'site'/filename
        if not path.is_file() or path.is_symlink():raise HTTPException(404,'Preview file missing.')
        return FileResponse(path,media_type=mimetypes.guess_type(filename)[0] or 'application/octet-stream',headers={'Cache-Control':'no-store'})
    @app.post('/api/publish/confirm')
    async def confirm(request:Request):
        from starlette.concurrency import run_in_threadpool
        actor=write_user(request);require_admin(actor);body=await object_body(request,5000)
        stamp=time.time();key='publish:'+actor['id']
        with store.connect(write=True) as c:
            c.execute('DELETE FROM attempts WHERE at<?',(stamp-900,))
            if c.execute('SELECT count(*) FROM attempts WHERE key=?',(key,)).fetchone()[0]>=5:raise HTTPException(429,'Too many password confirmations. Wait 15 minutes.')
            c.execute('INSERT INTO attempts VALUES(?,?)',(key,stamp))
            row=c.execute('SELECT password_hash,active,role FROM users WHERE id=?',(actor['id'],)).fetchone()
        password=body.pop('password','')
        ok=await run_in_threadpool(verify,row['password_hash'],password)
        password=None
        if not ok or not row['active'] or row['role'] not in ('owner','admin'):raise HTTPException(403,'Current administrator password is incorrect.')
        with store.connect(write=True) as c:c.execute('DELETE FROM attempts WHERE key=?',(key,))
        rid=body.get('preview_id','')
        if not isinstance(rid,str):raise HTTPException(422,'A preview ID is required.')
        # No password is passed to Git or stored in the audit trail.
        return await run_in_threadpool(publisher().push,rid,actor)
