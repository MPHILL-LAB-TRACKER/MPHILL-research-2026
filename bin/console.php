#!/usr/bin/env php
<?php
declare(strict_types=1);
require __DIR__.'/../php/bootstrap.php';
use Ted2\{Store,Auth,Config,PublicSite,Literature,Problem};
use function Ted2\{ensure,id,utc,json,atomic};
function prompt(string $text,bool $secret=false):string {
 if($secret && function_exists('posix_isatty') && posix_isatty(STDIN)){
  fwrite(STDOUT,$text);$state=trim(shell_exec('stty -g')??'');shell_exec('stty -echo');try{$v=trim(fgets(STDIN)?:'');}finally{if($state!=='')shell_exec('stty '.escapeshellarg($state));fwrite(STDOUT,"\n");}return $v;
 }
 fwrite(STDOUT,$text);return trim(fgets(STDIN)?:'');
}
try{
 $command=$argv[1]??'help';$store=new Store();
 switch($command){
 case 'init':
  $store->init();$store->seed();$report=$store->migrate();echo json($report)."\n";
  if(!$store->db->one("SELECT id FROM users WHERE role='owner' AND active=1")){
   $username=strtolower(prompt('Owner username (3–60 lowercase characters): '));ensure(preg_match('/^[a-z0-9][a-z0-9._-]{2,59}$/D',$username)===1,422,'Invalid username.');
   $password=prompt('Owner password (12 or more characters): ',true);$again=prompt('Repeat password: ',true);ensure(hash_equals($password,$again),422,'Passwords do not match.');$hash=Auth::hash($password);$uid=id();$store->db->query('INSERT INTO users VALUES(?,?,?,?,?,?,?)',[$uid,$username,$hash,'owner','',1,utc()]);$store->audit('server-operator','create-owner','users',$uid);echo "Owner created. No default password is used.\n";
  }else echo "Existing owner and password preserved.\n";
  break;
 case 'migrate': $store->init();$store->seed();echo json($store->migrate())."\n";break;
 case 'check':
  echo json(['version'=>Ted2\VERSION,'php'=>PHP_VERSION,'database'=>Config::db(),'adapter'=>$store->db->adapter,'fileinfo'=>extension_loaded('fileinfo'),'gd'=>extension_loaded('gd'),'openssl'=>extension_loaded('openssl'),'argon2id'=>defined('PASSWORD_ARGON2ID'),'origin'=>Config::origin(),'public_url'=>Config::site()])."\n";break;
 case 'build':
  $dest=$argv[2]??(Config::data().'/exports-v6/site');ensure(!file_exists($dest),409,'Build destination exists. Use a new directory rather than overwriting files.');$result=(new PublicSite($store,true))->build($dest);echo json(['destination'=>$dest,'files'=>count($result['files']),'bytes'=>$result['bytes'],'digest'=>$result['digest']])."\n";break;
 case 'literature-sync':echo json((new Literature($store))->sync($argv[2]??null))."\n";break;
 case 'rank':
  $raw=file_get_contents('php://stdin');$input=Ted2\decode($raw);ensure(is_array($input['documents']??null)&&is_array($input['terms']??null),422,'Provide documents and terms arrays.');echo json(Literature::rank($input['documents'],$input['terms'],in_array('--native',$argv,true)))."\n";break;
 default:echo "TED² Research Workspace V6\n\nphp bin/console.php init                 Initialise / preserve owner and seed\nphp bin/console.php migrate              Upgrade existing V5 content in place\nphp bin/console.php check                Runtime and storage information\nphp bin/console.php build DIRECTORY      Export approved public website\nphp bin/console.php literature-sync [ID] Check opted-in literature topics\nphp bin/console.php rank [--native]      Rank JSON metadata from stdin\n\nUse bash start.sh to run the local site.\n";
 }
}catch(Throwable $e){fwrite(STDERR,($e instanceof Problem?$e->getMessage():'Operation failed: '.$e->getMessage())."\n");exit(1);}
