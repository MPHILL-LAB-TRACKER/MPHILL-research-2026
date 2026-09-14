<?php
/** CLI policy/output contracts without external network traffic. */
declare(strict_types=1);
require __DIR__.'/../php/bootstrap.php';
use Ted2\{Pulse,Process,Publisher};
use function Ted2\{json,atomic};
$count=0;
function ck(bool $ok,string $label):void{global $count;if(!$ok)throw new RuntimeException($label);$count++;echo "PASS $label\n";}
$dir=sys_get_temp_dir().'/ted2-cloud-check-'.bin2hex(random_bytes(5));mkdir($dir,0700);
try {
 $config=Pulse::configuration(['pulse_enabled'=>true,'pulse_topics'=>['biosensor'],'pulse_policy'=>'source-headlines','pulse_delivery'=>'github-scheduled','pulse_sources'=>[]]);
 $run=function(array $c,?array $prior=null,bool $bad=false)use($dir):array{
  $c['digest']=$bad?str_repeat('0',64):Pulse::digest($c);atomic($dir.'/config.json',json($c));
  @unlink($dir.'/output.json');@unlink($dir.'/previous.json');if($prior!==null)atomic($dir.'/previous.json',json($prior));
  return Process::run(['php',Ted2\ROOT.'/scripts/science-pulse.php','--config',$dir.'/config.json','--previous',$dir.'/previous.json','--output',$dir.'/output.json']);
 };
 foreach(['enabled'=>false,'policy'=>'review','delivery'=>'local'] as $key=>$value){$c=$config;$c[$key]=$value;$r=$run($c);ck($r['code']===0&&!is_file($dir.'/output.json'),'No cloud output when '.$key.' is not authorised');}
 $r=$run($config,bad:true);ck($r['code']!==0&&!is_file($dir.'/output.json'),'Mismatched public policy digest is rejected');
 $prior=['digest'=>Pulse::digest($config),'next_check'=>time()+3600,'items'=>[]];$r=$run($config,$prior);ck($r['code']===0&&!is_file($dir.'/output.json'),'Configured interval prevents an early source check');
 $prior=['digest'=>Pulse::digest($config),'next_check'=>0,'last_success'=>'2026-01-01T00:00:00Z','items'=>[['source_key'=>'old-test','published_date'=>'2000-01-01','title'=>'Expired fixture']],'seen'=>[]];
 $r=$run($config,$prior);ck($r['code']===0&&is_file($dir.'/output.json'),'Empty allowlist is processed without any external request');$result=json_decode(file_get_contents($dir.'/output.json'),true);
 ck($result['items']===[],'Expired records leave the cloud feed');ck($result['last_success']===$prior['last_success'],'No successful-source timestamp is invented');
 ck($result['digest']===Pulse::digest($config),'Cloud output binds to the exact published policy');
 ck(!str_contains(file_get_contents($dir.'/output.json'),'private_email'),'Output contains metadata, not a private database export');
} finally {Publisher::removeTree($dir);}
echo "\n$count cloud CLI policy checks passed. No external fetch or GitHub push tested.\n";
