#!/usr/bin/env bash
# One-time explicit provisioning. Secrets and generated configuration stay under private var/.
set -Eeuo pipefail
umask 077
SOURCE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SOURCE/.." && pwd)"
command -v node >/dev/null || { echo 'Install Node.js 20.19+ or 22.12+ before response-service setup.'; exit 1; }
command -v npx >/dev/null || { echo 'Install npm/npx before setup.'; exit 1; }
node -e 'const [a,b]=process.versions.node.split(".").map(Number);if(!(a>22||a===22&&b>=12||a===20&&b>=19))process.exit(1)' || { echo 'A current supported Node.js version is required.'; exit 1; }
command -v git >/dev/null || { echo 'Git is required to verify the installed repository.'; exit 1; }
[[ "$(git -C "$ROOT" rev-parse --show-toplevel 2>/dev/null)" == "$ROOT" ]] || { echo 'Run this from the installed V7 Git clone, not the extracted package.'; exit 1; }
WORK="$ROOT/var/community-deploy"
mkdir -p "$WORK"
printf '\nThis creates a Cloudflare Worker and D1 response database in YOUR account.\nReview Cloudflare account terms/quotas. Nothing will be public until you configure the site in admin.\n'
read -r -p 'Type DEPLOY to proceed: ' answer
[[ "$answer" == DEPLOY ]] || exit 1
read -r -p 'Unique service name (lowercase letters/digits/hyphens): ' NAME
[[ "$NAME" =~ ^[a-z][a-z0-9-]{2,40}$ ]] || { echo 'Invalid name.'; exit 1; }
cd "$WORK"
printf 'Signing in to Cloudflare (browser approval)...\n'
npx --yes wrangler@4 login
cp "$SOURCE/worker.mjs" "$SOURCE/schema.sql" "$WORK/"
DBFILE="$WORK/database.json"
# Listing is read-only and lets a repeated setup recover without creating a second database.
npx --yes wrangler@4 d1 list --json > "$WORK/databases.json"
FOUND="$(node - "$WORK/databases.json" "${NAME}-responses" <<'JS'
const fs=require('fs');const [file,name]=process.argv.slice(2);const list=JSON.parse(fs.readFileSync(file,'utf8'));
if(!Array.isArray(list))throw new Error('Unexpected database list');process.stdout.write(list.some(x=>x.name===name)?'yes':'no');
JS
)"
if [[ "$FOUND" == no ]]; then
  npx --yes wrangler@4 d1 create "${NAME}-responses"
fi
# d1 create has no --json flag; d1 info and d1 list do.
npx --yes wrangler@4 d1 info "${NAME}-responses" --json > "$DBFILE"
# Wrangler JSON output may be an object or one-element list. Refuse missing IDs.
node - "$DBFILE" "$WORK/wrangler.json" "$NAME" <<'JS'
const fs=require('fs');const [dbfile,out,name]=process.argv.slice(2);
let db;try{db=JSON.parse(fs.readFileSync(dbfile,'utf8'));}catch{console.error('Could not parse D1 info. See responses-service/README.md.');process.exit(1);}
if(Array.isArray(db))db=db[0];const id=db.uuid||db.database_id||db.id;
if(!/^[a-f0-9-]{36}$/.test(id||'')){console.error('D1 database ID missing. See setup guide.');process.exit(1);}
fs.writeFileSync(out,JSON.stringify({name,main:'worker.mjs',compatibility_date:'2025-06-01',workers_dev:true,observability:{enabled:false},d1_databases:[{binding:'DB',database_name:db.name||`${name}-responses`,database_id:id}]},null,2));
JS
cd "$WORK"
npx --yes wrangler@4 d1 execute "${NAME}-responses" --remote --file schema.sql --yes
if [[ ! -s admin-token.txt ]]; then node -e 'process.stdout.write(require("crypto").randomBytes(32).toString("hex"))' > admin-token.txt; fi
npx --yes wrangler@4 deploy
npx --yes wrangler@4 secret put ADMIN_TOKEN < admin-token.txt
printf '\nDeployment command finished. Copy the HTTPS workers.dev address printed above.\nIn local admin open Visitor inbox → Connection, enter that address, and paste the key below.\nKeep this key private. Do NOT commit var/.\n\n'
cat admin-token.txt; printf '\n\nThen save the connection, synchronize researcher choices and publish your public website once.\n'
