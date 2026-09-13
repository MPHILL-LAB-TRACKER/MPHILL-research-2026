<?php
declare(strict_types=1);
namespace Ted2;
final class Auth {
 const COOKIE='ted2_v6_session';
 public function __construct(public Store $store){}
 public static function hash(string $password):string{ensure(strlen($password)>=12&&strlen($password)<=1024,422,'Use a password of 12–1024 characters.');return password_hash($password,PASSWORD_ARGON2ID,['memory_cost'=>65536,'time_cost'=>3,'threads'=>4]);}
 public function limit(string $key,int $n,int $window):void{$this->store->db->tx(function()use($key,$n,$window){$this->store->db->query('DELETE FROM attempts WHERE at<?',[time()-86400]);$count=$this->store->db->one('SELECT COUNT(*) n FROM attempts WHERE key=? AND at>?',[$key,time()-$window]);ensure($count['n']<$n,429,'Too many attempts. Please wait before trying again.');$this->store->db->query('INSERT INTO attempts VALUES(?,?)',[$key,microtime(true)]);});}
 public function current(bool $required=true):?array{
  $token=$_COOKIE[self::COOKIE]??'';$r=null;
  if(is_string($token)&&preg_match('/^[a-f0-9]{64}$/D',$token))$r=$this->store->db->one('SELECT u.id,u.username,u.role,u.researcher_id,u.active,s.csrf,s.created,s.expires,s.last_seen,COALESCE(r.edit_profile,0) edit_profile,COALESCE(r.edit_research,0) edit_research FROM sessions s JOIN users u ON u.id=s.user_id LEFT JOIN v6_rights r ON r.user_id=u.id WHERE token_hash=?',[hash('sha256',$token)]);
  if(!$r||!$r['active']||$r['expires']<time()||$r['last_seen']<time()-1800){if($required)throw new Problem(401,'Sign in again. Your session may have expired.');return null;}
  $this->store->db->query('UPDATE sessions SET last_seen=? WHERE token_hash=?',[microtime(true),hash('sha256',$token)]);return $r;
 }
 public static function origin():void{ensure(($_SERVER['HTTP_ORIGIN']??'')===Config::origin(),403,'This change must originate from the management site.');ensure(($_SERVER['HTTP_SEC_FETCH_SITE']??'same-origin')!=='cross-site',403,'Cross-site management requests are blocked.');}
 public function write():array{self::origin();$u=$this->current();ensure(hash_equals($u['csrf'],$_SERVER['HTTP_X_CSRF_TOKEN']??''),403,'Security token missing. Reload the page.');return $u;}
 public function login(array $body):array{
  self::origin();$name=$body['username']??'';$password=$body['password']??'';ensure(is_string($name)&&is_string($password)&&strlen($name)<=60&&strlen($password)<=1024,422,'Invalid credentials format.');
  $ip=hash_hmac('sha256',(string)($_SERVER['REMOTE_ADDR']??''),Config::secret());$this->limit('login-ip:'.$ip,30,900);$this->limit('login-name:'.hash('sha256',strtolower($name)),8,900);
  $user=$this->store->db->one('SELECT * FROM users WHERE username=?',[strtolower(trim($name))]);$dummy='$argon2id$v=19$m=65536,t=3,p=4$AAAAAAAAAAAAAAAAAAAAAA$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA';$ok=password_verify($password,$user['password_hash']??$dummy);ensure($user&&$user['active']&&$ok,401,'Username or password is incorrect.');
  $token=bin2hex(random_bytes(32));$csrf=bin2hex(random_bytes(32));$now=microtime(true);
  $this->store->db->tx(function()use($token,$csrf,$now,$user){$old=$_COOKIE[self::COOKIE]??'';if($old)$this->store->db->query('DELETE FROM sessions WHERE token_hash=?',[hash('sha256',$old)]);$this->store->db->query('DELETE FROM sessions WHERE expires<?',[$now]);$this->store->db->query('INSERT INTO sessions VALUES(?,?,?,?,?,?)',[hash('sha256',$token),$user['id'],$csrf,$now,$now,$now+8*3600]);$this->store->audit($user['username'],'login','users',$user['id']);});
  setcookie(self::COOKIE,$token,['expires'=>0,'path'=>'/','secure'=>Config::production(),'httponly'=>true,'samesite'=>'Strict']);$_COOKIE[self::COOKIE]=$token;return $this->current();
 }
 public function logout():void{$this->write();$this->store->db->query('DELETE FROM sessions WHERE token_hash=?',[hash('sha256',$_COOKIE[self::COOKIE]??'')]);setcookie(self::COOKIE,'',['expires'=>1,'path'=>'/','secure'=>Config::production(),'httponly'=>true,'samesite'=>'Strict']);}
 public function password(array $u,string $p):void{$this->limit('confirm:'.$u['id'],8,900);$row=$this->store->db->one('SELECT password_hash FROM users WHERE id=?',[$u['id']]);ensure(strlen($p)<=1024&&password_verify($p,$row['password_hash']),403,'Password confirmation failed.');}
 public static function admin(array $u):void{ensure(Records::admin($u),403,'Administrator permission required.');}
 public static function owner(array $u):void{ensure($u['role']==='owner',403,'Only an owner manages accounts.');}
}
