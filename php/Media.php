<?php
declare(strict_types=1);
namespace Ted2;
final class Media {
 const TYPES=['image/jpeg'=>'jpg','image/png'=>'png','image/webp'=>'webp','video/mp4'=>'mp4','video/webm'=>'webm','application/pdf'=>'pdf'];
 public string $directory;
 public function __construct(public Store $store){$this->directory=dirname($store->db->path).'/uploads';dirPrivate($this->directory);}
 public function path(array $row):string{$name=$row['path'];ensure(basename($name)===$name&&!is_link($this->directory.'/'.$name),409,'Invalid stored file path.');$path=$this->directory.'/'.$name;ensure(is_file($path),404,'Stored upload is missing.');return $path;}
 public static function filename(string $name,string $ext):string{$name=basename(str_replace('\\','/',$name));$name=preg_replace('/[\x00-\x1f\x7f<>:"|?*]/','-',$name);$name=trim(pathinfo($name,PATHINFO_FILENAME),'. ');return substr($name?:'download',0,110).'.'.$ext;}
 public function upload(array $u,string $collection,string $rid,array $file):array{
  $p=$this->store->get($collection,$rid);ensure($p!==null,404,'Save the record before uploading.');$records=new Records($this->store);ensure($records->canWrite($u,$collection,$p),403,'This record belongs to another researcher.');
  ensure(($file['error']??1)===UPLOAD_ERR_OK&&is_uploaded_file($file['tmp_name']??''),422,'Choose a file within the server upload limit.');
  $raw=$file['tmp_name'];$original=$file['name']??'upload';$mime=(new \finfo(FILEINFO_MIME_TYPE))->file($raw);$video=in_array($mime,['video/mp4','video/quicktime','video/webm','application/mp4'],true);$size=filesize($raw);ensure($size>0&&$size<=($video?80:20)*1024*1024,413,'Limit: 20 MiB images/PDF, 80 MiB video.');
  $fieldTypes=array_column(Schema::get($collection)['fields'],'type');ensure(array_intersect($fieldTypes,['image','document','asset'])!==[],422,'Upload photographs/videos through the record media gallery.');
  if($collection!=='media'){if(in_array('image',$fieldTypes,true))ensure(str_starts_with($mime,'image/'),422,'This slot accepts a photograph/logo. Use the gallery for videos.');else ensure($mime==='application/pdf',422,'This slot accepts PDF; use Photos, videos & files for mixed content.');}
  $uid=id();$temp=$this->directory.'/'.$uid.'.work';$destination='';$newMime=$mime;
  try{
   if(str_starts_with($mime,'image/')){
    ensure(in_array($mime,['image/jpeg','image/png','image/webp','image/gif','image/bmp','image/x-ms-bmp','image/tiff'],true),422,'Use JPEG, PNG, WebP, GIF, BMP or TIFF. SVG is not accepted as an upload.');
    $info=@getimagesize($raw);if($info)ensure($info[0]*$info[1]<=40000000,413,'Image dimensions exceed 40 megapixels.');
    $ext=in_array($mime,['image/png','image/webp'],true)?'png':'jpg';$destination=$this->directory.'/'.$uid.'.'.$ext;$newMime=$ext==='png'?'image/png':'image/jpeg';
    if(function_exists('imagecreatefromstring')&&$info){$im=@imagecreatefromstring(file_get_contents($raw));ensure($im!==false,422,'This image could not be decoded.');$w=imagesx($im);$h=imagesy($im);$ratio=min(1,2000/max($w,$h));$out=imagecreatetruecolor(max(1,(int)($w*$ratio)),max(1,(int)($h*$ratio)));if($ext==='png'){imagealphablending($out,false);imagesavealpha($out,true);}imagecopyresampled($out,$im,0,0,0,0,imagesx($out),imagesy($out),$w,$h);$ok=$ext==='png'?imagepng($out,$destination,6):imagejpeg($out,$destination,85);imagedestroy($im);imagedestroy($out);ensure($ok,422,'Image conversion failed.');}
    else{$r=Process::run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-i',$raw,'-frames:v','1','-vf','scale=w=min(2000\,iw):h=min(2000\,ih):force_original_aspect_ratio=decrease','-threads','1',$destination],seconds:45);ensure($r['code']===0&&is_file($destination),422,'Image conversion failed. Install ffmpeg or PHP GD.');}
   }elseif($video){
    $probe=Process::run(['ffprobe','-v','error','-show_entries','stream=codec_name,codec_type,width,height:format=duration','-of','json',$raw],seconds:30);ensure($probe['code']===0,422,'Cannot validate video. Install ffmpeg (which provides ffprobe).');$meta=decode($probe['out']);$streams=$meta['streams']??[];$v=array_values(array_filter($streams,fn($s)=>($s['codec_type']??'')==='video'));ensure(count($v)>=1&&($v[0]['width']??0)*($v[0]['height']??0)<=40000000,422,'Invalid video dimensions.');ensure((float)($meta['format']['duration']??0)>0&&(float)$meta['format']['duration']<=3600,422,'Use a recording shorter than one hour.');
    $destination=$this->directory.'/'.$uid.'.mp4';$newMime='video/mp4';
    $r=Process::run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-i',$raw,'-map','0:v:0','-map','0:a:0?','-vf','scale=w=min(1920\,iw):h=min(1080\,ih):force_original_aspect_ratio=decrease:force_divisible_by=2','-c:v','libx264','-preset','fast','-crf','24','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart','-map_metadata','-1','-threads','2',$destination],seconds:300);
    ensure($r['code']===0&&is_file($destination)&&filesize($destination)<=80*1024*1024,422,'Video conversion failed or exceeded 80 MiB. Compress it before upload.');
   }elseif($mime==='application/pdf'){$destination=$this->directory.'/'.$uid.'.pdf';ensure(str_starts_with(file_get_contents($raw,false,null,0,5),'%PDF-'),422,'Invalid PDF.');ensure(copy($raw,$destination),500,'Cannot save PDF.');}
   else throw new Problem(422,'Unsupported file type. Use a supported photograph, video or PDF.');
   chmod($destination,0600);$ext=self::TYPES[$newMime];$row=['id'=>$uid,'path'=>basename($destination),'original_name'=>self::filename($original,$ext),'mime'=>$newMime,'size'=>filesize($destination),'collection'=>$collection,'record_id'=>$rid,'created_by'=>$u['id'],'created_at'=>utc()];
   $this->store->db->query('INSERT INTO uploads VALUES(?,?,?,?,?,?,?,?,?)',array_values($row));$this->store->audit($u['username'],'upload',$collection,$rid,null,['id'=>$uid,'mime'=>$newMime]);return $row;
  }catch(\Throwable $e){if($destination&&is_file($destination))unlink($destination);throw $e;}
 }
 public function canAccess(array $row,?array $u):bool{
  $p=$this->store->get($row['collection'],$row['record_id']);if(!$p)return false;if($u&&(new Records($this->store))->canRead($u,$row['collection'],$p))return true;
  if(($p['visibility']??'private')!=='public')return false;$id=$row['id'];$c=$row['collection'];$owner=Records::researcherOf($c,$p);if($owner!==''&&$c!=='people'&&($this->store->get('people',$owner)['visibility']??'private')!=='public')return false;
  if($c==='media'){if(($p['scope']??'review')==='review')return false;if(($p['scope']??'')==='researcher'){if(($this->store->get('people',$p['researcher_id'])['visibility']??'private')!=='public')return false;}return !empty($p['approved'])&&($p['file_id']??'')===$id;}
  if($c==='people')return ($p['photo_permission']??'')==='approved'&&($p['photo_upload_id']??'')===$id&&!in_array('photo_url',$p['hidden_fields']??[],true);
  if($c==='settings')return ($p['hero_permission']??'')==='approved'&&($p['hero_upload_id']??'')===$id&&!in_array('hero_image_url',$p['hidden_fields']??[],true);
  if($c==='theme'){foreach(['logo_upload_id'=>'logo_approved','institution_logo_id'=>'institution_logo_approved','footer_logo_id'=>'footer_logo_approved','favicon_id'=>'favicon_approved'] as $field=>$flag)if(($p[$field]??'')===$id&&!empty($p[$flag]))return true;}
  if(in_array($c,['publications','achievements'],true))return !empty($p['document_public'])&&($p['document_id']??'')===$id;
  return false;
 }
 public static function send(string $path,string $mime,string $name='',bool $private=true):never{
  ensure(is_file($path)&&!is_link($path),404,'File not found.');$size=filesize($path);header('Content-Type: '.$mime);header('X-Content-Type-Options: nosniff');header('Cache-Control: '.($private?'private, no-store':'public, max-age=300'));header('Accept-Ranges: bytes');if($name)header("Content-Disposition: ".($mime==='application/pdf'?'attachment':'inline')."; filename*=UTF-8''".rawurlencode($name));
  $start=0;$end=$size-1;$range=$_SERVER['HTTP_RANGE']??'';if($range!==''){ensure(preg_match('/^bytes=(\d*)-(\d*)$/D',$range,$m)===1,416,'Invalid byte range.');if($m[1]==='')$start=max(0,$size-(int)$m[2]);else $start=(int)$m[1];if($m[1]!==''&&$m[2]!=='')$end=min($end,(int)$m[2]);ensure($start<=$end&&$start<$size,416,'Range not available.');http_response_code(206);header("Content-Range: bytes $start-$end/$size");}
  header('Content-Length: '.($end-$start+1));if(($_SERVER['REQUEST_METHOD']??'GET')==='HEAD')exit;$fp=fopen($path,'rb');fseek($fp,$start);$remaining=$end-$start+1;while($remaining>0&&!feof($fp)){set_time_limit(30);$buffer=fread($fp,min(65536,$remaining));echo $buffer;$remaining-=strlen($buffer);}fclose($fp);exit;
 }
}
