"""Validated uploads and explicit public delivery; no directory-wide static serving."""
from __future__ import annotations
import io,json,os,shutil,subprocess,tempfile,uuid
from pathlib import Path
from PIL import Image,ImageOps,UnidentifiedImageError
from fastapi import HTTPException
from .db import now

MAX_UPLOAD=50*1024*1024

def process(raw: bytes, name: str, *, mode='library'):
    if not raw: raise HTTPException(422,'The uploaded file is empty.')
    if len(raw)>MAX_UPLOAD: raise HTTPException(413,'Maximum upload is 50 MB.')
    suffix=Path(name).suffix.lower()
    if raw.startswith(b'%PDF-'):
        if mode in ('image','portrait'): raise HTTPException(422,'Choose a photograph, not a PDF.')
        if len(raw)>20*1024*1024: raise HTTPException(413,'Maximum PDF size is 20 MB.')
        if b'%%EOF' not in raw[-4096:] or any(t in raw for t in (b'/JavaScript',b'/JS',b'/Launch',b'/EmbeddedFile',b'/OpenAction',b'/RichMedia')):
            raise HTTPException(422,'Incomplete PDF or active/embedded actions detected. Upload a plain PDF.')
        return raw,'application/pdf','.pdf','document'
    if suffix in ('.mp4','.webm'):
        if mode!='library': raise HTTPException(422,'Upload videos through the Media library.')
        if (suffix=='.mp4' and raw[4:8]!=b'ftyp') or (suffix=='.webm' and raw[:4]!=b'\x1aE\xdf\xa3'):
            raise HTTPException(422,'This is not a valid MP4 or WebM container.')
        exe=shutil.which('ffprobe')
        if not exe: raise HTTPException(503,'Video uploads require ffprobe. Install it once: sudo apt install ffmpeg')
        with tempfile.TemporaryDirectory(prefix='ted2-video-') as tmp:
            p=Path(tmp)/('upload'+suffix);p.write_bytes(raw)
            try:
                result=subprocess.run([exe,'-v','error','-protocol_whitelist','file,pipe','-f','mov' if suffix=='.mp4' else 'matroska','-show_streams','-show_format','-of','json',str(p)],capture_output=True,timeout=20,check=False)
                info=json.loads(result.stdout);streams=info.get('streams',[])
                video=[s for s in streams if s.get('codec_type')=='video']
                allowed={'h264','av1'} if suffix=='.mp4' else {'vp8','vp9','av1'}
                if result.returncode or not video or len(streams)>4 or any(s.get('codec_type') not in ('video','audio') for s in streams): raise ValueError()
                if any(s.get('codec_name') not in allowed or s.get('width',0)*s.get('height',0)>16_777_216 for s in video): raise ValueError()
                if any(s.get('codec_name') not in {'aac','mp3','opus','vorbis'} for s in streams if s.get('codec_type')=='audio'): raise ValueError()
                if float(info['format'].get('duration',0))<=0: raise ValueError()
            except (ValueError,KeyError,subprocess.TimeoutExpired,OSError):
                raise HTTPException(422,'Unsupported or damaged video. Use H.264 MP4 or VP8/VP9 WebM with ordinary audio.')
        return raw,'video/mp4' if suffix=='.mp4' else 'video/webm',suffix,'video'
    if mode=='document': raise HTTPException(422,'This form accepts PDF documents only.')
    if len(raw)>(5 if mode=='portrait' else 10)*1024*1024: raise HTTPException(413,'Photograph exceeds the upload size limit.')
    try:
        image=Image.open(io.BytesIO(raw))
        if image.format not in ('JPEG','PNG','WEBP') or image.width*image.height>20_000_000: raise ValueError()
        image.load();image=ImageOps.exif_transpose(image).convert('RGB');image.thumbnail((2000,2000))
        stream=io.BytesIO();image.save(stream,format='JPEG',quality=88,optimize=True)
        return stream.getvalue(),'image/jpeg','.jpg','image'
    except (ValueError,OSError,UnidentifiedImageError,Image.DecompressionBombError):
        raise HTTPException(422,'Use a valid JPEG, PNG or WebP photograph under 20 megapixels.')

def persist(store,uploads,raw,name,actor,collection,rid,mode='library'):
    data,mime,ext,kind=process(raw,name,mode=mode)
    uid=uuid.uuid4().hex;target=uploads/(uid+ext)
    target.write_bytes(data);target.chmod(0o600)
    name=Path(name.replace('\\','/')).name[:160]
    name=''.join(c for c in name if ord(c)>=32) or 'upload'+ext
    try:
        with store.connect(write=True) as c:
            c.execute('INSERT INTO uploads VALUES(?,?,?,?,?,?,?,?,?)',(uid,target.name,name,mime,len(data),collection,rid,actor['id'],now()))
            store.audit(c,actor['username'],'upload',collection,rid,after={'id':uid,'name':name,'mime':mime})
    except BaseException:
        target.unlink(missing_ok=True);raise
    return {'id':uid,'url':'/media/'+uid,'mime':mime,'kind':kind,'name':name,'bytes':len(data)}

def publicly_attached(row,p):
    if not p or p.get('visibility')!='public': return False
    uid=row['id'];col=row['collection']
    if col=='media': return p.get('file_id')==uid and p.get('approved') is True
    if col=='settings': return p.get('hero_upload_id')==uid and p.get('hero_permission')=='approved' and row['mime'].startswith('image/')
    if col=='people': return p.get('photo_upload_id')==uid and p.get('photo_permission')=='approved' and row['mime'].startswith('image/')
    return col in ('publications','achievements') and p.get('document_id')==uid and p.get('document_public') is True and row['mime']=='application/pdf'
