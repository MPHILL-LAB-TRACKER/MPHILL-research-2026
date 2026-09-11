"""Deletion/restore, field management and media diagnostics. Admin-only writes."""
from __future__ import annotations
import json, shutil, time
from fastapi import HTTPException, Request
from .db import now
from .schema import SCHEMAS
from .security import user_for, write_user, require_admin, verify

PROTECTED = {'settings', 'theme'}

def dependencies(connection, collection, rid):
    """Find explicit links, including hidden/trash records, before permanent removal."""
    found=[]
    for row in connection.execute('SELECT collection,id,payload FROM records'):
        if (row['collection'],row['id'])==(collection,rid): continue
        payload=json.loads(row['payload']);schema=SCHEMAS.get(row['collection'],{})
        linked=any(f.get('relation')==collection and (rid in (payload.get(f['key']) or []) if f['type']=='multi' else payload.get(f['key'])==rid) for f in schema.get('fields',[]))
        linked=linked or (row['collection']=='fields' and payload.get('target_collection')==collection and payload.get('target_id')==rid)
        if linked:found.append(row['collection']+'/'+row['id'])
    if collection=='people':
        found += ['account/'+row['username'] for row in connection.execute('SELECT username FROM users WHERE researcher_id=?',(rid,))]
    return found

def install_routes(app):
    from .app import object_body
    store=app.state.store

    @app.get('/api/system/info')
    def system_info(request:Request):
        actor=user_for(request);require_admin(actor)
        return {'version':'5.0.0','ffprobe':bool(shutil.which('ffprobe')),'ffmpeg':bool(shutil.which('ffmpeg')),
                'image_formats':['JPEG','JPG','PNG','WebP','GIF (first frame)','BMP','TIFF (first page)'],
                'video_formats':['MP4','WebM','MOV (converted to MP4)'],
                'limits_mb':{'image':20,'video':80,'pdf':20},
                'database':str(store.path),'public_branch':'gh-pages'}

    @app.get('/api/trash')
    def trash_list(request:Request):
        actor=user_for(request);require_admin(actor)
        with store.connect() as c:
            return [{'collection':row['collection'],'id':row['id'],'label':json.loads(row['payload']).get(SCHEMAS[row['collection']]['title'],row['id']),
                     '_version':row['version'],'deleted_at':row['deleted_at'],'deleted_by':row['deleted_by']}
                    for row in c.execute("SELECT r.*,t.deleted_at,t.deleted_by FROM records r JOIN trash t ON r.collection=t.collection AND r.id=t.id WHERE t.state='trashed' ORDER BY t.deleted_at DESC") if row['collection'] in SCHEMAS]

    @app.get('/api/references/{collection}/{rid}')
    def references(request:Request,collection:str,rid:str):
        actor=user_for(request);require_admin(actor)
        if collection not in SCHEMAS:raise HTTPException(404,'Record type not found.')
        with store.connect() as c:return {'references':dependencies(c,collection,rid)}

    @app.post('/api/records/{collection}/{rid}/trash')
    async def trash_record(request:Request,collection:str,rid:str):
        actor=write_user(request);require_admin(actor);body=await object_body(request,5000)
        if collection in PROTECTED:raise HTTPException(422,'Core configuration cannot be deleted. Edit the settings, reset the theme, or hide homepage sections instead.')
        if collection not in SCHEMAS:raise HTTPException(404,'Record type not found.')
        with store.connect(write=True) as c:
            row=c.execute('SELECT * FROM records WHERE collection=? AND id=?',(collection,rid)).fetchone()
            if not row or c.execute('SELECT 1 FROM trash WHERE collection=? AND id=?',(collection,rid)).fetchone():raise HTTPException(404,'Active record not found.')
            if type(body.get('_version')) is not int or row['version']!=body['_version']:raise HTTPException(409,'Record changed. Reload before deleting.')
            c.execute("INSERT INTO trash VALUES(?,?,?,?,'trashed')",(collection,rid,now(),actor['username']))
            c.execute('UPDATE records SET version=version+1 WHERE collection=? AND id=?',(collection,rid))
            store.audit(c,actor['username'],'trash',collection,rid,after={'removed_from_website':True})
        return {'ok':True,'message':'Moved to Trash locally. Publish to GitHub to remove it from the online website.'}

    @app.post('/api/trash/{collection}/{rid}/restore')
    async def restore(request:Request,collection:str,rid:str):
        actor=write_user(request);require_admin(actor);body=await object_body(request,5000)
        with store.connect(write=True) as c:
            row=c.execute("SELECT r.* FROM records r JOIN trash t ON r.collection=t.collection AND r.id=t.id WHERE r.collection=? AND r.id=? AND t.state='trashed'",(collection,rid)).fetchone()
            if not row:raise HTTPException(404,'Trashed record not found.')
            if type(body.get('_version')) is not int or body['_version']!=row['version']:raise HTTPException(409,'Trash record changed. Reload first.')
            payload=json.loads(row['payload']);payload['visibility']='private'
            c.execute('UPDATE records SET payload=?,visibility=?,version=version+1,updated_at=? WHERE collection=? AND id=?',(json.dumps(payload,ensure_ascii=False),'private',now(),collection,rid))
            c.execute('DELETE FROM trash WHERE collection=? AND id=?',(collection,rid))
            store.audit(c,actor['username'],'restore-private',collection,rid)
        return store.get(collection,rid)

    @app.post('/api/trash/{collection}/{rid}/purge')
    async def purge(request:Request,collection:str,rid:str):
        actor=write_user(request);require_admin(actor);body=await object_body(request,5000)
        if collection in PROTECTED:raise HTTPException(422,'Core configuration is protected.')
        if body.get('confirmation')!='DELETE':raise HTTPException(422,'Type DELETE to confirm permanent removal.')
        stamp=time.time();key='delete:'+actor['id']
        with store.connect(write=True) as c:
            c.execute('DELETE FROM attempts WHERE at<?',(stamp-900,))
            if c.execute('SELECT count(*) FROM attempts WHERE key=?',(key,)).fetchone()[0]>=5:raise HTTPException(429,'Too many confirmations. Wait 15 minutes.')
            c.execute('INSERT INTO attempts VALUES(?,?)',(key,stamp))
            account=c.execute('SELECT password_hash FROM users WHERE id=?',(actor['id'],)).fetchone()
        from starlette.concurrency import run_in_threadpool
        if not await run_in_threadpool(verify,account['password_hash'],body.pop('password','')):raise HTTPException(403,'Current administrator password is incorrect.')
        with store.connect(write=True) as c:
            row=c.execute("SELECT r.* FROM records r JOIN trash t ON r.collection=t.collection AND r.id=t.id WHERE r.collection=? AND r.id=? AND t.state='trashed'",(collection,rid)).fetchone()
            if not row:raise HTTPException(404,'Trashed record not found.')
            if type(body.get('_version')) is not int or body['_version']!=row['version']:raise HTTPException(409,'Trash record changed. Reload first.')
            refs=dependencies(c,collection,rid)
            if refs:raise HTTPException(409,'Remove these links before permanent deletion: '+', '.join(refs[:20]))
            files=[r['path'] for r in c.execute('SELECT path FROM uploads WHERE collection=? AND record_id=?',(collection,rid))]
            for name in files:
                path=app.state.uploads/name
                if path.is_symlink() or path.resolve().parent!=app.state.uploads.resolve():raise HTTPException(409,'Unsafe upload path; ask the server operator to review it.')
            c.execute('DELETE FROM uploads WHERE collection=? AND record_id=?',(collection,rid))
            c.execute('DELETE FROM records WHERE collection=? AND id=?',(collection,rid))
            c.execute("UPDATE trash SET state='purged' WHERE collection=? AND id=?",(collection,rid))
            c.execute('UPDATE audit SET before_json=NULL,after_json=NULL WHERE collection=? AND record_id=?',(collection,rid))
            c.execute('DELETE FROM attempts WHERE key=?',(key,))
            store.audit(c,actor['username'],'permanent-delete',collection,rid)
        for name in files:(app.state.uploads/name).unlink(missing_ok=True)
        # Invalidate cached publication previews, which may contain earlier public files.
        publisher=getattr(app.state,'publisher',None)
        if publisher:
            with publisher.lock():
                for path in publisher.directory.iterdir():
                    if path.is_dir() and not path.is_symlink():shutil.rmtree(path)
        return {'ok':True,'message':'Removed from the active database and upload directory. Earlier backups, downloaded copies and Git history are not erased.'}
