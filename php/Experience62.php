<?php
declare(strict_types=1);
namespace Ted2;

/** Photographic bands use attributed local assets, never arbitrary remote URL execution. */
final class Experience62
{
    public static function registry(): array { return decode(file_get_contents(ROOT.'/data/photography.json')); }
    public static function photoPath(Store $store, string $key): ?string
    {
        $record=self::registry()[$key]??null;if(!$record)return null;
        foreach ([ROOT.'/data/photography/'.$record['file'], dirname($store->db->path).'/licensed-photography/'.$record['file']] as $path) {
            if (is_file($path) && !is_link($path)) return $path;
        }
        return null;
    }
    public static function photos(Store $store): array
    {
        $out=[];foreach(self::registry() as $key=>$p){unset($p['sha1'],$p['download']);$p['id']=$key;$p['installed']=self::photoPath($store,$key)!==null;$p['preview_url']=$p['installed']?'/api/visuals/'.$key:'';$out[]=$p;}return $out;
    }
    public static function install(Store $store,string $key,array $u): array
    {
        Auth::admin($u);$p=self::registry()[$key]??null;
        ensure($p && !empty($p['download']) && !empty($p['sha1']),422,'Choose a source-verified downloadable photograph.');
        $ctx=stream_context_create(['http'=>['timeout'=>25,'follow_location'=>0,'header'=>"User-Agent: TED2ResearchWorkspace/6.2 (+open-license-image-import)\r\n"], 'ssl'=>['verify_peer'=>true,'verify_peer_name'=>true]]);
        $bytes=@file_get_contents($p['download'],false,$ctx,0,10*1024*1024+1);
        ensure(is_string($bytes)&&strlen($bytes)<=10*1024*1024,503,'Image source unavailable. Existing photographs were not changed.');
        ensure(hash_equals($p['sha1'],sha1($bytes)),409,'Source image changed. Recheck the source/rights before importing a new version.');
        $info=@getimagesizefromstring($bytes);ensure($info&&($info['mime']??'')==='image/jpeg'&&$info[0]*$info[1]<=40000000,422,'Source image is invalid.');
        $dir=dirname($store->db->path).'/licensed-photography';dirPrivate($dir);$temp=$dir.'/download-'.id().'.jpg';
        try {atomic($temp,$bytes);$display=Media::thumbnailFile($temp,1400,$dir.'/resized');atomic($dir.'/'.$p['file'],file_get_contents($display));}
        finally {if(is_file($temp))unlink($temp);}
        Cache62::clear($store);
        $store->audit($u['username'],'import-licensed-photo','theme',$key,null,['source'=>$p['source'],'license'=>$p['license']]);
        return ['ok'=>true,'message'=>'Licensed photograph imported locally. Select it in Appearance and publish to update the public website.'];
    }
    public static function art(PublicSite $site,string $location): string
    {
        $t=$site->theme;if(empty($site->raw['theme']['website']['photo_art_approved']))return '';
        $key=$t[$location.'_art']??'none';if($key==='none')return '';
        $source='';$credit='';$title='';
        if($key==='custom'){$source=$site->upload($site->raw['theme']['website'][$location.'_art_upload']??'');$credit=$t[$location.'_art_credit']??'';$title='Custom photographic decoration';}
        elseif($path=self::photoPath($site->store,$key)){$p=self::registry()[$key];$name='public-media/'.hash_file('sha256',$path).'.jpg';$site->assets[$name]=$path;$source=$site->url($name);$credit=$p['credit'];$title=$p['title'];}
        if(!$source)return '';
        $height=in_array($t['photo_art_height']??'', ['small','medium','large'],true)?$t['photo_art_height']:'medium';
        $tint=in_array($t['photo_art_tint']??'', ['natural','theme-wash','monochrome'],true)?$t['photo_art_tint']:'natural';
        return '<figure class="photo-band photo-band-'.$location.' size-'.$height.' treatment-'.$tint.(!empty($t['photo_art_depth'])?' with-depth':'').'"><img '.($location==='footer'?'loading="lazy"':'fetchpriority="low"').' decoding="async" src="'.e($source).'" alt="" width="1400" height="350"><figcaption><a href="'.$site->url('sources/#photography').'">'.e($title).' · Image credit</a></figcaption></figure>';
    }
    public static function credits(Store $store): string
    {
        $h='<section id="photography"><span class="eyebrow">Real photographs · explicit rights</span><h2>Photographic design credits</h2><p>Decorative images are illustrative; they do not imply a laboratory result or endorsement. The laboratory-supplied photograph is not an open-licensed stock image.</p><div class="card-grid">';
        foreach(self::registry() as $key=>$p)if(self::photoPath($store,$key)){$h.='<article class="card"><h3>'.e($p['title']).'</h3><p>'.e($p['credit']).'</p><p>'.e($p['license']).'</p><p class="small">'.e($p['changes']).'</p>';if($p['source'])$h.='<a href="'.e($p['source']).'">Original source ↗</a> ';if($p['license_url'])$h.='<a href="'.e($p['license_url']).'">Rights statement ↗</a>';$h.='</article>';}
        return $h.'</div></section>';
    }
    public static function palette(array $t): string
    {
        $defaults=['primary'=>'#a8dcc5','accent'=>'#e6bd81','background'=>'#101c20','surface'=>'#192a2e','text_color'=>'#eff5f2','muted_color'=>'#b5c9c4','border_color'=>'#355057'];
        $css=':root[data-appearance="dark"]{color-scheme:dark;';
        foreach($defaults as $k=>$d){$v=$t['dark_'.$k]??$d;if(!preg_match('/^#[a-f0-9]{6}$/iD',$v))$v=$d;$css.='--'.str_replace('_','-',$k).':'.$v.'!important;';}
        return $css.'}:root[data-appearance="light"]{color-scheme:light}';
    }
    public static function appearance(array $t): string
    {
        $mode=in_array($t['appearance']??'', ['system','light','dark'],true)?$t['appearance']:'system';
        $data=['mode'=>$mode,'allow'=>(bool)($t['appearance_switch']??true)];
        $config=json_encode($data,JSON_HEX_TAG|JSON_HEX_AMP|JSON_HEX_APOS|JSON_HEX_QUOT);
        return '<script>window.TED2_APPEARANCE='.$config.';try{var a=window.TED2_APPEARANCE,m=a.mode;if(a.allow)m=localStorage.getItem("ted2-appearance-v62:"+location.host)||m;if(!["light","dark","system"].includes(m))m=a.mode;document.documentElement.dataset.appearance=m==="system"?(matchMedia("(prefers-color-scheme:dark)").matches?"dark":"light"):m}catch(e){document.documentElement.dataset.appearance="light"}</script>';
    }
    public static function switcher(array $theme): string
    {
        if(empty($theme['appearance_switch']))return '';
        return '<label class="appearance-control"><span class="sr-only">Colour mode</span><select data-appearance-control aria-label="Colour mode"><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option></select></label>';
    }
    public static function quotePanel(PublicSite $site): string
    {
        if(empty($site->theme['show_quotes']))return '';
        $rows=array_values(array_filter($site->data['science_quotes']??[],fn($p)=>!empty($p['homepage'])));if(!$rows)return '';
        $h='<section class="quote-panel" data-carousel data-quotes data-random="'.(!empty($site->theme['quotes_random'])?'yes':'no').'" data-autoplay="yes" data-seconds="'.e($site->theme['quote_seconds']??18).'" data-effect="fade"><div class="spotlight-top"><div><span class="eyebrow">Ideas worth keeping</span><h2>'.e($site->settings['quotes_heading']??'A moment of scientific perspective').'</h2></div><div><button data-carousel-prev aria-label="Previous quotation">←</button><button data-carousel-pause>Pause</button><button data-carousel-next aria-label="Next quotation">→</button></div></div>';
        foreach($rows as $q){$h.='<article data-slide data-quote-id="'.e($q['id']).'"><blockquote><p>“'.e($q['quote']).'”</p><footer>'.e($q['author']).'</footer></blockquote><p class="small muted">'.e($q['source_label']).'</p>';if($q['source_url'])$h.='<a href="'.e($q['source_url']).'">Check attribution ↗</a>'; $h.=self::tags($q['tags']??[]).'</article>';}
        return $h.'<p data-carousel-count class="carousel-count"></p></section>';
    }
    public static function tags(array $tags): string
    {
        $h='<div class="topic-tags">';foreach(array_slice($tags,0,8) as $tag){$tag=trim(preg_replace('/[^\pL\pN_-]+/u','',(string)$tag),'#');if($tag)$h.='<span>#'.e($tag).'</span>';}return $h.'</div>';
    }
    public static function pulsePanel(PublicSite $site): string
    {
        if(empty($site->theme['show_pulse']))return '';
        $config=Pulse::configuration($site->settings);$rows=$site->data['science_news']??[];
        if(!$config['enabled']&&!$rows)return '';
        $h='<section class="research-pulse pulse-'.e($site->theme['pulse_layout']??'editorial').'" data-pulse data-policy="'.e(Pulse::digest($config)).'" data-delivery="'.e($config['delivery']).'" data-auto="'.($config['enabled']&&$config['policy']==='source-headlines'?'yes':'no').'" data-limit="'.e($site->theme['pulse_max']??6).'"><div class="section-heading"><span class="eyebrow">#ResearchInFocus · an open-science reading desk</span><h2>'.e($site->settings['pulse_heading']??'Research in focus').'</h2><p class="muted">Source-linked research records and innovation perspectives. Headlines are not laboratory achievements or validated clinical advice.</p></div><label class="pulse-filter">Explore a topic <select data-pulse-filter><option value="">All topics</option></select></label><div class="pulse-grid" data-pulse-list>';
        usort($rows,fn($a,$b)=>strcmp($b['published_date']??'',$a['published_date']??''));
        foreach(array_slice($rows,0,(int)($site->theme['pulse_max']??6)) as $p){$h.='<article class="pulse-card" data-pulse-tags="'.e(implode(' ', $p['tags']??[])).'"><span class="tag">'.e($p['source_kind']??'research').'</span><time>'.e($p['published_date']??'').'</time><h3><a href="'.e($p['source_url']).'" rel="noopener">'.e($p['title']).'</a></h3>'.$site->paragraph($p['summary']??'').'<p class="small muted">'.e($p['source_label']??'').(!empty($p['authors'])?' · '.e($p['authors']):'').'</p><p class="small">'.(!empty($p['automatic'])?'Automatic source headline — not reviewed by the laboratory':'Administrator-reviewed item').'</p>'.self::tags($p['tags']??[]).'</article>';}
        if(!$rows)$h.='<p data-pulse-empty>No headlines have been published yet. Enabled sources will appear after a successful refresh; no results are invented when a source is unavailable.</p>';
        return $h.'</div><p class="small muted" data-pulse-status>Published reading selection. Updates depend on the configured source checks.</p></section>';
    }
}
