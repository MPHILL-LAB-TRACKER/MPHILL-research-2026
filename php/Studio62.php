<?php
declare(strict_types=1);
namespace Ted2;

final class Studio62
{
    public static function handle(Application $app,string $method,string $path,array $u,callable $body):void
    {
        if(!str_starts_with($path,'/api/visuals')&&!str_starts_with($path,'/api/pulse')&&!str_starts_with($path,'/api/cache'))return;
        Auth::admin($u);$store=$app->store;
        if($path==='/api/visuals'&&$method==='GET')$app->jsonResponse(Experience62::photos($store));
        if(preg_match('#^/api/visuals/([a-z-]+)$#D',$path,$m)){
            if($method==='GET'){$file=Experience62::photoPath($store,$m[1]);ensure($file!==null,404,'This optional photograph has not been downloaded.');Media::send($file,'image/jpeg',private:true);}
            if($method==='POST')$app->jsonResponse(Experience62::install($store,$m[1],$u));
        }
        if($path==='/api/pulse/status'&&$method==='GET')$app->jsonResponse(['configuration'=>Pulse::configuration($store->get('settings','laboratory')??[]),'state'=>(new Pulse($store))->state(),'published_items'=>count((new PublicSite($store))->data['science_news']),'review_items'=>count(array_filter($store->list('science_news'),fn($p)=>$p['visibility']==='private'))]);
        if($path==='/api/pulse/sync'&&$method==='POST'){$result=(new Pulse($store))->sync(true);$store->audit($u['username'],'refresh-science-pulse','settings','laboratory');$app->jsonResponse($result);}
        if($path==='/api/cache'&&$method==='GET')$app->jsonResponse(Cache62::stats($store));
        if($path==='/api/cache/clear'&&$method==='POST'){Cache62::clear($store);$store->audit($u['username'],'clear-public-render-cache','settings','laboratory');$app->jsonResponse(['ok'=>true,'message'=>'Public rendering cache cleared. Private research, uploads and accounts were not touched.']);}
        throw new Problem(404,'Studio operation not found.');
    }
}
