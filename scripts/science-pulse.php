#!/usr/bin/env php
<?php
declare(strict_types=1);
require __DIR__.'/../php/bootstrap.php';
use Ted2\{Pulse,Problem};
use function Ted2\{decode,json,ensure,atomic,utc};
/** Cloud worker: reads only exported public configuration, never the laboratory database. */
try {
    $opts=getopt('', ['config:','previous:','output:']);
    ensure(isset($opts['config'],$opts['output']),422,'Use --config PUBLIC_CONFIG --output FEED_JSON [--previous FEED_JSON].');
    $path=$opts['config'];ensure(is_file($path)&&filesize($path)<20000,422,'Public feed configuration is missing or too large.');
    $c=decode(file_get_contents($path));$declared=$c['digest']??'';unset($c['digest']);
    $safe=Pulse::configuration(['pulse_enabled'=>$c['enabled']??false,'pulse_topics'=>$c['topics']??[],'pulse_sources'=>$c['sources']??[],'pulse_policy'=>$c['policy']??'review','pulse_delivery'=>$c['delivery']??'local','pulse_lookback'=>$c['days']??45,'pulse_refresh_hours'=>$c['hours']??6]);
    $digest=Pulse::digest($safe);ensure(hash_equals($declared,$digest),422,'Public feed configuration digest does not match the supported policy.');
    if(!$safe['enabled']||$safe['policy']!=='source-headlines'||$safe['delivery']!=='github-scheduled') {echo "Scheduled source headlines are not enabled in the published configuration.\n";exit;}
    $prior=[];if(isset($opts['previous'])&&is_file($opts['previous'])&&filesize($opts['previous'])<2*1024*1024)$prior=decode(file_get_contents($opts['previous']));
    if(($prior['digest']??'')!==$digest)$prior=[];
    if(time()<(int)($prior['next_check']??0)){echo "Configured interval has not elapsed.\n";exit;}
    $fresh=(new Pulse())->collect($safe);$since=gmdate('Y-m-d',time()-$safe['days']*86400);$byKey=[];
    foreach($prior['items']??[] as $p)if(($p['published_date']??'')>=$since)$byKey[$p['source_key']]=$p;
    $seen=$prior['seen']??[];if(!is_array($seen))$seen=[];$seen=array_slice($seen,-2000);
    foreach($fresh['items'] as $item){$identities=Pulse::identities($item);if(!isset($byKey[$item['source_key']])&&array_intersect($identities,$seen))continue;foreach($identities as $key)$seen[]=$key;$byKey[$item['source_key']]=$item;}
    $items=array_values($byKey);usort($items,fn($a,$b)=>strcmp($b['published_date'],$a['published_date']));$items=array_slice($items,0,60);
    $out=['version'=>1,'digest'=>$digest,'last_check'=>utc(),'last_success'=>$fresh['successful']?utc():($prior['last_success']??null),'next_check'=>time()+($fresh['successful']?$safe['hours']:1)*3600,'items'=>$items,'errors'=>$fresh['errors'],'seen'=>array_slice(array_values(array_unique($seen)),-2000)];
    atomic($opts['output'],json($out));echo count($items)." source-linked records retained; ".count($fresh['errors'])." source warnings.\n";
}catch(Throwable $e){fwrite(STDERR,($e instanceof Problem?$e->getMessage():'Feed could not be processed.')."\n");exit(1);}
