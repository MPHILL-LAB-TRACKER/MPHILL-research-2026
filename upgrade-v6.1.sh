#!/usr/bin/env bash
set -euo pipefail
SOURCE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
command -v php >/dev/null || { echo 'Install PHP first: sudo apt install php-cli php-sqlite3 php-gd php-mbstring' >&2; exit 1; }
php -r 'exit(version_compare(PHP_VERSION,"8.3",">=") ? 0 : 1);' || { echo 'PHP 8.3 or newer is required.' >&2; exit 1; }
exec php "$SOURCE/installer/upgrade.php" "$@"
