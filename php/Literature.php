<?php
declare(strict_types=1);
namespace Ted2;
/** Fixed-host, bounded metadata retrieval. Never generates claims or silently republishes. */
final class Literature {
 public function __construct(public Store $store,private mixed $fetcher=null){}
 public static function identities(string $source,string $doi):array {
  $ids=[];if($source!=='')$ids[]='source:'.strtolower(trim($source));
  $doi=strtolower(trim(preg_replace('#^https?://(?:dx\.)?doi\.org/#i','',$doi)));
  if($doi!=='')$ids[]='doi:'.$doi;return $ids;
 }
 private function meta(string $key,mixed $value):void{$this->store->db->query('INSERT INTO v6_meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',[$key,json($value)]);}
 public function status():array{$rows=$this->store->db->all("SELECT key,value FROM v6_meta WHERE key LIKE 'discovery:%' ORDER BY key");$out=[];foreach($rows as $r)$out[$r['key']]=json_decode($r['value'],true);return $out;}
 public function ingest(array $results,string $owner=''):int {
  $n=0;foreach(array_slice($results,0,50) as $r){
   $source=(string)($r['source']??'MED');$sourceId=(string)($r['id']??'');$title=trim(strip_tags((string)($r['title']??'')));
   if($sourceId===''||$title===''||strlen($sourceId)>200||strlen($title)>4000)continue;
   $doi=(string)($r['doi']??'');$identities=self::identities($source.':'.$sourceId,$doi);$rid='lit-'.substr(hash('sha256',$owner.'|'.$source.'|'.$sourceId),0,32);
   $inserted=$this->store->db->tx(function()use($r,$source,$sourceId,$title,$doi,$identities,$rid,$owner){
    foreach($identities as $key)if($this->store->db->one('SELECT record_id FROM discovery_seen WHERE owner=? AND identity=?',[$owner,$key]))return false;
    $exists=$this->store->get('discoveries',$rid,true)||$this->store->db->one('SELECT id FROM trash WHERE collection=? AND id=?',['discoveries',$rid]);
    foreach($identities as $key)$this->store->db->query('INSERT OR IGNORE INTO discovery_seen VALUES(?,?,?,?)',[$owner,$key,$rid,utc()]);
    if($exists)return false;
    $date=(string)($r['firstPublicationDate']??'');if(!preg_match('/^\d{4}-\d{2}-\d{2}$/D',$date))$date='';
    $p=['id'=>$rid,'visibility'=>'private','title'=>$title,'researcher_id'=>$owner,'authors'=>substr((string)($r['authorString']??''),0,3900),'journal'=>substr((string)($r['journalTitle']??''),0,3900),'year'=>(string)($r['pubYear']??''),'doi'=>$doi,'source_url'=>'https://europepmc.org/article/'.rawurlencode($source).'/'.rawurlencode($sourceId),'source_id'=>$source.':'.$sourceId,'fetched_at'=>utc(),'evidence'=>'Search match, not a verified discovery. Check the original publication, article type, limitations and relevance.','summary'=>'','approved'=>false,'read'=>false,'publication_date'=>$date,'homepage'=>false,'media_items'=>[]];
    $this->store->insert('discoveries',Schema::validate('discoveries',$p),'literature-job');return true;
   });$n+=(int)$inserted;
  }return $n;
 }
 public function sync(?string $only=null):array {
  $s=$this->store->get('settings','laboratory')??[];$hours=max(1,min(168,(int)($s['discovery_hours']??24)));$days=max(1,min(365,(int)($s['discovery_days']??90)));
  $queries=[];if($only===null&&!empty($s['discovery_enabled'])&&!empty($s['discovery_query']))$queries['']=(string)$s['discovery_query'];
  foreach($this->store->list('people') as $p)if(($only===null||$only===$p['id'])&&!empty($p['literature_enabled'])&&!empty($p['literature_query']))$queries[$p['id']]=$p['literature_query'];
  $result=['inserted'=>0,'researchers'=>count(array_filter(array_keys($queries),fn($k)=>$k!=='')),'checked'=>0,'skipped'=>0,'errors'=>[]];$dir=dirname($this->store->db->path);$fp=fopen($dir.'/discovery.lock','c');
  if(!flock($fp,LOCK_EX|LOCK_NB)){fclose($fp);return $result+['busy'=>true];}
  try{foreach($queries as $owner=>$query){$key='discovery:'.($owner?:'laboratory');$row=$this->store->db->one('SELECT value FROM v6_meta WHERE key=?',[$key]);$state=$row?decode($row['value']):[];
   if(time()<(int)($state['next_check']??0)){$result['skipped']++;continue;}
   try{
    $query='('.$query.') AND FIRST_PDATE:['.gmdate('Y-m-d',time()-$days*86400).' TO '.gmdate('Y-m-d').']';
    $url='https://www.ebi.ac.uk/europepmc/webservices/rest/search?'.http_build_query(['query'=>$query,'format'=>'json','pageSize'=>50,'resultType'=>'lite']);
    if($this->fetcher)$data=($this->fetcher)($url);else{
     $ctx=stream_context_create(['http'=>['timeout'=>20,'follow_location'=>0,'header'=>"Accept: application/json\r\nUser-Agent: TED2ResearchWorkspace/6.1\r\n"],'ssl'=>['verify_peer'=>true,'verify_peer_name'=>true]]);
     $bytes=@file_get_contents($url,false,$ctx,0,4*1024*1024+1);ensure(is_string($bytes)&&strlen($bytes)<=4*1024*1024,503,'The Europe PMC service could not be reached. No results were invented.');$data=decode($bytes);
    }
    ensure(is_array($data['resultList']['result']??null),503,'Europe PMC returned an unexpected response.');$n=$this->ingest($data['resultList']['result'],$owner);$result['inserted']+=$n;$result['checked']++;
    $this->meta($key,['last_check'=>utc(),'last_success'=>utc(),'next_check'=>time()+$hours*3600,'inserted'=>$n,'state'=>'ok']);
   }catch(\Throwable $e){$message=$e instanceof Problem?$e->getMessage():'Source response could not be processed.';$result['errors'][]=['researcher'=>$owner?:'laboratory','message'=>$message];$this->meta($key,['last_check'=>utc(),'last_success'=>$state['last_success']??null,'next_check'=>time()+3600,'state'=>'unavailable','message'=>$message]);}
  }}finally{flock($fp,LOCK_UN);fclose($fp);}return $result;
 }
 public static function rank(array $documents,array $terms,bool $native=false):array {
  if($native){$r=Process::run([ROOT.'/var/native/ted2-worker','--rank'],json(['documents'=>$documents,'terms'=>$terms])."\n");ensure($r['code']===0,503,'Native ranker failed.');return decode($r['out'])['rows'];}
  return array_map(fn($d)=>['id'=>$d['id'],'score'=>count(array_filter($terms,fn($t)=>$t!==''&&str_contains(strtolower($d['title']),strtolower($t))))],$documents);
 }
}
