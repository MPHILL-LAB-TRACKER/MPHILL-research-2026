<?php
declare(strict_types=1);
namespace Ted2;

/** Additive V7 migration. Existing records, approvals and intentional removals win. */
final class Upgrade7
{
    public static function apply(Store $store): array
    {
        $db=$store->db;
        $db->query('CREATE TABLE IF NOT EXISTS community_messages(id TEXT PRIMARY KEY, receipt_hash TEXT NOT NULL, researcher_id TEXT NOT NULL, subject TEXT NOT NULL, message TEXT NOT NULL, nickname TEXT NOT NULL, consent_public INTEGER NOT NULL, reply TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)');
        $db->query('CREATE TABLE IF NOT EXISTS community_used(key TEXT PRIMARY KEY, expires INTEGER NOT NULL)');
        $db->query('CREATE TABLE IF NOT EXISTS community_limits(key TEXT PRIMARY KEY, count INTEGER NOT NULL, expires INTEGER NOT NULL)');
        if($db->one("SELECT value FROM v6_meta WHERE key='migration-7.0'"))return ['already_upgraded'=>true];
        $backup=dirname($db->path).'/pre-v7-'.gmdate('Ymd-His').'-'.id().'.sqlite3';
        $db->query('VACUUM INTO ?',[$backup]);@chmod($backup,0600);$added=0;
        $db->tx(function()use($store,$db,&$added):void{
            foreach(Schema::all() as $c=>$schema)foreach($store->list($c) as $p){
                $changed=false;$v=$p['_version'];unset($p['_version'],$p['_updated_at']);
                foreach($schema['fields'] as $f)if(!array_key_exists($f['key'],$p)){$p[$f['key']]=Schema::default($f);$changed=true;}
                if($changed)$store->replace($c,$p,$v,'migration-v7');
            }
            $seed=decode(file_get_contents(ROOT.'/data/seed.json'));
            foreach(['science_quotes'=>decode(file_get_contents(ROOT.'/data/v7-reflections.json')),'resources'=>$seed['resources']??[]] as $c=>$rows){
                foreach($rows as $p){
                    if($store->get($c,$p['id'],true)||$db->one('SELECT id FROM trash WHERE collection=? AND id=?',[$c,$p['id']]))continue;
                    $store->insert($c,Schema::validate($c,$p),'migration-v7');$added++;
                }
            }
            $db->query("INSERT INTO v6_meta VALUES('migration-7.0',?)",[utc()]);
            $store->audit('server-operator','migrate-v7','settings','laboratory');
        });
        return ['backup'=>$backup,'added_records'=>$added,'message'=>'V7 adds 32 original, explicitly labelled science reflections and an open-science resource shelf. Existing material is unchanged. Community hosting must be connected before internet responses can arrive.'];
    }

    public static function validate(string $c,array $p):void
    {
        if($c==='settings'){
            ensure(in_array($p['lab_timezone'],\DateTimeZone::listIdentifiers(),true),422,'Choose a valid IANA laboratory time zone.');
            $url=$p['community_endpoint'];
            if($url!=='')ensure(Responses7::validEndpoint($url),422,'Use the HTTPS base address of your deployed workers.dev response service (without a path), or leave it empty for the PHP-hosted service.');
        }
        if(in_array($c,['writing_projects','bench_notes'],true))ensure($p['visibility']==='private',422,'Writing projects and bench notes are private working records. Publish an approved research update separately.');
        if($c==='writing_projects'&&$p['overleaf_url']!==''){
            $u=parse_url($p['overleaf_url']);
            ensure(safeUrl($p['overleaf_url'],true)&&in_array(strtolower($u['host']??''),['www.overleaf.com','overleaf.com'],true)&&empty($u['port']),422,'Link to the genuine HTTPS Overleaf website.');
        }
        if($c==='albums')ensure(($p['scope']==='researcher'&&$p['researcher_id']!=='')||($p['scope']==='laboratory'&&$p['researcher_id']===''),422,'Select one researcher owner, or choose General laboratory with no researcher.');
    }
}
