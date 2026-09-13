<?php
declare(strict_types=1);
namespace Ted2;
/** Literature metadata, never generated scientific findings or protocol recommendations. */
final class Literature {
 public function __construct(public Store $store){}
 public function sync(?string $only=null):array{
  $result=['inserted'=>0,'researchers'=>0,'errors'=>[]];foreach($this->store->list('people') as $p){if($only!==null&&$p['id']!==$only)continue;if(empty($p['literature_enabled'])||empty($p['literature_query']))continue;$result['researchers']++;
   try{$key='literature:last:'.$p['id'];$last=$this->store->db->one('SELECT value FROM v6_meta WHERE key=?',[$key]);ensure(!$last||time()-(int)$last['value']>=3600,429,'Literature was checked in the last hour.');
    $query='('.$p['literature_query'].') AND FIRST_PDATE:['.gmdate('Y-m-d',time()-90*86400).' TO '.gmdate('Y-m-d').']';$url='https://www.ebi.ac.uk/europepmc/webservices/rest/search?'.http_build_query(['query'=>$query,'format'=>'json','pageSize'=>50,'resultType'=>'lite','sort'=>'FIRST_PDATE_D']);
    // Fixed HTTPS endpoint, no user-supplied fetch URL, redirects disallowed.
    $ctx=stream_context_create(['http'=>['timeout'=>25,'follow_location'=>0,'header'=>"Accept: application/json\r\nUser-Agent: TED2ResearchWorkspace/6.0\r\n"],'ssl'=>['verify_peer'=>true,'verify_peer_name'=>true]]);$bytes=@file_get_contents($url,false,$ctx,0,4*1024*1024);ensure(is_string($bytes),503,'Europe PMC could not be reached; no results were fabricated.');$data=decode($bytes);
    foreach($data['resultList']['result']??[] as $r){$source=(string)($r['source']??'MED');$sourceId=(string)($r['id']??'');if(!$sourceId)continue;$rid='lit-'.substr(hash('sha256',$p['id'].'|'.$source.'|'.$sourceId),0,32);if($this->store->get('discoveries',$rid,true))continue;$record=['id'=>$rid,'visibility'=>'private','title'=>strip_tags($r['title']??'Untitled source record'),'researcher_id'=>$p['id'],'authors'=>$r['authorString']??'','journal'=>$r['journalTitle']??'','year'=>(string)($r['pubYear']??''),'doi'=>$r['doi']??'','source_url'=>'https://europepmc.org/article/'.rawurlencode($source).'/'.rawurlencode($sourceId),'source_id'=>$source.':'.$sourceId,'fetched_at'=>utc(),'evidence'=>'Literature search match; publication type and relevance require researcher review.','summary'=>'','approved'=>false,'read'=>false,'media_items'=>[]];$this->store->insert('discoveries',Schema::validate('discoveries',$record),'literature-job');$result['inserted']++;}
    $this->store->db->query('INSERT INTO v6_meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',[$key,(string)time()]);
   }catch(\Throwable $e){$result['errors'][]=['researcher'=>$p['id'],'message'=>$e instanceof Problem?$e->getMessage():'Literature response could not be processed.'];}
  }return $result;
 }
 public static function rank(array $documents,array $terms,bool $native=false):array{
  if($native){$r=Process::run([ROOT.'/var/native/ted2-worker','--rank'],json(['documents'=>$documents,'terms'=>$terms])."\n");ensure($r['code']===0,503,'Native ranker failed.');return decode($r['out'])['rows'];}
  return array_map(fn($d)=>['id'=>$d['id'],'score'=>count(array_filter($terms,fn($t)=>$t!==''&&str_contains(strtolower($d['title']),strtolower($t))))],$documents);
 }
}
