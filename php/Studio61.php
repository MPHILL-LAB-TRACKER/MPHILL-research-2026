<?php
declare(strict_types=1);
namespace Ted2;
/** Small focused editors and reports layered over the existing schema/permission system. */
final class Studio61 {
 public static function handle(Application $app,string $method,string $path,array $u,callable $body):void {
  $s=$app->store;
  if(preg_match('#^/api/portrait/([a-z0-9-]+)$#D',$path,$m)&&$method==='GET'){
   $p=$s->get('people',$m[1]);ensure($p&&$app->records->canRead($u,'people',$p),404,'Profile not available.');
   if(!empty($p['photo_upload_id'])){$row=$s->db->one('SELECT * FROM uploads WHERE id=?',[$p['photo_upload_id']]);if($row&&$row['collection']==='people'&&$row['record_id']===$p['id'])Media::send((new Media($s))->path($row),$row['mime'],private:true);}
   $map=decode(file_get_contents(ROOT.'/data/asset-map.json'));$relative=$map['portraits'][$p['bundled_portrait']??'']??'';
   if($relative){$root=realpath(ROOT.'/data/assets');$file=realpath($root.'/'.$relative);if($file&&str_starts_with($file,$root.'/'))Media::send($file,(new \finfo(FILEINFO_MIME_TYPE))->file($file),private:true);}
   throw new Problem(404,'No local portrait has been attached.');
  }
  if($path==='/api/tracking'&&$method==='GET'){$rid=Records::admin($u)?($_GET['researcher_id']??null):$u['researcher_id'];$app->jsonResponse(Tracking::report($s,$u,$rid?:null));}
  if($path==='/api/literature/status'&&$method==='GET'){Auth::admin($u);$app->jsonResponse((new Literature($s))->status());}
  if(preg_match('#^/api/questionnaire-builder/([a-z0-9-]+)$#D',$path,$m)&&$method==='POST'){
   Auth::admin($u);$survey=$s->get('questionnaires',$m[1]);ensure($survey!==null,404,'Save the questionnaire first.');$b=$body();ensure(($b['survey_version']??null)===$survey['_version'],409,'The questionnaire changed. Reload before saving its questions.');
   $incoming=$b['questions']??null;ensure(is_array($incoming)&&array_is_list($incoming)&&count($incoming)<=60,422,'Use a list of at most 60 questions.');
   $result=$s->db->tx(function()use($s,$app,$u,$survey,$incoming,$b){
    $current=array_values(array_filter($s->list('survey_questions'),fn($p)=>$p['questionnaire_id']===$survey['id']));
    $versions=$b['versions']??[];foreach($current as $p)ensure(($versions[$p['id']]??null)===$p['_version'],409,'A question changed in another editor. Reload the builder.');$kept=[];$saved=[];
    foreach($incoming as $i=>$p){ensure(is_array($p)&&($p['questionnaire_id']??'')===$survey['id'],422,'Question belongs to another questionnaire.');ensure(!isset($kept[$p['id']??'']),422,'Duplicate question ID.');$kept[$p['id']]=true;$p['order']=$i;
     $old=$s->get('survey_questions',$p['id']);if($old)ensure($old['questionnaire_id']===$survey['id'],403,'Cannot replace a question from another questionnaire.');
     $saved[]=$app->records->save($u,'survey_questions',$p,$old?$p['id']:null);
    }
    foreach($current as $p)if(!isset($kept[$p['id']]))$app->records->trash($u,'survey_questions',$p['id'],$p['_version']);
    return $saved;
   });$app->jsonResponse(['questions'=>$result,'message'=>'Questions saved; removed questions are in Trash. Existing response snapshots are unchanged.']);
  }
 }
}
