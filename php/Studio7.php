<?php
declare(strict_types=1);
namespace Ted2;

final class Studio7
{
    public static function handle(Application $app,string $method,string $path,array $u,callable $body):void
    {
        $s=$app->store;
        if($path==='/api/writing/template'&&$method==='POST'){$b=$body();ensure(Records::admin($u)||!empty($u['edit_research']),403,'Writing access is not enabled.');$app->jsonResponse(['source'=>Writing7::template((string)($b['kind']??'report'))]);}
        if(preg_match('#^/api/writing/([a-z0-9-]+)/(export|overleaf)$#D',$path,$m)){
            $p=Writing7::record($s,$u,$m[1]);
            if($m[2]==='export'&&$method==='GET'){
                $zip=Writing7::export($p);header('Content-Type: application/zip');header('Content-Disposition: attachment; filename="'.$m[1].'-latex.zip"');header('Cache-Control: no-store');header('X-Robots-Tag: noindex,nofollow');echo $zip;exit;
            }
            if($m[2]==='overleaf'&&$method==='POST'){
                $b=$body();ensure(($b['confirm_transfer']??false)===true,422,'Confirm transfer of the saved source to Overleaf first.');
                $zip=Writing7::export($p);$s->audit($u['username'],'overleaf-handoff','writing_projects',$p['id']);
                $app->jsonResponse(['action'=>'https://www.overleaf.com/docs','snip_uri'=>'data:application/zip;base64,'.base64_encode($zip),'main_document'=>'main.tex','engine'=>'pdflatex']);
            }
            throw new Problem(405,'Method not allowed.');
        }
        if(!str_starts_with($path,'/api/community-admin'))return;
        Auth::admin($u);$remote=Responses7::endpoint($s)!=='';
        if($path==='/api/community-admin/status'&&$method==='GET')$app->jsonResponse(['mode'=>$remote?'cloud':'php','endpoint'=>Responses7::endpoint($s),'token_saved'=>is_file(Responses7::tokenFile()),'enabled'=>(bool)($s->get('settings','laboratory')['community_enabled']??false)]);
        if($path==='/api/community-admin/config'&&$method==='POST')$app->jsonResponse(Responses7::configure($s,$u,$body()));
        if($path==='/api/community-admin/sync'&&$method==='POST'){Auth::owner($u);$app->jsonResponse(Responses7::sync($s));}
        if($path==='/api/community-admin/messages'&&$method==='GET'){
            if($remote)$app->jsonResponse(Responses7::remote($s,'/admin/messages'));
            $app->jsonResponse(['items'=>$s->db->all('SELECT id,researcher_id,subject,message,nickname,consent_public,reply,status,created_at,updated_at FROM community_messages ORDER BY created_at DESC LIMIT 200')]);
        }
        if(preg_match('#^/api/community-admin/messages/([a-f0-9]{32})$#D',$path,$m)){
            if($remote){ensure(in_array($method,['PUT','DELETE'],true),405,'Method not allowed.');$app->jsonResponse(Responses7::remote($s,'/admin/messages/'.$m[1],$method,$body()));}
            $r=$s->db->one('SELECT * FROM community_messages WHERE id=?',[$m[1]]);ensure($r!==null,404,'Message not found.');
            if($method==='PUT'){$v=Responses7::moderation($body(),$r);$s->db->query('UPDATE community_messages SET reply=?,status=?,updated_at=? WHERE id=?',[$v['reply'],$v['status'],utc(),$m[1]]);$s->audit($u['username'],'reply','community_messages',$m[1]);$app->jsonResponse(['ok'=>true]);}
            if($method==='DELETE'){ensure(($body()['confirm']??'')==='DELETE',422,'Confirm deletion.');$s->db->query('DELETE FROM community_messages WHERE id=?',[$m[1]]);$s->audit($u['username'],'delete','community_messages',$m[1]);$app->jsonResponse(['ok'=>true]);}
        }
        throw new Problem(404,'Community administration operation not found.');
    }
}
