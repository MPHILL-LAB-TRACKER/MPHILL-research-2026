<?php
declare(strict_types=1);
namespace Ted2;

/** Visitor responses are private until an administrator replies and explicit consent allows publication. */
final class Responses7
{
    public static function validEndpoint(string $url):bool
    {
        $p=parse_url($url);
        return $p!==false&&safeUrl($url,true)&&empty($p['port'])&&empty($p['query'])&&empty($p['fragment'])&&in_array($p['path']??'',['','/'],true)&&preg_match('/^[a-z0-9-]+\.[a-z0-9-]+\.workers\.dev$/iD',$p['host']??'')===1;
    }
    public static function endpoint(Store $s):string{return rtrim((string)($s->get('settings','laboratory')['community_endpoint']??''),'/');}
    public static function tokenFile():string{return Config::data().'/community-admin-token';}
    private static function origin():void
    {
        ensure(rtrim($_SERVER['HTTP_ORIGIN']??'','/')===Config::origin(),403,'Open the form on the configured website.');
    }
    public static function limit(Store $s,string $kind,int $limit=8,int $window=3600):void
    {
        $key=hash_hmac('sha256',$kind.'|'.($_SERVER['REMOTE_ADDR']??'unknown').'|'.intdiv(time(),$window),Config::secret());
        $s->db->tx(function()use($s,$key,$limit,$window){
            $s->db->query('DELETE FROM community_limits WHERE expires<?',[time()]);
            $s->db->query('INSERT INTO community_limits VALUES(?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1',[$key,time()+$window]);
            $n=$s->db->one('SELECT count FROM community_limits WHERE key=?',[$key]);
            ensure((int)$n['count']<=$limit,429,'Too many requests. Please try again later.');
        });
    }
    public static function publicRoute(Application $app,string $method,string $path,callable $body):never
    {
        $s=$app->store;$settings=$s->get('settings','laboratory')??[];
        ensure(!empty($settings['community_enabled']),403,'Visitor responses are closed.');
        if($path==='/api/community/health'&&$method==='GET')$app->jsonResponse(['ok'=>true,'service'=>'TED2 Responses','version'=>'1','moderated'=>true]);
        if($path==='/api/community/public'&&$method==='GET'){
            $rows=$s->db->all("SELECT id,researcher_id,subject,message,nickname,reply,updated_at FROM community_messages WHERE status='public' AND consent_public=1 ORDER BY updated_at DESC LIMIT 40");
            $app->jsonResponse(['items'=>$rows]);
        }
        if($path==='/api/community/challenge'&&$method==='GET'){
            self::limit($s,'challenge',60);$value=time().'.'.id();
            $app->jsonResponse(['token'=>$value.'.'.hash_hmac('sha256',$value,Config::secret()),'wait_seconds'=>2]);
        }
        ensure($method==='POST',405,'Method not allowed.');self::origin();$b=$body();
        if($path==='/api/community/submit'){
            self::limit($s,'submit');$token=$b['token']??'';
            ensure(is_string($token)&&preg_match('/^(\d{10})\.([a-f0-9]{32})\.([a-f0-9]{64})$/D',$token,$m)===1,403,'Reload the response form.');
            ensure(hash_equals(hash_hmac('sha256',$m[1].'.'.$m[2],Config::secret()),$m[3])&&time()-(int)$m[1]>=2&&time()-(int)$m[1]<=1800,403,'Wait two seconds after opening the form, or reload it.');
            ensure(empty($b['website']),422,'Submission rejected.');
            $clean=self::message($b);$rid=$clean['researcher_id'];
            if($rid!==''){$p=$s->get('people',$rid);ensure($p&&$p['visibility']==='public',422,'Choose a published researcher or General laboratory.');}
            $count=$s->db->one('SELECT COUNT(*) n FROM community_messages');ensure((int)$count['n']<5000,503,'The response inbox is full. Please contact the laboratory using its published contact details.');
            $s->db->query('DELETE FROM community_used WHERE expires<?',[time()]);
            try{$s->db->query('INSERT INTO community_used VALUES(?,?)',[hash('sha256',$token),time()+1800]);}catch(\Throwable){throw new Problem(409,'This form was already submitted. Reload before another response.');}
            $id=id();$receipt=bin2hex(random_bytes(24));$now=utc();
            $s->db->query('INSERT INTO community_messages VALUES(?,?,?,?,?,?,?,?,?,?,?)',[$id,hash('sha256',$receipt),$rid,$clean['subject'],$clean['message'],$clean['nickname'],$clean['consent_public']?1:0,'','pending',$now,$now]);
            $app->jsonResponse(['ok'=>true,'id'=>$id,'receipt'=>$receipt,'message'=>'Received privately. Save your response key to read the laboratory’s reply. It cannot be recovered if lost.'],201);
        }
        if($path==='/api/community/lookup'){
            self::limit($s,'lookup',30);$id=$b['id']??'';$receipt=$b['receipt']??'';
            ensure(is_string($id)&&is_string($receipt)&&preg_match('/^[a-f0-9]{32}$/D',$id)===1&&preg_match('/^[a-f0-9]{48}$/D',$receipt)===1,404,'Response key not found.');
            $r=$s->db->one('SELECT * FROM community_messages WHERE id=?',[$id]);
            ensure($r&&hash_equals($r['receipt_hash'],hash('sha256',$receipt)),404,'Response key not found.');
            unset($r['receipt_hash']);$app->jsonResponse(['item'=>$r]);
        }
        throw new Problem(404,'Response operation not found.');
    }
    public static function message(array $b):array
    {
        $out=[];
        foreach(['subject'=>[3,180],'message'=>[8,4000],'nickname'=>[0,80],'researcher_id'=>[0,80]] as $key=>[$min,$max]){
            $v=$b[$key]??'';ensure(is_string($v),422,'Use text in '.$key.'.');$v=trim($v);
            ensure(strlen($v)>=$min&&strlen($v)<=$max&&!preg_match('/[\x00-\x08\x0b\x0c\x0e-\x1f]/',$v),422,$key.' is missing or too long.');$out[$key]=$v;
        }
        ensure($out['researcher_id']===''||slug($out['researcher_id']),422,'Invalid researcher.');
        ensure(is_bool($b['consent_public']??false),422,'Public permission must be true or false.');
        $out['consent_public']=$b['consent_public']??false;
        return $out;
    }
    public static function moderation(array $b,array $old):array
    {
        $reply=$b['reply']??'';$status=$b['status']??'answered';
        ensure(is_string($reply)&&strlen($reply)<=8000,422,'Reply must be at most 8,000 characters.');$reply=trim($reply);
        ensure(in_array($status,['pending','answered','public','closed'],true),422,'Invalid response status.');
        if(in_array($status,['answered','public'],true))ensure(strlen($reply)>=2,422,'Write a reply before marking it answered.');
        if($status==='public')ensure((int)$old['consent_public']===1,422,'The visitor did not permit public sharing. Reply privately instead.');
        return ['reply'=>$reply,'status'=>$status];
    }
    public static function remote(Store $s,string $path,string $method='GET',?array $body=null):array
    {
        $endpoint=self::endpoint($s);ensure(self::validEndpoint($endpoint),422,'Connect your HTTPS workers.dev response service first.');
        $token=trim((string)@file_get_contents(self::tokenFile()));ensure(preg_match('/^[a-f0-9]{64}$/D',$token)===1,422,'Save the private response-service administrator key first.');
        ensure(preg_match('#^/admin(?:/(?:config|messages(?:/[a-f0-9]{32})?))?$#D',$path)===1,400,'Invalid response-service path.');
        $headers="Accept: application/json\r\nAuthorization: Bearer ".$token."\r\n";
        $opts=['method'=>$method,'header'=>$headers,'timeout'=>20,'ignore_errors'=>true,'follow_location'=>0,'max_redirects'=>0];
        if($body!==null){$opts['content']=json($body);$opts['header'].="Content-Type: application/json\r\n";}
        $context=stream_context_create(['http'=>$opts,'ssl'=>['verify_peer'=>true,'verify_peer_name'=>true]]);
        $raw=@file_get_contents($endpoint.$path,false,$context,0,1048577);
        $http=$http_response_header??[];$status=0;foreach($http as $line)if(preg_match('#^HTTP/\S+ (\d{3})#',$line,$m))$status=(int)$m[1];
        ensure(is_string($raw)&&strlen($raw)<=1048576,503,'Response service could not be reached. Check the configured endpoint, network and deployment.');
        if($status<200||$status>=300){$msg='Response service rejected the request.';try{$error=decode($raw);if(is_string($error['error']??null)&&strlen($error['error'])<250)$msg=$error['error'];}catch(\Throwable){}throw new Problem($status>=400&&$status<500?$status:503,$msg);}
        try{return decode($raw);}catch(\Throwable){throw new Problem(503,'Response service returned invalid data.');}
    }
    public static function configure(Store $s,array $u,array $b):array
    {
        Auth::owner($u);$endpoint=rtrim(trim((string)($b['endpoint']??'')),'/');
        ensure($endpoint===''||self::validEndpoint($endpoint),422,'Use your deployed HTTPS workers.dev address.');
        $token=trim((string)($b['admin_token']??''));
        if($token!==''){ensure(preg_match('/^[a-f0-9]{64}$/D',$token)===1,422,'Use the 64-character administrator key produced by the response-service setup.');atomic(self::tokenFile(),$token);}
        $p=$s->get('settings','laboratory');$v=$p['_version'];unset($p['_version'],$p['_updated_at']);$p['community_endpoint']=$endpoint;$s->replace('settings',$p,$v,$u['id']);
        $s->audit($u['username'],'community-config','settings','laboratory');
        if($endpoint!=='')self::sync($s);
        return ['ok'=>true,'endpoint'=>$endpoint,'token_saved'=>is_file(self::tokenFile()),'message'=>$endpoint?'Connection saved and public researcher options synchronized. Republish the website once to activate its endpoint.':'Local PHP response service selected. Internet visitors need publicly hosted PHP or a connected response gateway.'];
    }
    public static function sync(Store $s):array
    {
        $researchers=[];foreach($s->list('people',true) as $p)$researchers[]=['id'=>$p['id'],'name'=>$p['name']];
        $origin=parse_url(Config::site());$origin=$origin['scheme'].'://'.$origin['host'].(isset($origin['port'])?':'.$origin['port']:'');
        return self::remote($s,'/admin/config','PUT',['origin'=>$origin,'enabled'=>(bool)($s->get('settings','laboratory')['community_enabled']??false),'preview_origin'=>in_array(parse_url(Config::origin(),PHP_URL_HOST),['127.0.0.1','localhost'],true)?Config::origin():'','researchers'=>$researchers]);
    }
}
