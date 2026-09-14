<?php
declare(strict_types=1);
namespace Ted2;
final class Public61 {

 /** Validate only automatically loaded resources, not ordinary evidence hyperlinks. */
 public static function validateExport(string $html,string $route):void {
  preg_match_all('/(?:src|poster)="([^"]+)"/i',$html,$matches);
  foreach($matches[1] as $raw){
   $url=html_entity_decode($raw,ENT_QUOTES|ENT_HTML5,'UTF-8');
   if(str_starts_with($url,'/')&&!str_starts_with($url,'//'))continue;
   $p=parse_url($url);$host=strtolower(trim((string)($p['host']??''),'[]'));
   $valid=safeUrl($url,true)&&!str_contains($host,':')&&!in_array($host,['localhost','localhost.localdomain'],true)&&!str_ends_with($host,'.local')&&!str_ends_with($host,'.localhost')&&str_contains($host,'.');
   if(filter_var($host,FILTER_VALIDATE_IP))$valid=$valid&&(bool)filter_var($host,FILTER_VALIDATE_IP,FILTER_FLAG_NO_PRIV_RANGE|FILTER_FLAG_NO_RES_RANGE);
   ensure($valid,422,'Public export blocked on '.$route.': a media address is insecure or local-only. Upload the file locally or use a public HTTPS media URL; do not use localhost or a private network address.');
  }
 }
 public static function facts(PublicSite $s):string {
  $items=[];foreach($s->data['lab_facts']??[] as $p)if(!empty($p['homepage'])&&(empty($p['expires_on'])||$p['expires_on']>=gmdate('Y-m-d')))$items[]=['lab_facts',$p];
  $days=max(1,(int)($s->settings['discovery_show_days']??90));$cutoff=gmdate('Y-m-d',time()-$days*86400);
  foreach($s->data['discoveries']??[] as $p)if(!empty($p['homepage'])&&($p['publication_date']??'')>=$cutoff)$items[]=['discoveries',$p];
  if(!$items)return '';usort($items,fn($a,$b)=>strcmp($b[1]['publication_date']??$b[1]['reviewed_date']??'', $a[1]['publication_date']??$a[1]['reviewed_date']??''));
  $unique=[];$seen=[];foreach($items as [$c,$p]){$key=strtolower($p['doi']??'')?:($p['source_url']??$p['id']);if(isset($seen[$key]))continue;$seen[$key]=true;$unique[]=[$c,$p];}
  $unique=array_slice($unique,0,max(1,(int)($s->theme['fact_max']??8)));
  $h='<section class="spotlight facts-board" data-carousel data-facts data-autoplay="yes" data-seconds="'.e($s->theme['fact_seconds']??12).'" data-effect="fade"><div class="spotlight-top"><div><span class="eyebrow">Source-backed science</span><h2>'.e($s->settings['fact_heading']??'Did you know?').'</h2></div><div><button data-carousel-prev aria-label="Previous research fact">←</button><button data-carousel-pause>Pause</button><button data-carousel-next aria-label="Next research fact">→</button></div></div>';
  foreach($unique as [$c,$p])$h.='<article class="notice-slide" data-slide data-fact-id="'.e($p['id']).'"><span class="tag">'.($c==='discoveries'?'Reviewed literature match':'Laboratory fact').'</span><h3>'.e($p['title']).'</h3>'.$s->paragraph($p['summary']??'').'<p><a href="'.e($p['source_url']).'" rel="noopener">'.e($p['source_label']??'Read the original research record').' ↗</a></p>'.(!empty($p['researcher_id'])?'<p>'.$s->linkPerson($p['researcher_id']).'</p>':'').'</article>';
  return $h.'<p data-carousel-count class="carousel-count"></p><p class="small muted">Selected and approved by the laboratory. A literature match is not automatically a validated discovery.</p></section>';
 }
 public static function procurement(PublicSite $s):string {
  $h='<section><span class="eyebrow">Methodology-linked preparation</span><h1>Research resources & procurement</h1><p class="lead">Only the resource requirements explicitly shared by the laboratory are listed. Private inventory, suppliers, prices and troubleshooting notes are not published.</p><div class="card-grid">';
  foreach($s->data['procurement']??[] as $p)$h.=$s->recordCard('procurement',$p);
  return $h.'</div>'.(empty($s->data['procurement'])?'<p>No procurement lists have been approved for public sharing.</p>':'').'</section>';
 }
 public static function details(PublicSite $s,string $c,array $p):string {
  if(!in_array($c,['procurement','methods'],true))return '';
  $keys=$c==='methods'?['reference','status','due_date']:['category','specification','method_step','required_quantity','available_quantity','ordered_quantity','unit','condition','due_date','status','priority'];
  $h='<dl class="details-grid">';foreach($keys as $k)if(isset($p[$k])&&$p[$k]!==''&&$p[$k]!==null)$h.='<div><dt>'.e(ucwords(str_replace('_',' ',$k))).'</dt><dd>'.nl2br(e($p[$k])).'</dd></div>';
  $h.='</dl>';if(!empty($p['method_id'])&&$s->find('methods',$p['method_id']))$h.='<p><a href="'.$s->url('records/methods/'.$p['method_id'].'/').'">Linked methodology reference →</a></p>';
  if($c==='procurement')$h.='<p class="small muted">Inventory is reported by the laboratory. Scientific suitability and readiness require the researcher’s review.</p>';
  return $h;
 }
 /** This page deliberately has no JS, fonts, images, API or stylesheet dependencies. */
 public static function light(PublicSite $s,bool $diagnostic=false):string {
  $h='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TED² · '.($diagnostic?'Connection check':'Low-data view').'</title><style>body{max-width:52rem;margin:2rem auto;padding:0 1.2rem;font:18px/1.65 system-ui,sans-serif;color:#172e24;background:#fff}a{color:#145c44}li{margin:1rem 0}h1{line-height:1.2}small{display:block}</style></head><body><a href="'.$s->url().'">Full laboratory website</a><h1>'.($diagnostic?'Connection check':'TED² Laboratory · Low-data view').'</h1>';
  if($diagnostic)return $h.'<p>This tiny page loaded from the website host. It does not require JavaScript, images, an API connection or third-party resources.</p><p>Release: <strong>'.VERSION.'</strong></p><p>If this page loads on mobile data but the main page does not, report the browser error and test the low-data page. If neither loads but Wi-Fi works, the cause may be on the network/DNS/TLS path; a theme change cannot correct it.</p><a href="'.$s->url('light/').'">Open low-data view</a></body></html>';
  $h.='<p>'.e($s->settings['hero_intro']??'').'</p><h2>Researchers</h2><ul>';
  foreach($s->data['people'] as $p)$h.='<li><a href="'.$s->url('researchers/'.$p['id'].'/').'">'.e($p['name']).'</a><small>'.e($p['role']??'').'</small></li>';
  $h.='</ul><h2>Research capabilities</h2>';foreach($s->data['capabilities'] as $p)$h.='<h3>'.e($p['title']).'</h3><p>'.e($p['text']).'</p>';
  $h.='<h2>Contact</h2><p>'.e($s->settings['contact_name']??'').'</p>';if(!empty($s->settings['contact_email']))$h.='<a href="mailto:'.e($s->settings['contact_email']).'">'.e($s->settings['contact_email']).'</a>';
  return $h.'<p><a href="'.$s->url('connection-check/').'">Connection check</a></p></body></html>';
 }
 public static function questions(PublicSite $s):string {
  $h='<section class="question-hub"><span class="eyebrow">Listen · reflect · improve</span><h1>Questions & questionnaires</h1><p class="lead">'.e($s->settings['questionnaire_intro']??'No name or email is requested.').'</p><details><summary>Privacy & how answers are used</summary>'.$s->paragraph($s->settings['privacy_notice']??'').'</details>';
  foreach($s->data['questions'] as $q)$h.='<details class="question-card"><summary>'.e($q['question']).'</summary>'.$s->paragraph($q['answer']).'</details>';
  $endpoint=$s->settings['submission_site']??'';
  if($s->static){$h.=($endpoint!==''&&safeUrl($endpoint,true))?'<a class="button" href="'.e(rtrim($endpoint,'/').'/questions/').'">Open the secure anonymous forms →</a>':'<p class="notice-evidence">Online submissions are not connected yet. A publicly hosted PHP service must be configured before internet visitors can send answers.</p>';foreach($s->data['questionnaires'] as $q)$h.='<article class="card"><h2>'.e($q['title']).'</h2>'.$s->paragraph($q['description']??'').'</article>';return $h.'</section>';}
  if(!empty($s->settings['anonymous_enabled']))$h.='<details class="question-card"><summary>Ask a new question</summary><form data-anonymous="question" class="anonymous-form"><label>What would you like to ask?<textarea name="question" rows="4" required minlength="8" maxlength="4000"></textarea></label><label class="honeypot" aria-hidden="true">Leave blank<input name="website" tabindex="-1" autocomplete="off"></label><button type="submit">Send for moderation</button><p role="status"></p></form></details>';
  $surveys=$s->data['questionnaires'];usort($surveys,fn($a,$b)=>($a['order']??0)<=>($b['order']??0));
  foreach($surveys as $q){if(empty($q['open']))continue;$qs=array_values(array_filter($s->data['survey_questions'],fn($i)=>$i['questionnaire_id']===$q['id']));if(!$qs)continue;usort($qs,fn($a,$b)=>($a['order']??0)<=>($b['order']??0));
   $h.='<details class="survey-card"><summary><strong>'.e($q['title']).'</strong><span>'.count($qs).' questions · anonymous</span></summary><form class="anonymous-form" data-anonymous="survey" data-survey="'.e($q['id']).'" data-wizard="'.(!empty($q['one_question_at_a_time'])?'yes':'no').'">'.$s->paragraph($q['description']??'').'<p data-step-count aria-live="polite"></p><progress data-step-progress max="'.count($qs).'" value="1" aria-label="Question progress"></progress>';
   foreach($qs as $i){$req=!empty($i['required_answer'])?' required':'';$name='q_'.$i['id'];$h.='<fieldset data-question-step><legend>'.e($i['label']).($req?' <small>(required)</small>':' <small>(optional)</small>').'</legend>'.$s->paragraph($i['help_text']??'');
    if(in_array($i['kind'],['single-choice','rating'],true)){$choices=$i['kind']==='rating'?['1','2','3','4','5']:$i['options'];$h.='<div class="answer-choices">';foreach($choices as $choice)$h.='<label class="answer-choice"><input type="radio" name="'.e($name).'" value="'.e($choice).'"'.$req.'> '.e($choice).'</label>';$h.='</div>';}
    elseif($i['kind']==='long-text')$h.='<textarea aria-label="Your answer" name="'.e($name).'" rows="4" maxlength="4000"'.$req.'></textarea>';
    else $h.='<input aria-label="Your answer" name="'.e($name).'" maxlength="1000"'.$req.'>';$h.='</fieldset>';
   }
   $h.='<label class="honeypot" aria-hidden="true">Leave blank<input name="website" tabindex="-1" autocomplete="off"></label><div class="actions"><button type="button" data-step-back hidden>Back</button><button type="button" data-step-next hidden>Next</button><button type="submit">Submit answers anonymously</button></div><p role="status"></p></form></details>';
  }return $h.'</section>';
 }
}
