<?php
declare(strict_types=1);
namespace Ted2;
use PDO;
/** Both adapters use SQLite prepared statements and the original V5 database. */
final class Database {
 private ?PDO $pdo=null;private mixed $worker=null;private array $pipes=[];private bool $transaction=false;
 public string $adapter;
 public function __construct(public string $path){
  dirPrivate(dirname($path));
  if(in_array('sqlite',PDO::getAvailableDrivers(),true)&&Config::get('TED2_SQLITE_DRIVER')!=='native'){$this->pdo=new PDO('sqlite:'.$path,null,null,[PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION,PDO::ATTR_DEFAULT_FETCH_MODE=>PDO::FETCH_ASSOC]);$this->adapter='pdo-sqlite';}
  else{$binary=Config::get('TED2_NATIVE',ROOT.'/var/native/ted2-worker');ensure(is_executable($binary),503,'Install php-sqlite3, or compile the optional worker with bash bin/build-native.sh.');$this->worker=proc_open([$binary,$path],[0=>['pipe','r'],1=>['pipe','w'],2=>['file','/dev/null','a']],$this->pipes);ensure(is_resource($this->worker),503,'Native SQLite worker unavailable.');stream_set_timeout($this->pipes[1],20);$this->adapter='native-sqlite';}
  $this->query('PRAGMA foreign_keys=ON');$this->query('PRAGMA busy_timeout=15000');
 }
 public function query(string $sql,array $params=[]):array{
  if($this->pdo){$s=$this->pdo->prepare($sql);$s->execute($params);return ['rows'=>$s->columnCount()?$s->fetchAll():[],'changes'=>$s->rowCount()];}
  $bytes=json(['sql'=>$sql,'params'=>array_values($params)])."\n";$offset=0;while($offset<strlen($bytes)){$n=fwrite($this->pipes[0],substr($bytes,$offset));ensure($n!==false&&$n>0,503,'Native connection failed.');$offset+=$n;}
  $line=fgets($this->pipes[1],128*1024*1024);ensure(is_string($line),503,'Native connection timed out.');$v=decode($line);if(empty($v['ok']))throw new \RuntimeException('Database: '.($v['error']??'failed'));return $v;
 }
 public function all(string $sql,array $p=[]):array{return $this->query($sql,$p)['rows'];}
 public function one(string $sql,array $p=[]):?array{return $this->all($sql,$p)[0]??null;}
 public function tx(callable $f,bool $write=true):mixed{
  if($this->transaction)return $f();$this->query($write?'BEGIN IMMEDIATE':'BEGIN');$this->transaction=true;
  try{$r=$f();$this->query('COMMIT');return $r;}catch(\Throwable $e){$this->query('ROLLBACK');throw $e;}finally{$this->transaction=false;}
 }
 public function __destruct(){if(is_resource($this->worker)){foreach($this->pipes as $p)if(is_resource($p))fclose($p);proc_close($this->worker);}}
}
final class Store {
 public Database $db;
 public function __construct(?string $path=null){$this->db=new Database($path??Config::db());}
 public function init():void{
  $this->db->query('PRAGMA journal_mode=WAL');
  $statements=[
   'CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,username TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL CHECK(role IN (\'owner\',\'admin\',\'researcher\')),researcher_id TEXT NOT NULL DEFAULT \'\',active INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL)',
   'CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,csrf TEXT NOT NULL,created REAL NOT NULL,last_seen REAL NOT NULL,expires REAL NOT NULL)',
   'CREATE TABLE IF NOT EXISTS records(collection TEXT NOT NULL,id TEXT NOT NULL,payload TEXT NOT NULL,visibility TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created_by TEXT NOT NULL,updated_at TEXT NOT NULL,PRIMARY KEY(collection,id))',
   'CREATE INDEX IF NOT EXISTS public_records ON records(visibility,collection)',
   'CREATE TABLE IF NOT EXISTS uploads(id TEXT PRIMARY KEY,path TEXT NOT NULL,original_name TEXT NOT NULL,mime TEXT NOT NULL,size INTEGER NOT NULL,collection TEXT NOT NULL,record_id TEXT NOT NULL,created_by TEXT NOT NULL,created_at TEXT NOT NULL)',
   'CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,actor TEXT NOT NULL,action TEXT NOT NULL,collection TEXT NOT NULL,record_id TEXT NOT NULL,before_json TEXT,after_json TEXT,created_at TEXT NOT NULL)',
   'CREATE TABLE IF NOT EXISTS trash(collection TEXT NOT NULL,id TEXT NOT NULL,deleted_at TEXT NOT NULL,deleted_by TEXT NOT NULL,state TEXT NOT NULL CHECK(state IN (\'trashed\',\'purged\')),PRIMARY KEY(collection,id))',
   'CREATE TABLE IF NOT EXISTS attempts(key TEXT NOT NULL,at REAL NOT NULL)',
   'CREATE INDEX IF NOT EXISTS attempts_time ON attempts(key,at)',
   'CREATE TABLE IF NOT EXISTS v6_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)',
   'CREATE TABLE IF NOT EXISTS v6_rights(user_id TEXT PRIMARY KEY REFERENCES users(id),edit_profile INTEGER NOT NULL DEFAULT 0,edit_research INTEGER NOT NULL DEFAULT 0)',
   'CREATE TABLE IF NOT EXISTS responses(id TEXT PRIMARY KEY,questionnaire_id TEXT NOT NULL,answers TEXT NOT NULL,created_at TEXT NOT NULL)',
  ];foreach($statements as $sql)$this->db->query($sql);@chmod($this->db->path,0600);
 }
 public function get(string $c,string $rid,bool $trash=false):?array{$r=$this->db->one('SELECT * FROM records WHERE collection=? AND id=?'.($trash?'':' AND NOT EXISTS(SELECT 1 FROM trash t WHERE t.collection=records.collection AND t.id=records.id)'),[$c,$rid]);return $r?self::record($r):null;}
 public static function record(array $r):array{$p=decode($r['payload']);$p['_version']=(int)$r['version'];$p['_updated_at']=$r['updated_at'];return $p;}
 public function list(string $c,bool $public=false):array{return array_map(self::record(...),$this->db->all('SELECT * FROM records WHERE collection=? AND NOT EXISTS(SELECT 1 FROM trash t WHERE t.collection=records.collection AND t.id=records.id)'.($public?" AND visibility='public'":'').' ORDER BY id',[$c]));}
 public function audit(string $actor,string $action,string $c,string $rid,?array $before=null,?array $after=null):void{$this->db->query('INSERT INTO audit(actor,action,collection,record_id,before_json,after_json,created_at) VALUES(?,?,?,?,?,?,?)',[$actor,$action,$c,$rid,$before?json($before):null,$after?json($after):null,utc()]);}
 public function insert(string $c,array $p,string $actor):array{$this->db->query('INSERT INTO records(collection,id,payload,visibility,version,created_by,updated_at) VALUES(?,?,?,?,1,?,?)',[$c,$p['id'],json($p),$p['visibility'],$actor,utc()]);return $this->get($c,$p['id'])??[];}
 public function replace(string $c,array $p,int $version,string $actor):array{$result=$this->db->query('UPDATE records SET payload=?,visibility=?,version=version+1,updated_at=? WHERE collection=? AND id=? AND version=?',[json($p),$p['visibility'],utc(),$c,$p['id'],$version]);ensure($result['changes']===1,409,'Someone changed this record. Reload before saving; your text has not been discarded.');return $this->get($c,$p['id'])??[];}
 public function seed():void{if($this->db->one('SELECT COUNT(*) AS n FROM records')['n'])return;$seed=decode(file_get_contents(ROOT.'/data/seed.json'));$this->db->tx(function()use($seed){foreach($seed as $c=>$rows)foreach($rows as $p)$this->insert($c,$p,'seed');});}
 public function migrate():array{
  $this->init();if($this->db->one("SELECT value FROM v6_meta WHERE key='migration'"))return ['already_upgraded'=>true];
  $backup=dirname($this->db->path).'/pre-v6-'.gmdate('Ymd-His').'-'.id().'.sqlite3';$this->db->query('VACUUM INTO ?',[$backup]);@chmod($backup,0600);
  $report=['backup'=>$backup,'media_review'=>[],'added_defaults'=>0];$schema=Schema::all();$seed=decode(file_get_contents(ROOT.'/data/seed.json'));
  $this->db->tx(function()use(&$report,$schema,$seed){
   $owners=[];$referenced=[];
   foreach(array_keys($schema) as $c)foreach($this->list($c) as $p){foreach(($p['media_items']??[]) as $mid){$referenced[$mid]=true;$rid=Records::researcherOf($c,$p);$owners[$mid][$rid?:'laboratory']=true;}}
   foreach(array_keys($schema) as $c)foreach($this->list($c) as $p){$old=$p;$version=$p['_version'];unset($p['_version'],$p['_updated_at']);foreach($schema[$c]['fields'] as $f)if(!array_key_exists($f['key'],$p)){$p[$f['key']]=Schema::default($f);$report['added_defaults']++;}
    if($c==='media'){$keys=array_keys($owners[$p['id']]??[]);if(!isset($old['scope'])){if(count($keys)===1&&$keys[0]!=='laboratory'){$p['scope']='researcher';$p['researcher_id']=$keys[0];}elseif(!$keys||$keys===['laboratory']){$p['scope']='laboratory';$p['researcher_id']='';}else{$p['scope']='review';$p['researcher_id']='';$report['media_review'][]=$p['id'];}}}
    if($c==='people'){if($p['id']==='jaydine-feris'&&in_array($p['name'],['Ms Jaydine Jeris','Ms Jaydine Feris'],true))$p['name']='Ms Jaydine Feris';if(!$p['sort_name']){$parts=preg_split('/\s+/',preg_replace('/^(Ms|Mr|Mrs|Dr|Prof)\.?\s+/','',$p['name']));$last=array_pop($parts);$p['sort_name']=$last.', '.implode(' ',$parts);}if($p['id']==='albertina-shatri'&&!isset($old['priority']))$p['priority']=1;}
    if($c==='theme'){foreach(['show_lab_logo'=>true,'show_institution_logo'=>true,'show_footer_logo'=>true,'rotate_spotlight'=>true,'preset'=>'vintage','header_band'=>'vintage','footer_band'=>'vintage','header_alignment'=>'balanced','footer_alignment'=>'balanced'] as $k=>$v)if(!isset($old[$k]))$p[$k]=$v;foreach(['leadership','questions'] as $block)if(!in_array($block,$p['home_blocks']))$p['home_blocks'][]=$block;}
    if($c==='settings'&&!isset($old['privacy_notice']))$p['privacy_notice']=$seed['settings'][0]['privacy_notice'];
    $this->replace($c,$p,$version,'migration-v6');
   }
   foreach($seed['acknowledgements'] as $p)if(!$this->get('acknowledgements',$p['id'],true))$this->insert('acknowledgements',$p,'migration-v6');
   $this->db->query("INSERT OR IGNORE INTO v6_rights(user_id,edit_profile,edit_research) SELECT id,0,1 FROM users WHERE role='researcher'");
   // V5 sessions are revoked on migration, but Argon2 password hashes are unchanged.
   $this->db->query('DELETE FROM sessions');$this->db->query("INSERT INTO v6_meta(key,value) VALUES('migration',?)",[utc()]);$this->audit('server-operator','migrate-v6','settings','laboratory');
  });return $report;
 }
}
