<?php
declare(strict_types=1);
namespace Ted2;

/** Bounded, metadata-only reading feed. No arbitrary feeds or generated scientific claims. */
final class Pulse
{
    public function __construct(public ?Store $store=null, private mixed $fetcher=null) {}
    public static function configuration(array $s): array
    {
        $topics=[];foreach(array_slice($s['pulse_topics']??[],0,12) as $topic){$topic=trim(preg_replace('/[^\pL\pN \-]/u','',(string)$topic));if($topic!=='')$topics[]=substr($topic,0,90);}
        return ['enabled'=>(bool)($s['pulse_enabled']??false),'topics'=>array_values(array_unique($topics)),
            'sources'=>array_values(array_intersect(['europepmc','plos-blog'],$s['pulse_sources']??['europepmc'])),
            'policy'=>($s['pulse_policy']??'review')==='source-headlines'?'source-headlines':'review',
            'delivery'=>($s['pulse_delivery']??'local')==='github-scheduled'?'github-scheduled':'local',
            'days'=>max(1,min(180,(int)($s['pulse_lookback']??45))),
            'hours'=>max(1,min(168,(int)($s['pulse_refresh_hours']??6)))];
    }
    public static function digest(array $c): string { return hash('sha256',json($c)); }
    public static function text(mixed $s,int $max=1000): string {return trim(substr(preg_replace('/\s+/u',' ',html_entity_decode(strip_tags((string)$s),ENT_QUOTES|ENT_HTML5,'UTF-8')),0,$max));}
    private function fetch(string $url): array
    {
        if($this->fetcher)return ($this->fetcher)($url);
        $context=stream_context_create(['http'=>['timeout'=>20,'follow_location'=>0,'header'=>"Accept: application/json\r\nUser-Agent: TED2ResearchWorkspace/6.2 (metadata reading desk)\r\n"], 'ssl'=>['verify_peer'=>true,'verify_peer_name'=>true]]);
        $raw=@file_get_contents($url,false,$context,0,4*1024*1024+1);
        ensure(is_string($raw)&&strlen($raw)<=4*1024*1024,503,'The source could not be reached. No new items were fabricated.');
        $data=json_decode($raw,true,512,JSON_THROW_ON_ERROR);ensure(is_array($data),503,'Unexpected source response.');return $data;
    }
    public static function identities(array $row): array
    {
        $ids=['source:'.$row['source_key']];$doi=strtolower(trim($row['doi']??''));$doi=preg_replace('#^https?://(?:dx\.)?doi.org/#','',$doi);
        if($doi)$ids[]='doi:'.$doi;$ids[]='title:'.hash('sha256',strtolower(preg_replace('/[^\pL\pN]/u','',$row['title'])));return $ids;
    }
    public static function tags(array $topics,string $title): array
    {
        $tags=['OpenScience'];foreach($topics as $topic)if(str_contains(strtolower($title),strtolower($topic)))$tags[]=preg_replace('/[^\pL\pN_-]/u','',ucwords($topic));return array_slice(array_values(array_unique($tags)),0,8);
    }
    public function collect(array $config): array
    {
        $items=[];$errors=[];$successful=[];$since=gmdate('Y-m-d',time()-$config['days']*86400);$until=gmdate('Y-m-d');
        if(!$config['enabled']||!$config['topics']||!$config['sources'])return ['items'=>[],'errors'=>[],'successful'=>[]];
        foreach($config['sources'] as $source){try{
            if($source==='europepmc'){
                $query='('.implode(' OR ',array_map(fn($v)=>'"'.$v.'"',$config['topics'])).') AND FIRST_PDATE:['.$since.' TO '.$until.'] sort_date:y';
                $data=$this->fetch('https://www.ebi.ac.uk/europepmc/webservices/rest/search?'.http_build_query(['query'=>$query,'format'=>'json','pageSize'=>30,'resultType'=>'lite']));
                ensure(is_array($data['resultList']['result']??null),503,'Europe PMC returned an unexpected response.');
                foreach($data['resultList']['result'] as $r){$rid=(string)($r['id']??'');$src=(string)($r['source']??'MED');$title=self::text($r['title']??'');$date=(string)($r['firstPublicationDate']??'');
                    if(!$rid||!$title||!preg_match('/^\d{4}-\d{2}-\d{2}$/D',$date)||$date<$since||$date>$until)continue;
                    $items[]=['title'=>$title,'source_url'=>'https://europepmc.org/article/'.rawurlencode($src).'/'.rawurlencode($rid),'source_label'=>'Europe PMC','authors'=>self::text($r['authorString']??'',600),'published_date'=>$date,'fetched_at'=>utc(),'doi'=>self::text($r['doi']??'',250),'source_kind'=>$src==='PPR'?'preprint':'research','source_key'=>'europepmc:'.$src.':'.$rid,'summary'=>'','license'=>'Bibliographic metadata and source link; no article text or images republished.','automatic'=>true,'homepage'=>true,'tags'=>self::tags($config['topics'],$title)];
                }
            }elseif($source==='plos-blog'){
                // Public science-publishing/innovation perspectives; never treated as experiments.
                $query=['per_page'=>30,'after'=>$since.'T00:00:00','_fields'=>'id,date,link,title,excerpt'];
                $data=$this->fetch('https://theplosblog.plos.org/wp-json/wp/v2/posts?'.http_build_query($query));
                ensure(array_is_list($data),503,'PLOS returned an unexpected response.');
                foreach($data as $r){$title=self::text($r['title']['rendered']??'');$date=substr((string)($r['date']??''),0,10);$url=(string)($r['link']??'');$match=strtolower($title.' '.self::text($r['excerpt']['rendered']??'',3000));
                    if(!$title||!safeUrl($url)||!str_ends_with((string)parse_url($url,PHP_URL_HOST),'.plos.org')||!preg_match('/^\d{4}-\d{2}-\d{2}$/D',$date)||$date<$since||$date>$until)continue;
                    if(!array_filter($config['topics'],fn($t)=>str_contains($match,strtolower($t))))continue;
                    $items[]=['title'=>$title,'source_url'=>$url,'source_label'=>'The PLOS Blog','authors'=>'PLOS — authors at source','published_date'=>$date,'fetched_at'=>utc(),'doi'=>'','source_kind'=>'blog','source_key'=>'plos-blog:'.(string)$r['id'],'summary'=>'','license'=>'Headline/link only. PLOS CC BY unless the source states otherwise; images are not copied.','automatic'=>true,'homepage'=>true,'tags'=>self::tags($config['topics'],$match)];
                }
            }$successful[]=$source;
        }catch(\Throwable $e){$errors[]=['source'=>$source,'message'=>$e instanceof Problem?$e->getMessage():'Source response could not be processed.'];}}
        $seen=[];$unique=[];usort($items,fn($a,$b)=>strcmp($b['published_date'],$a['published_date']));
        foreach($items as $row){$ids=self::identities($row);if(array_intersect($ids,array_keys($seen)))continue;foreach($ids as $key)$seen[$key]=true;$unique[]=$row;}
        return ['items'=>array_slice($unique,0,60),'errors'=>$errors,'successful'=>$successful];
    }
    public function state(): array { $r=$this->store?->db->one("SELECT value FROM v6_meta WHERE key='pulse-state'");return $r?decode($r['value']):[]; }
    public function sync(bool $force=false): array
    {
        ensure($this->store!==null,500,'A local store is required.');$s=$this->store->get('settings','laboratory')??[];$config=self::configuration($s);$state=$this->state();
        if(!$config['enabled'])return ['state'=>'disabled','inserted'=>0];
        $lock=fopen(dirname($this->store->db->path).'/pulse.lock','c');if(!flock($lock,LOCK_EX|LOCK_NB)){fclose($lock);return ['state'=>'busy'];}
        try {
            if(!$force&&($state['digest']??'')===self::digest($config)&&time()<(int)($state['next_check']??0))return $state+['skipped'=>true];
            $fetched=$this->collect($config);$count=0;
            foreach($fetched['items'] as $row){$identities=self::identities($row);$rid='pulse-'.substr(hash('sha256',$row['source_key']),0,24);
                $this->store->db->tx(function()use(&$count,$row,$identities,$rid,$config){
                    foreach($identities as $key)if($this->store->db->one('SELECT identity FROM pulse_seen WHERE identity=?',[$key]))return;
                    foreach($identities as $key)$this->store->db->query('INSERT OR IGNORE INTO pulse_seen VALUES(?,?,?)',[$key,$rid,utc()]);
                    if($this->store->get('science_news',$rid,true)||$this->store->db->one('SELECT id FROM trash WHERE collection=? AND id=?',['science_news',$rid]))return;
                    $row['id']=$rid;$row['visibility']=$config['policy']==='source-headlines'?'public':'private';$row['automatic']=$row['visibility']==='public';$row['approved']=false;$row['identity']=implode('|',$identities);$row['internal_notes']='';
                    $this->store->insert('science_news',Schema::validate('science_news',$row),'science-pulse');$count++;
                });
            }
            $result=['state'=>$fetched['errors']?'partial-or-unavailable':'ok','last_check'=>utc(),'last_success'=>$fetched['successful']?utc():($state['last_success']??null),'next_check'=>time()+($fetched['successful']?$config['hours']:1)*3600,'inserted'=>$count,'digest'=>self::digest($config),'errors'=>$fetched['errors'],'successful_sources'=>$fetched['successful']];
            $this->store->db->query("INSERT INTO v6_meta VALUES('pulse-state',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",[json($result)]);return $result;
        }finally{flock($lock,LOCK_UN);fclose($lock);}
    }
    public static function publicRows(PublicSite $site): array
    {
        return array_map(fn($p)=>array_intersect_key($p,array_flip(['id','title','source_url','source_label','authors','published_date','fetched_at','doi','source_kind','summary','license','automatic','tags'])),array_slice($site->data['science_news']??[],0,100));
    }
}
