<?php
declare(strict_types=1);
namespace Ted2;
final class Schema {
 public static function all():array{static $s;$s??=decode(file_get_contents(ROOT.'/data/schema.json'));return $s;}
 public static function get(string $c):array{$s=self::all();ensure(isset($s[$c]),404,'Unknown content type.');return $s[$c];}
 public static function default(array $f):mixed{return in_array($f['type'],['multi','lines','urls','multi-choice'],true)?[]:($f['type']==='checkbox'?false:(in_array($f['type'],['number','year','percent','weight','money'],true)?null:''));}
 public static function validate(string $c,array $p):array{
  $schema=self::get($c);$allowed=array_merge(['id','visibility'],array_column($schema['fields'],'key'));
  ensure(!array_diff(array_keys($p),$allowed),422,'Unexpected fields in record.');ensure(is_string($p['id']??null)&&slug($p['id']),422,'Use a lowercase record ID with letters, digits and hyphens.');
  ensure(in_array($p['visibility']??'private',['public','private'],true),422,'Choose public or private visibility.');$out=['id'=>$p['id'],'visibility'=>$p['visibility']??'private'];
  foreach($schema['fields'] as $f){$k=$f['key'];$v=$p[$k]??self::default($f);$t=$f['type'];ensure(!$f['required']||!($v===null||$v===''||$v===[]),422,$f['label'].' is required.');
   if(in_array($t,['multi','lines','urls','multi-choice'],true)){ensure(is_array($v)&&array_is_list($v)&&count($v)<=150,422,$f['label'].' must be a list.');foreach($v as $item){ensure(is_string($item)&&strlen($item)<=2000&&trim($item)!=='',422,'Invalid list item.');if($t==='multi-choice')ensure(in_array($item,$f['options'],true),422,'Invalid choice.');if($t==='urls')ensure(safeUrl($item),422,'Invalid URL.');}$v=array_values(array_unique(array_map('trim',$v)));}
   elseif($t==='checkbox'){ensure(is_bool($v),422,$f['label'].' must be true or false.');}
   elseif(in_array($t,['number','year','percent','weight','money'],true)){if($v===''||$v===null)$v=null;else{ensure(is_int($v)||is_float($v),422,$f['label'].' must be numeric.');$bounds=['number'=>[0,10000],'year'=>[1600,2200],'percent'=>[0,100],'weight'=>[1,100],'money'=>[0,1e12]][$t];ensure(is_finite((float)$v)&&$v>=$bounds[0]&&$v<=$bounds[1],422,$f['label'].' is out of range.');if($t!=='money')ensure((int)$v==$v,422,'Whole number required.');}}
   else{ensure(is_string($v)&&strlen($v)<=($t==='textarea'?50000:4000),422,$f['label'].' is too long or invalid.');$v=trim($v);if($t==='select'&&$v!=='')ensure(in_array($v,$f['options'],true),422,'Invalid '.$f['label']);if($t==='url')ensure(safeUrl($v),422,'Use an HTTP(S) URL.');if($t==='email'&&$v!=='')ensure(filter_var($v,FILTER_VALIDATE_EMAIL)!==false,422,'Invalid email address.');if($t==='color')ensure(preg_match('/^#[0-9a-fA-F]{6}$/D',$v)===1,422,'Use a six-digit hex colour.');if($t==='date'&&$v!=='')ensure(preg_match('/^\d{4}-\d{2}-\d{2}$/D',$v)===1&&gmdate('Y-m-d',strtotime($v))===$v,422,'Use a valid YYYY-MM-DD date.');if(in_array($t,['relation','image','document','asset','target'],true)&&$v!=='')ensure(slug($v),422,'Invalid linked record.');}
   $out[$k]=$v;
  }
  if(in_array($c,['contacts','fields'],true)){
   $kind=$out['kind'];$value=$out['value'];
   if($kind==='email')ensure(filter_var($value,FILTER_VALIDATE_EMAIL)!==false,422,'Enter a valid email address.');
   if(in_array($kind,['website','url'],true))ensure($value!==''&&safeUrl($value),422,'Use an absolute HTTP(S) URL.');
   if($kind==='number')ensure(is_numeric($value)&&is_finite((float)$value),422,'Enter a numeric custom-field value.');
   if($kind==='date')ensure(preg_match('/^\d{4}-\d{2}-\d{2}$/D',$value)===1&&gmdate('Y-m-d',strtotime($value))===$value,422,'Use a valid YYYY-MM-DD date.');
  }
  if($c==='settings'&&$out['submission_site']!=='')ensure(safeUrl($out['submission_site'],true),422,'Public submission site must use HTTPS, not a local browser address.');
  if($c==='theme'){ensure($p['id']==='website'&&$out['visibility']==='public',422,'Keep the website theme public with its original ID.');foreach(['font_size'=>[14,22],'content_width'=>[960,1600],'corner_radius'=>[0,28]] as $k=>$b)ensure($out[$k]>=$b[0]&&$out[$k]<=$b[1],422,$k.' is out of range.');}
  if($c==='settings')ensure($p['id']==='laboratory'&&$out['visibility']==='public',422,'Keep the laboratory settings public.');
  if($c==='media'){ensure($out['scope']!=='researcher'||$out['researcher_id']!=='',422,'Select the researcher who owns this media.');ensure($out['scope']==='researcher'||$out['researcher_id']==='',422,'General/review media must not have a researcher owner.');}
  if($c==='sections'&&$out['location']==='researcher-profile')ensure($out['researcher_id']!=='',422,'Choose the profile for this section.');
  if($c==='questions'&&$out['visibility']==='public')ensure($out['status']==='answered'&&$out['answer']!=='',422,'Only answered, approved questions can be public.');
  if($c==='survey_questions'&&$out['kind']==='single-choice')ensure(count($out['options'])>=2,422,'Add at least two answer choices.');
  foreach([['start_date','end_date'],['start_date','due_date']] as [$a,$b])if(!empty($out[$a])&&!empty($out[$b]))ensure($out[$b]>=$out[$a],422,'End date must not precede start date.');
  return $out;
 }
}
final class Records {
 public function __construct(public Store $store){}
 public static function admin(array $u):bool{return in_array($u['role'],['owner','admin'],true);}
 public static function researcherOf(string $c,array $p):string{if($c==='people')return $p['id'];if(!empty($p['researcher_id']))return $p['researcher_id'];if(!empty($p['lead_id']))return $p['lead_id'];if(count($p['people']??[])===1)return $p['people'][0];return '';}
 public function canRead(array $u,string $c,array $p):bool{
  if(self::admin($u))return true;$rid=$u['researcher_id'];if(!$rid)return false;
  if($c==='theme')return true;if($c==='people')return $p['id']===$rid;
  if($c==='fields'){$parent=$this->store->get($p['target_collection'],$p['target_id']);return $parent&&$this->canRead($u,$p['target_collection'],$parent);}
  if(in_array($c,['media','contacts','milestones','updates','achievements','sections','discoveries'],true))return ($p['researcher_id']??'')===$rid;
  if(in_array($c,['projects','manuscripts','publications'],true))return ($p['lead_id']??'')===$rid||in_array($rid,$p['people']??[],true);
  return false;
 }
 public function canWrite(array $u,string $c,array $p,?array $old=null):bool{
  if(self::admin($u))return true;if(!$this->canRead($u,$c,$p)||($old&&!$this->canRead($u,$c,$old)))return false;
  if($c==='people')return !empty($u['edit_profile']);
  if(in_array($c,['contacts','fields','media','sections'],true))return !empty($u['edit_profile'])||!empty($u['edit_research']);
  return !empty($u['edit_research'])&&in_array($c,['milestones','updates','achievements','manuscripts'],true);
 }
 public function references(string $c,array $p,?array $old=null):void{
  foreach(Schema::get($c)['fields'] as $f){$v=$p[$f['key']]??null;if(!$v)continue;
   if($f['relation']){foreach($f['type']==='multi'?$v:[$v] as $rid)ensure($this->store->get($f['relation'],$rid)!==null,422,'The selected '.$f['label'].' no longer exists.');}
   if(in_array($f['type'],['image','document','asset'],true)){$upload=$this->store->db->one('SELECT * FROM uploads WHERE id=?',[$v]);ensure($upload&&$upload['collection']===$c&&$upload['record_id']===$p['id'],422,'Upload belongs to another record.');if($f['type']==='image')ensure(str_starts_with($upload['mime'],'image/'),422,'This field needs an image.');if($f['type']==='document')ensure($upload['mime']==='application/pdf',422,'Use the media gallery for photographs/videos; this document slot is for PDF.');}
  }
  if($c==='fields'){Schema::get($p['target_collection']);ensure($this->store->get($p['target_collection'],$p['target_id'])!==null,422,'Select an existing target record.');}
  $owner=self::researcherOf($c,$p);
  foreach($p['media_items']??[] as $mid){$m=$this->store->get('media',$mid);ensure($m!==null,422,'Media no longer exists.');if(($m['scope']??'review')==='review')ensure(in_array($mid,$old['media_items']??[],true),422,'Review legacy media ownership before attaching it.');else ensure($owner!==''?($m['scope']==='researcher'&&$m['researcher_id']===$owner):$m['scope']==='laboratory',422,'This upload belongs to a different researcher. Use the correct media owner or general laboratory media.');}
  if($c==='media'&&$old&&(($old['scope']??'')!==$p['scope']||($old['researcher_id']??'')!==$p['researcher_id'])){foreach(array_keys(Schema::all()) as $other)foreach($this->store->list($other) as $parent)if(in_array($p['id'],$parent['media_items']??[],true)){$r=self::researcherOf($other,$parent);ensure($p['scope']==='review'||($r?($p['scope']==='researcher'&&$p['researcher_id']===$r):$p['scope']==='laboratory'),409,'Detach this upload from incompatible records before changing its owner.');}}
 }
 public function save(array $u,string $c,array $body,?string $rid=null):array{
  $version=$body['_version']??null;unset($body['_version'],$body['_updated_at']);$p=Schema::validate($c,$body);
  return $this->store->db->tx(function()use($u,$c,$p,$version,$rid){$old=$rid?$this->store->get($c,$rid):null;
   if($rid){ensure($old!==null,404,'Record not found.');ensure($rid===$p['id'],422,'The record ID cannot change.');ensure(is_int($version)&&$version===$old['_version'],409,'Reload this record before saving; another update occurred.');}
   else ensure($this->store->get($c,$p['id'],true)===null,409,'This ID already exists, including in Trash.');
   ensure($this->canWrite($u,$c,$p,$old),403,'You may edit only your assigned profile and content.');
   if(!self::admin($u)){
    ensure($p['visibility']===($old['visibility']??'private'),403,'Only administrators may approve public visibility.');
    foreach(['priority','group','approved','photo_permission','document_public','homepage','navigation','literature_enabled','scope'] as $k)if(array_key_exists($k,$p)){if($k==='scope'&&$c==='media')ensure($p[$k]==='researcher',403,'Researchers must own their media.');else ensure($p[$k]===($old[$k]??Schema::default(['type'=>is_bool($p[$k])?'checkbox':'text'])),403,'Only an administrator can change '.$k.'.');}
   }
   // A researcher may propose a replacement, but a prior approval must not
   // silently approve a different binary or remote portrait.
   if(!self::admin($u)&&$old){
    if($c==='people'&&(($p['photo_upload_id']??'')!==($old['photo_upload_id']??'')||($p['photo_url']??'')!==($old['photo_url']??'')||($p['bundled_portrait']??'')!==($old['bundled_portrait']??'')))$p['photo_permission']='unconfirmed';
    if($c==='media'&&($p['file_id']??'')!==($old['file_id']??'')){$p['approved']=false;$p['visibility']='private';}
   }
   $this->references($c,$p,$old);
   if(!self::admin($u))foreach(Schema::get($c)['fields'] as $field){if(!$field['relation'])continue;$value=$p[$field['key']]??null;if(!$value)continue;foreach($field['type']==='multi'?$value:[$value] as $linked){$parent=$this->store->get($field['relation'],$linked);ensure($parent&&$this->canRead($u,$field['relation'],$parent),403,'You cannot link content outside your researcher workspace.');}}
   $saved=$old?$this->store->replace($c,$p,$version,$u['id']):$this->store->insert($c,$p,$u['id']);$this->store->audit($u['username'],$old?'update':'create',$c,$p['id'],$old,$saved);return $saved;
  });
 }
 public function trash(array $u,string $c,string $rid,int $version):void{
  ensure(!in_array($c,['settings','theme'],true),422,'Clear or hide settings; do not delete the site configuration.');
  $this->store->db->tx(function()use($u,$c,$rid,$version){$p=$this->store->get($c,$rid);ensure($p!==null,404,'Record not found.');ensure($this->canWrite($u,$c,$p)&&$c!=='people'||self::admin($u),403,'You cannot remove this record.');ensure($version===$p['_version'],409,'Reload before deleting.');
   if($c==='people')ensure(!$this->store->db->one('SELECT id FROM users WHERE researcher_id=? AND active=1',[$rid]),409,'Disable or reassign linked accounts before deleting this researcher.');
   $this->store->db->query("INSERT INTO trash VALUES(?,?,?,?,'trashed')",[$c,$rid,utc(),$u['username']]);$this->store->audit($u['username'],'trash',$c,$rid,$p);
  });
 }
}
