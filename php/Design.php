<?php
declare(strict_types=1);
namespace Ted2;
/** Author-created, self-contained vector ornaments. Never executes uploaded SVG. */
final class Design {
 public static function presets():array{return decode(file_get_contents(ROOT.'/data/design-presets.json'));}
 public static function motifs():array {return [
  'test-tubes'=>'<path d="M15 8h20m-17 0v43a7 7 0 0 0 14 0V8M18 34h14M48 8h20m-17 0v43a7 7 0 0 0 14 0V8M51 42h14M80 8h20m-17 0v43a7 7 0 0 0 14 0V8M83 29h14M10 48h98v16H10z"/><circle cx="26" cy="26" r="2"/><circle cx="58" cy="31" r="2"/><circle cx="89" cy="19" r="2"/>',
  'glassware'=>'<path d="M27 7h18m-14 0v25L14 58q-3 7 5 7h34q8 0 5-7L41 32V7M23 46h25M73 11h28m-25 0v48q0 6 6 6h12q6 0 6-6V11M78 40h20m-5-20h6m-6 9h6m-6 20h6"/>',
  'microscopes'=>'<path d="M32 9l13-6 18 29-13 7zM60 26c34 8 34 36 7 37M30 45h43m-23 0v14M30 67h64M46 59v8M33 9l-7 5m27 25-8 5"/><circle cx="76" cy="43" r="6"/>',
  'pipettes'=>'<path d="M18 9l13-4 14 44-13 4zM22 8l-2-6m18 49 7 14M66 8l12 3-11 37-12-3zM73 9l2-7M61 47l-6 13M83 39h21m-18 0v23q0 6 7 6t7-6V39"/><circle cx="49" cy="68" r="2"/>',
  'dna'=>'<path d="M20 4c90 15-70 48 20 64M88 4c-90 15 70 48-20 64M33 8h42M43 16h22M46 26h16M39 36h29M28 46h53M27 56h53M36 64h35"/>',
  'molecules'=>'<path d="M24 18l30 17 35-19M54 35v25m0-25 37 20M24 18 12 44"/><circle cx="24" cy="18" r="8"/><circle cx="54" cy="35" r="9"/><circle cx="89" cy="16" r="7"/><circle cx="91" cy="55" r="8"/><circle cx="54" cy="61" r="6"/><circle cx="12" cy="44" r="5"/>',
  'cells'=>'<ellipse cx="31" cy="35" rx="23" ry="29"/><circle cx="31" cy="34" r="9"/><ellipse cx="84" cy="33" rx="22" ry="19"/><circle cx="84" cy="33" r="7"/><path d="M14 23l6 3m19 27 5-4m52-9 3 4"/>',
  'lab-grid'=>'<path d="M0 16h120M0 36h120M0 56h120M20 0v72M40 0v72M60 0v72M80 0v72M100 0v72M3 70h114"/>',
  'leaves'=>'<path d="M12 64C31 45 56 27 103 8M32 48C7 45 14 16 46 34c3 2-6 12-14 14zM54 32c-6-27 17-36 19-13M55 32c32-3 40 20 7 20M78 18c25-19 41-6 21 8"/>',
  'fern'=>'<path d="M59 67V8M59 53Q24 49 18 35q29 0 41 18M59 43Q28 36 26 23q25 3 33 20M59 32Q34 23 39 12q17 5 20 20M59 54q36-7 43-21-30 1-43 21M59 43q29-9 32-22-22 4-32 22M59 30q19-12 17-20-13 5-17 20"/>',
  'botanical'=>'<path d="M28 66V23m0 26Q1 40 13 23q15 7 15 26m0-15q20-6 21-21-20-1-21 21M84 66V26"/><circle cx="84" cy="19" r="6"/><path d="M84 13c-19-21-22 10-6 8-19 9 1 23 6 4 8 20 24 0 6-4 20 0 9-28-6-8M84 50q20-20 25-5-4 13-25 5"/>',
  'mountains'=>'<path d="M0 64 32 14l24 33L77 9l43 55H0M22 30l10 7 9-8M67 27l11 6 7-9M0 69h120"/>',
  'dunes'=>'<path d="M0 59Q36 19 72 42t48 9M0 66q65-42 120-5M36 62q22-26 31-25M0 71h120"/><circle cx="97" cy="19" r="9"/>',
  'landscape'=>'<path d="M0 62 25 36l21 20 20-38 33 38 21-13M0 69q29-17 54 0t66-4M9 44V20m-9 19 9-19 10 19z"/><circle cx="99" cy="16" r="8"/>',
  'waves'=>'<path d="M0 24q15-16 30 0t30 0t30 0t30 0M0 40q15-16 30 0t30 0t30 0t30 0M0 56q15-16 30 0t30 0t30 0t30 0"/>',
  'savannah'=>'<path d="M0 67h120M59 65V28M59 40l-19-9m19 6 18-10M16 26q5-18 25-11 19-20 32-5 28-7 33 16Z"/><circle cx="104" cy="49" r="7"/>',
  'geometric'=>'<path d="M10 36 30 9l21 27-21 27ZM67 10h40v52H67ZM0 69h120"/><circle cx="87" cy="36" r="12"/>',
  'vintage'=>'<path d="M0 36h120M0 30h36m48 0h36M0 42h36m48 0h36M45 36l15-15 15 15-15 15zM13 25q-6-15 6-15 13 0 6 15M96 47q-8 15 5 15 12 0 6-15"/>',
  'modern'=>'<path d="M0 25h38l12 11h70M0 47h71l12-11M15 60h90"/><circle cx="44" cy="25" r="4"/><circle cx="76" cy="47" r="4"/>'
 ];}
 public static function band(array $theme,string $location):string {
  $name=$theme[$location.'_motif']??'none';$art=self::motifs()[$name]??'';if($art==='')return '';
  $strength=in_array($theme['motif_strength']??'', ['subtle','balanced','bold'],true)?$theme['motif_strength']:'balanced';
  $size=in_array($theme['motif_size']??'', ['small','medium','large'],true)?$theme['motif_size']:'medium';
  $cells='';for($i=0;$i<12;$i++)$cells.='<g transform="translate('.($i*120).' 0)">'.$art.'</g>';
  return '<div aria-hidden="true" class="ornament ornament-'.$location.' strength-'.$strength.' size-'.$size.'"><svg viewBox="0 0 1440 72" preserveAspectRatio="xMidYMid slice" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'.$cells.'</svg></div>';
 }
}
