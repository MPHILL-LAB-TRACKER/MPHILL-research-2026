"""Checked image/video/PDF ingestion. Active files are never served as executable content."""
from __future__ import annotations
import io,json,os,shutil,subprocess,tempfile,uuid
from pathlib import Path
from PIL import Image,ImageOps,UnidentifiedImageError
from fastapi import HTTPException
from .db import now

MAX_UPLOAD=80*1024*1024
IMAGE_LIMIT=20*1024*1024

def _video(raw:bytes, suffix:str):
    probe=shutil.which('ffprobe')
    if not probe:raise HTTPException(503,'Video support is not installed on this computer. Run: sudo apt install ffmpeg; then retry the upload.')
    if (suffix in ('.mp4','.mov','.m4v') and raw[4:8] not in (b'ftyp',b'moov',b'wide',b'mdat')) or (suffix=='.webm' and raw[:4]!=b'\x1aE\xdf\xa3'):
        raise HTTPException(422,'The contents are not a valid MP4, MOV or WebM video.')
    demux='matroska' if suffix=='.webm' else 'mov'
    with tempfile.TemporaryDirectory(prefix='ted2-video-') as tmp:
        path=Path(tmp)/('source'+suffix);path.write_bytes(raw)
        def inspect(p,fmt):
            result=subprocess.run([probe,'-v','error','-protocol_whitelist','file,pipe','-f',fmt,'-show_streams','-show_format','-of','json',str(p)],capture_output=True,timeout=30,check=False)
            value=json.loads(result.stdout);streams=value.get('streams',[]);videos=[x for x in streams if x.get('codec_type')=='video' and not x.get('disposition',{}).get('attached_pic')]
            if result.returncode or not videos or len(streams)>16:raise ValueError()
            video=videos[0]
            if not 0 < video.get('width',0)*video.get('height',0) <= 33_177_600:raise ValueError()
            if not 0 < float(value['format'].get('duration',0)) <= 7200:raise ValueError()
            return streams,video
        try:
            streams,video=inspect(path,demux)
            normal=(suffix=='.mp4' and video.get('codec_name')=='h264' or suffix=='.webm' and video.get('codec_name') in ('vp8','vp9','av1'))
            normal=normal and all(x.get('codec_type') in ('video','audio') for x in streams) and len(streams)<=4
            allowed_audio={'aac','mp3'} if suffix=='.mp4' else {'opus','vorbis'}
            normal=normal and all(x.get('codec_name') in allowed_audio for x in streams if x.get('codec_type')=='audio')
            if normal:return raw,'video/mp4' if suffix=='.mp4' else 'video/webm',suffix,'video'
            exe=shutil.which('ffmpeg')
            if not exe:raise HTTPException(503,'This recording needs conversion. Install FFmpeg: sudo apt install ffmpeg')
            output=Path(tmp)/'converted.mp4'
            cmd=[exe,'-v','error','-nostdin','-threads','2','-protocol_whitelist','file,pipe','-f',demux,'-i',str(path),
                 '-map','0:V:0','-map','0:a:0?','-map_metadata','-1','-map_chapters','-1','-sn','-dn',
                 '-vf',"scale='min(1920,iw)':-2:force_original_aspect_ratio=decrease,pad=ceil(iw/2)*2:ceil(ih/2)*2",
                 '-c:v','libx264','-preset','veryfast','-crf','24','-pix_fmt','yuv420p','-threads','2',
                 '-c:a','aac','-b:a','128k','-movflags','+faststart','-fs',str(MAX_UPLOAD),str(output)]
            result=subprocess.run(cmd,capture_output=True,timeout=180,check=False)
            if result.returncode or not output.is_file() or output.stat().st_size>=MAX_UPLOAD:raise ValueError()
            inspect(output,'mov')
            return output.read_bytes(),'video/mp4','.mp4','video'
        except HTTPException:raise
        except (ValueError,KeyError,TypeError,subprocess.TimeoutExpired,OSError):
            raise HTTPException(422,'Video could not be validated or converted within three minutes. Use a shorter/compressed H.264 MP4 (up to 80 MB), or VP8/VP9 WebM.')

def process(raw:bytes,name:str,*,mode='library'):
    if not raw:raise HTTPException(422,'The uploaded file is empty.')
    if len(raw)>MAX_UPLOAD:raise HTTPException(413,'Maximum video/upload size is 80 MB. Compress longer recordings first.')
    suffix=Path(name).suffix.lower()
    if raw.startswith(b'%PDF-'):
        if mode in ('image','portrait'):raise HTTPException(422,'Choose an image for this photograph/logo field. Use Attachments for documents.')
        if len(raw)>20*1024*1024:raise HTTPException(413,'Maximum PDF size is 20 MB.')
        if b'%%EOF' not in raw[-4096:] or any(t in raw for t in (b'/JavaScript',b'/JS',b'/Launch',b'/EmbeddedFile',b'/OpenAction',b'/RichMedia')):
            raise HTTPException(422,'Incomplete PDF or active/embedded actions detected. Upload a plain PDF.')
        return raw,'application/pdf','.pdf','document'
    if suffix in ('.mp4','.webm','.mov','.m4v'):
        if mode!='library':raise HTTPException(422,'Use the Photos, videos & files area below this record to attach a video, not the PDF/portrait field.')
        return _video(raw,suffix)
    if mode=='document':raise HTTPException(422,'This particular field is for a PDF. Use Photos, videos & files to add images and videos to the same record.')
    if len(raw)>IMAGE_LIMIT:raise HTTPException(413,'Maximum image size is 20 MB.')
    try:
        image=Image.open(io.BytesIO(raw))
        if image.format not in ('JPEG','PNG','WEBP','GIF','BMP','TIFF') or image.width*image.height>40_000_000:raise ValueError()
        # Animated/multipage images use frame/page one; sanitize and remove metadata.
        image.seek(0);image.load();image=ImageOps.exif_transpose(image);image.thumbnail((2400,2400))
        transparent=image.mode in ('RGBA','LA') or 'transparency' in image.info
        stream=io.BytesIO()
        if transparent:
            image.convert('RGBA').save(stream,format='PNG',optimize=True)
            return stream.getvalue(),'image/png','.png','image'
        image.convert('RGB').save(stream,format='JPEG',quality=88,optimize=True)
        return stream.getvalue(),'image/jpeg','.jpg','image'
    except (ValueError,OSError,UnidentifiedImageError,Image.DecompressionBombError):
        raise HTTPException(422,'Use JPEG/JPG, PNG, WebP, GIF, BMP or TIFF, up to 20 MB and 40 megapixels. GIF/TIFF use the first frame/page. SVG/HTML and executable files are not accepted.')

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
    if not p or p.get('visibility')!='public':return False
    uid=row['id'];col=row['collection'];hidden=p.get('hidden_fields') or []
    if col=='media':return p.get('file_id')==uid and p.get('approved') is True
    if col=='settings':return p.get('hero_upload_id')==uid and p.get('hero_permission')=='approved' and row['mime'].startswith('image/') and 'hero_image_url' not in hidden
    if col=='theme':return p.get('logo_upload_id')==uid and p.get('logo_approved') is True and row['mime'].startswith('image/')
    if col=='people':return p.get('photo_upload_id')==uid and p.get('photo_permission')=='approved' and row['mime'].startswith('image/') and 'photo_url' not in hidden
    return col in ('publications','achievements') and p.get('document_id')==uid and p.get('document_public') is True and row['mime']=='application/pdf'
