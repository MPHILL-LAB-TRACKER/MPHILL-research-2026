"""Approved public content → immutable, portable release. Private fields are excluded."""
from __future__ import annotations
import base64,hashlib,json,re,sqlite3
from pathlib import Path
from fastapi import HTTPException
from .schema import SCHEMAS
from .public import project_public
from .build import compile_public
from .media_v4 import publicly_attached
MAX_RELEASE=400*1024*1024
EXT={'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','video/mp4':'.mp4','video/webm':'.webm','application/pdf':'.pdf'}

def release_files(store,uploads,*,embedded=False):
    # A single SQLite read snapshot for payloads and attachment metadata.
    with store.connect() as c:
        c.execute('BEGIN')
        records={name:[] for name in SCHEMAS}
        for row in c.execute('SELECT * FROM records WHERE NOT EXISTS(SELECT 1 FROM trash t WHERE t.collection=records.collection AND t.id=records.id) ORDER BY collection,id'):
            if row['collection'] in records: records[row['collection']].append(json.loads(row['payload']))
        attachments={row['id']:dict(row) for row in c.execute('SELECT * FROM uploads')}
    data=project_public(records,'');files={};total=0
    lookup={(collection,p['id']):p for collection,rows in records.items() for p in rows}
    def asset(value):
        nonlocal total
        if not isinstance(value,str): return value
        match=re.fullmatch(r'/media/([a-f0-9]{32})',value)
        if match:
            row=attachments.get(match[1])
            if not row or not publicly_attached(row,lookup.get((row['collection'],row['record_id']))):
                raise HTTPException(409,'A public attachment is no longer approved. Reload the preview.')
            path=uploads/row['path']
            if path.is_symlink() or path.resolve().parent!=uploads.resolve() or not path.is_file(): raise HTTPException(409,'A published attachment is missing. Re-upload it before publishing.')
            mime=row['mime'];blob=path.read_bytes()
        elif value.startswith('data:'):
            match=re.fullmatch(r'data:([^;]+);base64,([A-Za-z0-9+/=]+)',value)
            if not match or match[1] not in EXT: raise HTTPException(422,'Unsupported embedded media.')
            mime=match[1]
            try: blob=base64.b64decode(match[2],validate=True)
            except ValueError: raise HTTPException(422,'Invalid embedded media.')
        else:return value
        if mime not in EXT: raise HTTPException(422,'Unsupported public media type.')
        key='public-media/'+hashlib.sha256(blob).hexdigest()+EXT[mime]
        if key not in files:
            total+=len(blob)
            if total>MAX_RELEASE: raise HTTPException(413,'Public release exceeds 400 MB. Compress recordings before publishing.')
            files[key]=blob
        return 'data:'+mime+';base64,'+base64.b64encode(blob).decode('ascii') if embedded else key
    for collection,rows in data.items():
        for p in rows:
            for key in ('photo_url','document_url','certificate_preview','asset_url','hero_image_url','logo_url'):
                if key in p:p[key]=asset(p[key])
    html=compile_public(data).encode('utf-8')
    if embedded:return {'index.html':html}
    files['index.html']=html;files['.nojekyll']=b''
    return files

def fingerprint(files):
    h=hashlib.sha256()
    for name,data in sorted(files.items()):
        h.update(name.encode()+b'\0'+hashlib.sha256(data).digest())
    return h.hexdigest()

def write_files(files,dest):
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=True)
    for name,blob in files.items():
        path=dest/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(blob)
