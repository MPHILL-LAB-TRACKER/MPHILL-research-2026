<?php
declare(strict_types=1);
namespace Ted2;

/** Only rendered public projections and their asset references enter this cache. */
final class Cache62
{
    public static function assetVersion(string $name):string {return substr(hash_file('sha256',ROOT.'/public/assets/'.$name),0,16);}
    public static function path(Store $store):string{return dirname($store->db->path).'/public-render-cache';}
    public static function stats(Store $store):array{$files=glob(self::path($store).'/*.json')?:[];return ['entries'=>count($files),'bytes'=>array_sum(array_map('filesize',$files)),'private_pages_cached'=>false];}
    public static function clear(Store $store):void {foreach(glob(self::path($store).'/*.json')?:[] as $p)if(!is_link($p))unlink($p);}
    public static function render(PublicSite $site,string $route):array
    {
        $seconds=max(0,min(600,(int)($site->theme['render_cache_seconds']??120)));
        if($route==='questions/'||$seconds===0)return ['html'=>$site->render($route),'hit'=>false];
        $code=[];foreach(array_merge(glob(ROOT.'/php/*.php'),glob(ROOT.'/public/assets/*')) as $p)if(is_file($p))$code[]=hash_file('sha256',$p);
        // Include reviewed public projection, published file approvals and time-sensitive sections.
        $key=hash('sha256',json([$site->data,$site->raw,$route,$site->prefix,Config::site(),gmdate('Y-m-d'),$code]));
        $directory=self::path($site->store);dirPrivate($directory);$file=$directory.'/'.$key.'.json';
        if(is_file($file)&&!is_link($file)&&filemtime($file)>time()-$seconds){$p=decode(file_get_contents($file));return ['html'=>$p['html'],'hit'=>true];}
        $html=$site->render($route);atomic($file,json(['html'=>$html]));
        $files=glob($directory.'/*.json')?:[];usort($files,fn($a,$b)=>filemtime($b)<=>filemtime($a));foreach(array_slice($files,100) as $old)if(!is_link($old))unlink($old);
        return ['html'=>$html,'hit'=>false];
    }
    public static function worker(PublicSite $site):string
    {
        $prefix=$site->prefix.'/';$namespace='ted2-public-'.substr(hash('sha256',Config::site()),0,12).'-';
        $generation=substr(hash('sha256',json([$site->data,VERSION,self::assetVersion('site.css'),self::assetVersion('site.js'),self::assetVersion('experience.js')])),0,20);
        $config=json(['prefix'=>$prefix,'namespace'=>$namespace,'cache'=>$namespace.$generation,'enabled'=>(bool)($site->theme['public_asset_cache']??true),'limit'=>max(10,min(100,(int)($site->theme['public_cache_entries']??60)))]);
        return "const C=".$config.";\n".file_get_contents(ROOT.'/public/assets/sw-template.js');
    }
}
