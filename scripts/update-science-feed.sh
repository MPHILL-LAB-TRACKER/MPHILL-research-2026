#!/usr/bin/env bash
set -euo pipefail
# Runs in an ephemeral Actions checkout, not a user's local workspace.
[[ "${GITHUB_ACTIONS:-}" == true ]] || { echo 'Run the local PHP feed worker for local updates.' >&2; exit 1; }
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
git fetch --no-tags origin gh-pages
WORK="$(mktemp -d)"
trap 'rm -rf -- "$WORK"' EXIT
git show FETCH_HEAD:science-config.json > "$WORK/config.json" || { echo 'Publish V6.2 once before enabling this workflow.'; exit 0; }
PARENT="$(git ls-remote --heads origin refs/heads/science-feed | cut -f1)"
if [[ -n "$PARENT" ]]; then
    git fetch --no-tags origin "$PARENT"
    git show "$PARENT:feed.json" > "$WORK/previous.json"
fi
php scripts/science-pulse.php --config "$WORK/config.json" --previous "$WORK/previous.json" --output "$WORK/feed.json"
[[ -f "$WORK/feed.json" ]] || exit 0
# Publish metadata alone using an isolated index; no source/private files can be staged here.
export GIT_INDEX_FILE="$WORK/index"
git read-tree --empty
BLOB="$(git hash-object -w "$WORK/feed.json")"
printf '100644 %s\tfeed.json\n' "$BLOB" | git update-index --index-info
TREE="$(git write-tree)"
git config user.name 'TED2 Research Pulse'
git config user.email 'research-pulse@users.noreply.github.com'
ARGS=(commit-tree "$TREE" -m 'Refresh source-linked research headlines')
[[ -z "$PARENT" ]] || ARGS+=(-p "$PARENT")
COMMIT="$(git "${ARGS[@]}")"
git push origin "$COMMIT:refs/heads/science-feed"
