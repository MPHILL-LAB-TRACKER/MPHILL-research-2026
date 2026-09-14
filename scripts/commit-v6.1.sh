#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[[ "$(git rev-parse --show-toplevel)" == "$ROOT" ]] || { echo 'Use the actual MPHILL-research-2026 clone, not its parent.' >&2; exit 1; }
[[ "$(git branch --show-current)" == main ]] || { echo 'Source commits belong on main. This helper will not switch branches.' >&2; exit 1; }
LIST="$(mktemp)"
trap 'rm -f -- "$LIST"' EXIT
php -r '
$m=json_decode(file_get_contents("release-manifest.json"),true,512,JSON_THROW_ON_ERROR);
if (($m["version"]??"")!=="6.1.0" || !is_array($m["files"]??null)) exit(1);
foreach(array_keys($m["files"]) as $p){
 if (!is_string($p) || !preg_match("~^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$~D",$p)
     || str_contains($p,"..") || preg_match("~^(?:var|\\.git|\\.venv|private|backups)/~",$p)
     || (str_starts_with($p,".env") && $p!==".env.example") || !is_file($p) || is_link($p)) exit(1);
 echo $p,"\0";
}
echo "release-manifest.json\0";
' > "$LIST" || { echo 'Invalid release manifest. Nothing was staged.' >&2; exit 1; }
mapfile -d '' -t FILES < "$LIST"
(( ${#FILES[@]} > 10 )) || { echo 'Incomplete release manifest.' >&2; exit 1; }
declare -A ALLOWED=()
for path in "${FILES[@]}"; do ALLOWED["$path"]=1; done
while IFS= read -r -d '' path; do
  [[ -v 'ALLOWED[$path]' ]] || { printf 'Unrelated work is already staged: %s\nCommit or unstage that work deliberately before continuing.\n' "$path" >&2; exit 1; }
done < <(git diff --cached --name-only -z)
printf '\nCommit only %s V6.1 release paths. Database, .env, uploads and private backups are excluded.\n' "${#FILES[@]}"
printf 'Already staged release files are supported. The complete listed source files will be staged together.\n'
read -r -p 'Type COMMIT to proceed: ' CONFIRM
[[ "$CONFIRM" == COMMIT ]] || { echo 'Cancelled.'; exit 1; }
git add -- "${FILES[@]}"
if git diff --cached --quiet; then echo 'No V6.1 source changes to commit.'; exit 0; fi
git --no-pager diff --cached --stat
git -c core.pager=cat commit -m 'Upgrade TED2 to V6.1: portrait fixes, research procurement, themes and discovery review'
printf '\nSource committed locally. Next: git push origin main\nThen publish the public website through the local administration page.\n'
