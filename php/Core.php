<?php
declare(strict_types=1);
namespace Ted2;
use RuntimeException;
final class Problem extends RuntimeException { public function __construct(public int $status,string $message){parent::__construct($message);} }
function ensure(bool $condition,int $status,string $message):void { if(!$condition) throw new Problem($status,$message); }
function utc():string{return gmdate('Y-m-d\TH:i:s\Z');}
function json(mixed $value):string{return json_encode($value,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);}
function decode(string $value):array { $v=json_decode($value,true,512,JSON_THROW_ON_ERROR);ensure(is_array($v),422,'An object or array is required.');return $v; }
function e(mixed $v):string{return htmlspecialchars((string)($v??''),ENT_QUOTES|ENT_SUBSTITUTE,'UTF-8');}
function id():string{return bin2hex(random_bytes(16));}
function slug(string $v):bool{return preg_match('/^[a-z0-9][a-z0-9-]{0,79}$/D',$v)===1;}
function safeUrl(string $u,bool $https=false):bool{if($u==='')return true;$p=parse_url($u);return $p!==false&&isset($p['host'],$p['scheme'])&&in_array(strtolower($p['scheme']),$https?['https']:['http','https'],true)&&!isset($p['user'])&&!isset($p['pass'])&&!preg_match('/[\x00-\x20\x7f]/',$u);}
function dirPrivate(string $p):void{if(!is_dir($p)&&!mkdir($p,0700,true)&&!is_dir($p))throw new RuntimeException('Cannot create private storage.');}
function atomic(string $p,string $bytes):void{dirPrivate(dirname($p));$tmp=$p.'.'.id().'.tmp';ensure(file_put_contents($tmp,$bytes,LOCK_EX)!==false,500,'Cannot write file.');chmod($tmp,0600);ensure(rename($tmp,$p),500,'Cannot replace file.');}
final class Config {
 public static function load():void{if(is_file(ROOT.'/.env'))foreach(file(ROOT.'/.env',FILE_IGNORE_NEW_LINES) as $line){$line=trim($line);if(!$line||str_starts_with($line,'#'))continue;if(preg_match('/^(TED2_[A-Z_]+)=(.*)$/',$line,$m)&&getenv($m[1])===false)putenv($m[1].'='.trim($m[2]," \t\"'"));}}
 public static function get(string $key,string $default=''):string{return getenv($key)===false?$default:(string)getenv($key);}
 public static function db():string{return self::get('TED2_DB',ROOT.'/var/ted2.sqlite3');}
 public static function origin():string{return rtrim(self::get('TED2_BASE_URL','http://127.0.0.1:8000'),'/');}
 public static function production():bool{return self::get('TED2_PRODUCTION')==='1';}
 public static function site():string{return rtrim(self::get('TED2_PUBLIC_URL','https://mphill-lab-tracker.github.io/MPHILL-research-2026'),'/');}
 public static function data():string{return dirname(self::db());}
 public static function secret():string{$p=self::data().'/v6-secret';if(!is_file($p)){dirPrivate(dirname($p));$fp=@fopen($p,'x');if($fp){chmod($p,0600);fwrite($fp,bin2hex(random_bytes(32)));fclose($fp);}}$s=(string)@file_get_contents($p);ensure(strlen($s)===64,503,'Secret storage unavailable.');return $s;}
}
final class Process {
 /** Execute an argument vector without a shell; bound runtime and captured bytes. */
 public static function run(array $args,string $input='',int $seconds=30,?string $cwd=null,array $extra=[]):array{
  $env=getenv();foreach(array_keys($env) as $k)if(str_starts_with($k,'GIT_'))unset($env[$k]);$env=array_merge($env,['GIT_TERMINAL_PROMPT'=>'0','GIT_SSH_COMMAND'=>'ssh -oBatchMode=yes -oStrictHostKeyChecking=yes'],$extra);
  $p=proc_open($args,[0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes,$cwd,$env);ensure(is_resource($p),503,'Required executable could not start.');
  foreach($pipes as $pipe)stream_set_blocking($pipe,false);$out='';$err='';$sent=0;$start=microtime(true);$closed=false;$exit=-1;
  try{while(true){$s=proc_get_status($p);if(!$s['running'])$exit=$s['exitcode'];
    if(!$closed){if($sent<strlen($input)){$n=fwrite($pipes[0],substr($input,$sent,65536));if($n!==false)$sent+=$n;}if($sent>=strlen($input)){fclose($pipes[0]);$closed=true;}}
    $out.=stream_get_contents($pipes[1]);$err.=stream_get_contents($pipes[2]);ensure(strlen($out)+strlen($err)<128*1024*1024,413,'Process output too large.');
    if(!$s['running'])break;if(microtime(true)-$start>$seconds)throw new Problem(503,'Operation timed out; no success was assumed.');usleep(5000);
   }}catch(\Throwable $e){proc_terminate($p,9);throw $e;}finally{foreach($pipes as $pipe)if(is_resource($pipe))fclose($pipe);$last=proc_close($p);if($exit<0)$exit=$last;}
  return ['code'=>$exit,'out'=>$out,'err'=>$err];
 }
}
