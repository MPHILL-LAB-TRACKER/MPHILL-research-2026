<?php
declare(strict_types=1);
namespace Ted2;

/** Public presentation helpers. They receive only the already-approved projection. */
final class Research7
{
    public static function today(array $settings,?int $time=null):string
    {
        $tz=$settings['lab_timezone']??'Africa/Windhoek';
        if(!in_array($tz,\DateTimeZone::listIdentifiers(),true))$tz='Africa/Windhoek';
        return (new \DateTimeImmutable('@'.($time??time())))->setTimezone(new \DateTimeZone($tz))->format('Y-m-d');
    }
    public static function expiry(array $p):string{return ($p['expires_on']??'')?:($p['end_date']??'')?:($p['start_date']??'');}
    public static function eventStatus(array $p,array $settings,?int $time=null):string
    {
        $state=$p['lifecycle']??'automatic';if(in_array($state,['closed','cancelled'],true))return $state;
        $end=self::expiry($p);if($end!==''&&$end<self::today($settings,$time))return 'elapsed';
        return !empty($p['start_date'])&&$p['start_date']>self::today($settings,$time)?'upcoming':'open';
    }
    public static function references(Store $s,string $c,array $p,?array $old):void
    {
        if($c==='media'&&!empty($p['album_id'])){
            $album=$s->get('albums',$p['album_id']);ensure($album!==null,422,'Choose an existing album.');
            ensure(($album['scope']??'')===($p['scope']??'')&&($album['researcher_id']??'')===($p['researcher_id']??''),422,'The album and upload must have the same researcher or general-laboratory owner.');
        }
        if($c==='albums'&&$old)foreach($s->list('media') as $media)if(($media['album_id']??'')===$p['id']){
            ensure(($media['scope']??'')===$p['scope']&&($media['researcher_id']??'')===$p['researcher_id'],409,'Move or unassign this album’s uploads before changing its owner.');
        }
        if(in_array($c,['writing_projects','bench_notes'],true)){
            if(!empty($p['project_id'])){$project=$s->get('projects',$p['project_id']);ensure($project&&(($project['lead_id']??'')===$p['researcher_id']||in_array($p['researcher_id'],$project['people']??[],true)),422,'The selected project must include this researcher.');}
            if(!empty($p['method_id'])){$method=$s->get('methods',$p['method_id']);ensure($method&&$method['researcher_id']===$p['researcher_id'],422,'The methodology must belong to this researcher.');}
        }
    }
    public static function hero(PublicSite $s):string
    {
        $p=$s->settings;$t=$s->theme;$h='<section class="v7-hero layout-'.e($t['hero_layout']??'photo-right').'"><div class="v7-hero-copy"><span class="eyebrow">'.e($p['hero_eyebrow']?:'TED² · Biomedical research').'</span><h1>'.e($p['hero_title']??$p['title']).'</h1><div class="lead">'.$s->paragraph($p['hero_intro']??'').'</div><div class="actions"><a class="button" href="'.$s->url('researchers/').'">Meet the people <span aria-hidden="true">↗</span></a><a class="button secondary" href="'.$s->url('research/').'">Explore our science</a></div><dl class="v7-metrics"><div><dt>'.count($s->data['people']).'</dt><dd>Researcher & collaborator profiles</dd></div><div><dt>'.count($s->data['capabilities']).'</dt><dd>Research capabilities</dd></div><div><dt>'.count($s->data['publications']).'</dt><dd>Selected research records</dd></div></dl></div>';
        if(($t['hero_layout']??'')!=='text-only'&&!empty($p['hero_image_url']))$h.='<figure class="v7-hero-figure"><span class="v7-image-index" aria-hidden="true">IN THE LAB / TED²</span><img fetchpriority="high" decoding="async" src="'.e($p['hero_image_url']).'" alt="'.e($p['hero_image_alt']?:'Laboratory activity').'"><figcaption>'.e($p['hero_image_caption']?:'A closer look at the work, people and questions behind the research.').'</figcaption><a class="v7-image-link" href="'.$s->url('gallery/').'">Explore the gallery ↗</a></figure>';
        return $h.'</section><div class="v7-pathway"><a href="'.$s->url('research/').'"><span>01</span> Explore the research</a><a href="'.$s->url('discoveries/').'"><span>02</span> Read & discover</a><a href="'.$s->url('connect/').'"><span>03</span> Start a conversation</a></div>';
    }
    public static function spotlight(PublicSite $s):string
    {
        $items=[];foreach($s->data['announcements'] as $p)if(!empty($p['homepage'])&&in_array(self::eventStatus($p,$s->settings),['open','upcoming'],true))$items[]=['announcements',$p];
        foreach($s->data['achievements'] as $p)if(!empty($p['homepage']))$items[]=['achievements',$p];
        foreach($s->data['updates'] as $p)$items[]=['updates',$p];
        foreach($s->data['projects'] as $p)if($p['public_progress']!==null&&($p['stage']??'')!=='completed')$items[]=['projects',$p];
        if(!$items)return '';
        $h='<section class="spotlight v7-notice notice-layout-'.e($s->theme['notice_layout']??'split').'" aria-label="Laboratory notice board" data-lab-zone="'.e($s->settings['lab_timezone']??'Africa/Windhoek').'" data-carousel data-seconds="'.e($s->theme['notice_seconds']??5).'" data-effect="'.e($s->theme['notice_effect']??'fade').'" data-autoplay="'.(!empty($s->theme['rotate_spotlight'])?'yes':'no').'"><div class="spotlight-top"><span class="eyebrow">The laboratory notebook / notice board</span><div><button data-carousel-prev aria-label="Previous notice">←</button><button data-carousel-pause>Pause</button><button data-carousel-next aria-label="Next notice">→</button></div></div>';
        foreach($items as [$c,$p]){
            $expiry=$c==='announcements'?self::expiry($p):'';
            $h.='<article class="notice-slide" data-slide'.($expiry?' data-expiry="'.e($expiry).'"':'').'><span class="tag">'.e($c==='announcements'?($p['kind']??'notice'):Schema::get($c)['label']).'</span><h2><a href="'.$s->url('records/'.$c.'/'.$p['id'].'/').'">'.e($p['title']).'</a></h2><p>'.e(PublicSite::excerpt($p['description']??$p['summary']??$p['text']??'',280)).'</p>';
            if(!empty($p['start_date']))$h.='<p class="notice-date">'.e($p['start_date']).(!empty($p['end_date'])?' — '.e($p['end_date']):'').'</p>';
            if(($p['date_status']??'')==='date-conflict')$h.='<p class="notice-evidence">Date confirmation pending. '.e($p['evidence_note']??'').'</p>';
            if($c==='projects')$h.='<p>Approved public progress: '.e($p['public_progress']).'%</p>';
            $h.='</article>';
        }
        return $h.'<div class="v7-notice-footer"><p class="carousel-count" data-carousel-count></p><a href="'.$s->url('activity/').'">Activity archive →</a></div></section>';
    }
    public static function routes(PublicSite $s):array
    {
        $r=['connect/','resources/','gallery/general/'];
        foreach($s->data['people'] as $p)$r[]='gallery/researchers/'.$p['id'].'/';
        foreach($s->data['albums']??[] as $p)$r[]='gallery/albums/'.$p['id'].'/';return $r;
    }
    private static function folder(PublicSite $s,string $title,string $url,array $ids,string $description,?string $photo=null):string
    {
        if(!$photo)foreach($ids as $id){$p=$s->find('media',$id);if(($p['kind']??'')==='image'){$photo=$p['thumb_url']??$p['asset_url'];break;}}
        return '<a class="v7-folder" href="'.e($s->url($url)).'">'.($photo?'<img loading="lazy" decoding="async" src="'.e($photo).'" alt="">':'<div class="v7-folder-empty" aria-hidden="true">▰</div>').'<div><span class="eyebrow">'.count($ids).' approved item'.(count($ids)===1?'':'s').'</span><h2>'.e($title).'</h2><p>'.e($description).'</p><span class="text-link">Open collection ↗</span></div></a>';
    }
    public static function gallery(PublicSite $s,string $route):string
    {
        $media=$s->data['media'];$owner='';$scope='laboratory';$album=null;
        if($route==='gallery/'){
            $h='<section><span class="eyebrow">Behind the research</span><h1>One laboratory.<br>Many perspectives.</h1><p class="lead">Browse researcher collections, experiments in context and general laboratory moments. Only approved uploads appear here.</p><div class="v7-folder-grid">';
            $ids=array_column(array_filter($media,fn($m)=>$m['scope']==='laboratory'),'id');$h.=self::folder($s,'General laboratory','gallery/general/',$ids,'Shared photographs, recordings and documents.');
            foreach($s->data['people'] as $p){$ids=array_column(array_filter($media,fn($m)=>$m['scope']==='researcher'&&$m['researcher_id']===$p['id']),'id');$h.=self::folder($s,$p['name'],'gallery/researchers/'.$p['id'].'/',$ids,'Researcher-owned albums and files.',$p['photo_thumb']??$p['photo_url']??null);}
            return $h.'</div></section>';
        }
        if(preg_match('#^gallery/researchers/([a-z0-9-]+)/$#D',$route,$m)){$person=$s->find('people',$m[1]);ensure($person!==null,404,'Researcher collection not found.');$owner=$m[1];$scope='researcher';$title=$person['name'];}
        elseif(preg_match('#^gallery/albums/([a-z0-9-]+)/$#D',$route,$m)){$album=$s->find('albums',$m[1]);ensure($album!==null,404,'Album not found.');$owner=$album['researcher_id'];$scope=$album['scope'];$title=$album['title'];}
        else{ensure($route==='gallery/general/',404,'Collection not found.');$title='General laboratory';}
        $h='<section class="v7-gallery"><a class="text-link" href="'.$s->url('gallery/').'">← All collections</a><span class="eyebrow">Research in pictures / collection</span><h1>'.e($title).'</h1>'.($owner?'<p>'.$s->linkPerson($owner).'</p>':'');
        if($album)$h.=$s->paragraph($album['description']);
        if(!$album){$albums=array_values(array_filter($s->data['albums'],fn($a)=>$a['scope']===$scope&&$a['researcher_id']===$owner));usort($albums,fn($a,$b)=>(($a['order']??0)<=>($b['order']??0))?:strnatcasecmp($a['title'],$b['title']));if($albums){$h.='<div class="v7-folder-grid">';foreach($albums as $a){$ids=array_column(array_filter($media,fn($p)=>($p['album_id']??'')===$a['id']),'id');$h.=self::folder($s,$a['title'],'gallery/albums/'.$a['id'].'/',$ids,$a['description']);}$h.='</div><h2>Other approved uploads</h2>';}}
        $ids=array_column(array_filter($media,fn($p)=>$p['scope']===$scope&&$p['researcher_id']===$owner&&($album?($p['album_id']??'')===$album['id']:empty($p['album_id']))),'id');
        return $h.($ids?$s->mediaCards($ids):'<div class="v7-empty"><h2>A collection in the making</h2><p>No approved files in this part of the collection yet.</p></div>').'</section>';
    }
    public static function resources(PublicSite $s,bool $shelf=false):string
    {
        $items=$s->data['resources']??[];if($shelf)$items=array_values(array_filter($items,fn($p)=>!empty($p['homepage'])));
        usort($items,fn($a,$b)=>($a['order']??0)<=>($b['order']??0));if(!$items)return '';
        $h='<section class="v7-resources"><span class="eyebrow">Open science / useful connections</span><'.($shelf?'h2':'h1').'>'.e($s->settings['resources_heading']??'Your open-science toolkit').'</'.($shelf?'h2':'h1').'><p class="lead">A curated starting point for reading, writing and reproducible research. External resources are not endorsements or substitutes for local approvals.</p><div class="v7-resource-grid">';
        foreach($shelf?array_slice($items,0,3):$items as $p)$h.='<article class="v7-resource"><span class="tag">'.e($p['category']).'</span><h3><a href="'.e($p['url']).'" target="_blank" rel="noopener noreferrer">'.e($p['title']).' ↗</a></h3><p>'.e($p['description']).'</p><small>'.e($p['license_note']).'</small></article>';
        return $h.'</div>'.($shelf?'<a class="button secondary" href="'.$s->url('resources/').'">Open the full resource shelf →</a>':'').'</section>';
    }
    public static function connect(PublicSite $s):string
    {
        $settings=$s->settings;$endpoint=rtrim($settings['community_endpoint']??'','/');
        $online=!empty($settings['community_enabled'])&&(!$s->static||$endpoint!=='');
        $h='<section class="v7-connect"><span class="eyebrow">Curiosity starts a conversation</span><h1>Ask. Share. Connect.</h1><p class="lead">'.e($settings['community_intro']??'Send a question or collaboration idea to the laboratory. No account is required.').'</p><div class="v7-connect-grid">';
        if($online){
            $h.='<div class="v7-message-card" data-community data-endpoint="'.e($endpoint).'"><h2>Send the laboratory a message</h2><p class="small">Messages start private. Use a nickname or leave it blank. Do not send patient information, identifiers, confidential data or requests for medical advice.</p><form data-message><label>Topic<input name="subject" required minlength="3" maxlength="180" placeholder="What would you like to discuss?"></label><label>For<select name="researcher_id"><option value="">General laboratory</option>';
            foreach($s->data['people'] as $p)$h.='<option value="'.e($p['id']).'">'.e($p['name']).'</option>';
            $h.='</select></label><label>Your message<textarea name="message" required minlength="8" maxlength="4000" rows="6"></textarea></label><label>Nickname <span class="muted">(optional)</span><input name="nickname" maxlength="80" autocomplete="off"></label><div class="trap" aria-hidden="true"><label>Leave empty<input name="website" tabindex="-1" autocomplete="off"></label></div><label class="check"><input type="checkbox" name="consent_public"> The laboratory may publish this message, my nickname and its reply after review.</label><button class="button" type="submit">Send privately →</button><p role="status"></p></form><div data-receipt hidden></div></div>';
        }else $h.='<div class="v7-message-card"><h2>Messages are not connected yet</h2><p>The public response service has not been connected, or the administrator has paused it. Use the laboratory’s published contact details in the meantime. No message will be falsely marked as sent.</p><a class="button secondary" href="'.$s->url('researchers/').'">Find a researcher</a></div>';
        $h.='<aside class="v7-response-help"><span class="eyebrow">No account needed</span><h2>A private reply.<br>A simple response key.</h2><p>After sending, save the response key shown on screen. Return here and paste it to check the reply. The key is not sent by email and cannot be recovered if lost.</p><p>We do not attach a laboratory account to your response. Hosting providers may log connection data. Avoid information that identifies you when anonymity matters.</p>';
        if($online)$h.='<details class="v7-check-reply"><summary>Check a reply</summary><form data-response-lookup data-endpoint="'.e($endpoint).'"><label>Your response key<input name="key" autocomplete="off" required placeholder="Paste the key you saved"></label><button class="button secondary" type="submit">Check reply</button><p role="status"></p><div data-reply></div></form></details>';
        $h.='<a class="text-link" href="'.$s->url('questions/').'">Questionnaires & existing Q&A →</a></aside></div>';
        if($online)$h.='<div class="v7-public-replies" data-community-public data-endpoint="'.e($endpoint).'"><h2>Shared conversations</h2><p>Only messages with the visitor’s permission and an administrator’s approval appear here.</p><div data-public-replies class="card-grid"></div><p data-public-state class="muted"></p></div>';
        return $h.'</section>';
    }
}
