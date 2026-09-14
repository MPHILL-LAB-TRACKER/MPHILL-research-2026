#!/usr/bin/env php
<?php
declare(strict_types=1);
require __DIR__.'/../php/bootstrap.php';
use Ted2\{Store,Config,Literature};
$directory=Config::data();Ted2\dirPrivate($directory);$lock=fopen($directory.'/discovery-worker.lock','c');
if(!flock($lock,LOCK_EX|LOCK_NB)){fwrite(STDERR,"A discovery worker is already running.\n");exit(0);}
$once=in_array('--once',$argv,true);
do {
 try{$store=new Store();$result=(new Literature($store))->sync();if($result['checked']||$result['errors'])fwrite(STDOUT,Ted2\utc().' '.Ted2\json($result)."\n");unset($store);}catch(Throwable $e){fwrite(STDERR,Ted2\utc()." Research source check failed; retry on next cycle.\n");}
 if(!$once)sleep(60);
}while(!$once);
flock($lock,LOCK_UN);fclose($lock);
