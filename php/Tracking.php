<?php
declare(strict_types=1);
namespace Ted2;
/** Procurement tracks explicit user-entered methodology needs, not inferred protocols. */
final class Tracking {
 public static function references(Store $s,string $c,array $p):void {
  if(!in_array($c,['methods','procurement'],true))return;
  if(!empty($p['project_id'])){$project=$s->get('projects',$p['project_id']);ensure($project&&(($project['lead_id']??'')===$p['researcher_id']||in_array($p['researcher_id'],$project['people']??[],true)),422,'The project must include the assigned researcher. A project is optional.');}
  if($c==='procurement'&&!empty($p['method_id'])){$m=$s->get('methods',$p['method_id']);ensure($m&&$m['researcher_id']===$p['researcher_id'],422,'The methodology must belong to this researcher.');if($p['visibility']==='public')ensure($m['visibility']==='public',422,'Keep this procurement item private while its linked methodology is private, or unlink the methodology and review the public method-step text.');}
 }
 public static function calculate(array $p,?string $today=null):array {
  $today??=gmdate('Y-m-d');$expired=!empty($p['expiry_date'])&&$p['expiry_date']<$today;
  $required=(float)($p['required_quantity']??0);$available=(float)($p['available_quantity']??0);$ordered=(float)($p['ordered_quantity']??0);
  $usable=($p['condition']??'check-needed')==='ready'&&!$expired?$available:0.0;
  $shortage=max(0,$required-$usable);$gap=max(0,$shortage-$ordered);$warnings=[];
  if(empty($p['method_id']))$warnings[]='Method linkage needs review';
  if($expired)$warnings[]='Recorded stock is expired';
  if(($p['condition']??'')!=='ready')$warnings[]='Availability/condition must be checked';
  if($shortage>0)$warnings[]='Stock or equipment availability is short';
  if(!empty($p['due_date'])&&$p['due_date']<$today&&$shortage>0)$warnings[]='Required-by date has passed';
  return ['usable'=>$usable,'shortfall'=>$shortage,'to_source'=>$gap,'expired'=>$expired,'ready'=>$shortage===0.0,'warnings'=>$warnings];
 }
 public static function report(Store $s,array $u,?string $rid=null):array {
  $records=new Records($s);$items=[];$summary=['items'=>0,'ready'=>0,'gaps'=>0,'method_review'=>0,'overdue_milestones'=>0];
  foreach($s->list('procurement') as $p)if((!$rid||$p['researcher_id']===$rid)&&$records->canRead($u,'procurement',$p)){$calc=self::calculate($p);$items[]=['record'=>$p,'calculation'=>$calc];$summary['items']++;$summary['ready']+=(int)$calc['ready'];$summary['gaps']+=(int)($calc['shortfall']>0);$summary['method_review']+=(int)empty($p['method_id']);}
  foreach($s->list('milestones') as $p)if((!$rid||($p['researcher_id']??'')===$rid)&&$records->canRead($u,'milestones',$p)&&!empty($p['due_date'])&&$p['due_date']<gmdate('Y-m-d')&&$p['status']!=='done')$summary['overdue_milestones']++;
  return ['summary'=>$summary,'items'=>$items,'note'=>'Quantities use your entered units. Availability is not scientific validation or a procurement order.'];
 }
}
