#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[[ "$(git rev-parse --show-toplevel)" == "$ROOT" ]] || { echo 'Run inside the actual clone.' >&2; exit 1; }
[[ "$(git branch --show-current)" == main ]] || { echo 'Keep release source on main; resolve your current branch deliberately first.' >&2; exit 1; }
git diff --cached --quiet || { echo 'Unrelated work is already staged. Commit or unstage it yourself before using this helper.' >&2; exit 1; }
LIST="$(mktemp)"
trap 'rm -f -- "$LIST"' EXIT
php -r '
$m=json_decode(file_get_contents("release-manifest.json"),true,512,JSON_THROW_ON_ERROR);
if (($m["version"]??"")!=="6.0.0" || !is_array($m["files"]??null)) exit(1);
foreach(array_keys($m["files"]) as $p){
 if (!is_string($p) || !preg_match("~^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$~D",$p)
     || str_contains($p,"..") || preg_match("~^(?:var|\\.git|\\.venv|private|backups)/~",$p)
     || (str_starts_with($p,".env") && $p!==".env.example") || !is_file($p) || is_link($p)) exit(1);
 echo $p,"\0";
}
echo "release-manifest.json\0";
' > "$LIST" || { echo 'Invalid or unsafe release manifest. Nothing was staged.' >&2; exit 1; }
mapfile -d '' -t FILES < "$LIST"
(( ${#FILES[@]} > 10 )) || { echo 'Invalid release manifest.' >&2; exit 1; }
printf 'Stage and commit only %s V6 release paths. No database, uploads, .env or backups will be included.\n' "${#FILES[@]}"
read -r -p 'Type COMMIT to proceed: ' CONFIRM
[[ "$CONFIRM" == COMMIT ]] || { echo 'Cancelled.'; exit 1; }
git add -- "${FILES[@]}"
if git diff --cached --quiet; then echo 'No release changes to commit.'; exit 0; fi
git diff --cached --stat
git commit -m 'Upgrade TED2 to V6: PHP research studio, scoped media and verified publishing'
printf '\nSource committed locally. Review, then run: git push origin main\n'
