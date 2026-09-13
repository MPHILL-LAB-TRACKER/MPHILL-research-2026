<?php
declare(strict_types=1);
require __DIR__.'/../php/bootstrap.php';
use Ted2\{Config,Process,Problem};
use function Ted2\{ensure,decode,dirPrivate,atomic,json};
try {
 $args=$argv;array_shift($args);$target=getenv('HOME').'/Documents/MPhill in biomedical sciences (medical microbiology)/GitHub tracker/MPHILL-research-2026';$yes=false;$dry=false;
 while($args){$a=array_shift($args);if($a==='--target'){$target=array_shift($args)??'';}elseif($a==='--yes')$yes=true;elseif($a==='--dry-run')$dry=true;else throw new Problem(422,'Unknown argument: '.$a);}
 ensure(function_exists('posix_geteuid')?posix_geteuid()!==0:true,403,'Run as your normal user, not root or sudo.');
 $source=realpath(dirname(__DIR__));$target=realpath($target);ensure($target!==false&&$target!==$source,422,'Target must be your existing Git clone, not the extracted package.');
 $git=Process::run(['git','-C',$target,'rev-parse','--show-toplevel']);ensure($git['code']===0&&realpath(trim($git['out']))===$target,422,'Target is not the actual Git repository root.');
 $origin=Process::run(['git','-C',$target,'remote','get-url','origin']);ensure($origin['code']===0&&preg_match('#^(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)MPHILL-LAB-TRACKER/MPHILL-research-2026(?:\.git)?$#iD',trim($origin['out']))===1,422,'The target origin is not the expected laboratory repository.');
 ensure(is_file($source.'/release-manifest.json'),422,'The release manifest is missing. Use the complete release ZIP.');$manifest=decode(file_get_contents($source.'/release-manifest.json'));$hashes=$manifest['files'];
 $prior=decode(file_get_contents($source.'/data/v5-source-hashes.json'));$conflicts=[];
 foreach($hashes as $rel=>$hash){ensure(preg_match('#^[a-zA-Z0-9_.\-/]+$#D',$rel)===1&&!str_contains($rel,'..')&&!preg_match('#^(?:var|\.git|\.venv)/#',$rel),422,'Unsafe release path.');ensure(is_file($source.'/'.$rel)&&!is_link($source.'/'.$rel)&&hash_equals($hash,hash_file('sha256',$source.'/'.$rel)),422,'Release integrity failed: '.$rel);
  $path=$target.'/'.$rel;for($d=dirname($path);$d!==$target;$d=dirname($d))ensure(!is_link($d),422,'A target parent is a symlink: '.$rel);ensure(!is_link($path),422,'Target file is a symlink: '.$rel);
  if(is_file($path)&&$rel!=='.gitignore'&&!hash_equals($hash,hash_file('sha256',$path))&&(!isset($prior[$rel])||!hash_equals($prior[$rel],hash_file('sha256',$path))))$conflicts[]=$rel;
 }
 ensure(!$conflicts,409,'Locally customised files need review before replacement: '.implode(', ',$conflicts));
 // Read the target environment without executing its contents.
 $environment=[];if(is_file($target.'/.env'))foreach(file($target.'/.env',FILE_IGNORE_NEW_LINES) as $line)if(preg_match('/^(TED2_[A-Z_]+)=(.*)$/',trim($line),$m))$environment[$m[1]]=trim($m[2]," \t\"'");
 $db=getenv('TED2_DB')?:($environment['TED2_DB']??($target.'/var/ted2.sqlite3'));if(!str_starts_with($db,'/'))$db=$target.'/'.$db;ensure(is_file($db),422,'Existing database not found. Do not initialise a second installation; confirm your database path.');
 $base=getenv('TED2_BASE_URL')?:($environment['TED2_BASE_URL']??'http://127.0.0.1:8000');$host=parse_url($base,PHP_URL_HOST);$port=parse_url($base,PHP_URL_PORT)?:($host==='127.0.0.1'?8000:443);
 if(in_array($host,['127.0.0.1','localhost'],true)){$fp=@fsockopen($host,$port,$errno,$errstr,0.4);if($fp){fclose($fp);throw new Problem(409,'Stop the current local server with Ctrl+C before upgrading.');}}
 ensure(in_array('sqlite',PDO::getAvailableDrivers(),true)||is_executable($target.'/var/native/ted2-worker'),422,'Install php-sqlite3 first. The optional native adapter may instead be built explicitly; it is not downloaded automatically.');
 $stamp=gmdate('Ymd-His').'-'.substr(bin2hex(random_bytes(4)),0,8);$backup=getenv('HOME').'/TED2-private-backups/v6-'.$stamp;
 printf("\nTED² V6 · in-place PHP upgrade\nSource: %s\nTarget: %s\nDatabase: %s\nPrivate backup: %s\n\nThe existing Git index/branch, accounts, password hashes and uploads are preserved. Old Python source remains available for rollback; V6 runs PHP.\n",$source,$target,$db,$backup);
 if($dry){echo "Dry run passed. No files were changed.\n";exit;}
 if(!$yes){fwrite(STDOUT,'Type UPGRADE to proceed: ');ensure(trim(fgets(STDIN)?:'')==='UPGRADE',400,'Cancelled.');}
 dirPrivate($backup);
 $tar=Process::run(['tar','--exclude=./.git','--exclude=./.venv','--exclude=./var','--exclude=./node_modules','--exclude=./__pycache__','-czf',$backup.'/source-and-config.tar.gz','-C',$target,'.'],seconds:180);ensure($tar['code']===0,500,'Source backup failed. No release files were replaced.');chmod($backup.'/source-and-config.tar.gz',0600);
 // The server is stopped; SQLite backup API (VACUUM INTO) preserves a consistent copy including WAL.
 putenv('TED2_DB='.$db);putenv('TED2_NATIVE='.$target.'/var/native/ted2-worker');$database=new Ted2\Database($db);$database->query('VACUUM INTO ?',[$backup.'/ted2.sqlite3']);unset($database);chmod($backup.'/ted2.sqlite3',0600);
 $uploads=dirname($db).'/uploads';if(is_dir($uploads)){$r=Process::run(['tar','-czf',$backup.'/uploads.tar.gz','-C',dirname($db),'uploads'],seconds:180);ensure($r['code']===0,500,'Upload backup failed; no release files replaced.');chmod($backup.'/uploads.tar.gz',0600);}
 atomic($backup.'/recovery.json',json(['target'=>$target,'database'=>$db,'source_backup'=>'source-and-config.tar.gz','database_backup'=>'ted2.sqlite3','uploads'=>'uploads.tar.gz']));
 foreach($hashes as $rel=>$hash){$path=$target.'/'.$rel;if(!is_dir(dirname($path)))mkdir(dirname($path),0755,true);$bytes=file_get_contents($source.'/'.$rel);if($rel==='.gitignore'&&is_file($path))$bytes=rtrim(file_get_contents($path))."\n\n".$bytes;ensure(file_put_contents($path,$bytes)!==false,500,'Cannot install '.$rel);chmod($path,str_ends_with($rel,'.sh')?0755:0644);}
 copy($source.'/release-manifest.json',$target.'/release-manifest.json');
 $run=Process::run(['php',$target.'/bin/console.php','migrate'],seconds:180,cwd:$target,extra:['TED2_DB'=>$db,'TED2_NATIVE'=>$target.'/var/native/ted2-worker']);atomic($backup.'/migration-report.txt',$run['out']."\n".$run['err']);ensure($run['code']===0,500,'Migration failed. Keep the server stopped and consult '.$backup.'/migration-report.txt. Your backup is intact.');
 echo $run['out'];echo "\nV6 installed.\nCommit source: bash scripts/commit-v6.sh\nStart PHP: bash start.sh\nBackup: $backup\n\nReview any media_review entries in the migration report before publishing.\n";
}catch(Throwable $e){fwrite(STDERR,$e->getMessage()."\n");exit(1);}
