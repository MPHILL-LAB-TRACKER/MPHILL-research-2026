#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
command -v php >/dev/null || { echo 'Install PHP: sudo apt install php-cli php-sqlite3 php-gd php-mbstring' >&2; exit 1; }
php -r 'exit(version_compare(PHP_VERSION,"8.3",">=") ? 0 : 1);' || { echo 'PHP 8.3 or newer is required.' >&2; exit 1; }
php bin/console.php init
printf '\nLocal website: http://127.0.0.1:8000/\nAdmin: http://127.0.0.1:8000/admin\nResearcher workspace: http://127.0.0.1:8000/workspace\nKeep this terminal open. Ctrl+C stops the local server.\n\n'
exec php -d upload_max_filesize=80M -d post_max_size=84M -d memory_limit=512M -d max_execution_time=300 -S 127.0.0.1:8000 -t public public/router.php
