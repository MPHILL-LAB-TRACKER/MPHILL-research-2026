<?php
declare(strict_types=1);
namespace Ted2;
/** Additive, repeatable migration: existing values, accounts and uploads are not reset. */
final class Upgrade61 {
 public static function apply(Store $store):array {
  $db=$store->db;
  $db->query('CREATE TABLE IF NOT EXISTS discovery_seen(owner TEXT NOT NULL,identity TEXT NOT NULL,record_id TEXT NOT NULL,seen_at TEXT NOT NULL,PRIMARY KEY(owner,identity))');
  if($db->one("SELECT value FROM v6_meta WHERE key='migration-6.1'"))return ['already_upgraded'=>true];
  $backup=dirname($db->path).'/pre-v6.1-'.gmdate('Ymd-His').'-'.id().'.sqlite3';
  $db->query('VACUUM INTO ?',[$backup]);@chmod($backup,0600);$count=0;
  $db->tx(function()use($store,$db,&$count){
   foreach(Schema::all() as $c=>$schema)foreach($store->list($c) as $p){$changed=false;$v=$p['_version'];unset($p['_version'],$p['_updated_at']);
    foreach($schema['fields'] as $f)if(!array_key_exists($f['key'],$p)){$p[$f['key']]=Schema::default($f);$count++;$changed=true;}
    if($changed)$store->replace($c,$p,$v,'migration-v6.1');
   }
   $seed=decode(file_get_contents(ROOT.'/data/seed.json'));
   foreach($seed['lab_facts']??[] as $p)if(!$store->get('lab_facts',$p['id'],true)&&!$db->one('SELECT id FROM trash WHERE collection=? AND id=?',['lab_facts',$p['id']]))$store->insert('lab_facts',$p,'migration-v6.1');
   // Remember previous matches including trashed records; a refresh must not resurrect them.
   foreach($db->all("SELECT payload FROM records WHERE collection='discoveries'") as $row){$p=decode($row['payload']);$identities=Literature::identities($p['source_id']??'', $p['doi']??'');foreach($identities as $identity)$db->query('INSERT OR IGNORE INTO discovery_seen VALUES(?,?,?,?)',[$p['researcher_id']??'',$identity,$p['id'],utc()]);}
   $db->query("INSERT INTO v6_meta(key,value) VALUES('migration-6.1',?)",[utc()]);$store->audit('server-operator','migrate-v6.1','settings','laboratory');
  });return ['backup'=>$backup,'added_defaults'=>$count,'facts'=>'New source-backed facts are private and require approval.'];
 }
 public static function validate(string $c,array $p):void {
  if($c==='theme')foreach(['notice_seconds'=>[3,120],'fact_seconds'=>[5,120],'fact_max'=>[1,30]] as $k=>$b)ensure(is_numeric($p[$k])&&$p[$k]>=$b[0]&&$p[$k]<=$b[1],422,str_replace('_',' ',$k).' must be between '.$b[0].' and '.$b[1].'.');
  if($c==='settings')foreach(['discovery_hours'=>[1,168],'discovery_days'=>[1,365],'discovery_show_days'=>[1,365]] as $k=>$b)ensure(is_numeric($p[$k])&&$p[$k]>=$b[0]&&$p[$k]<=$b[1],422,'Discovery interval/lookback is out of range.');
  if($c==='procurement')ensure(($p['required_quantity']??0)>0,422,'The required quantity must be greater than zero.');
  if($c==='lab_facts'&&$p['visibility']==='public')ensure($p['approved']===true,422,'Review the source and explicitly approve a fact before publishing.');
 }
}
