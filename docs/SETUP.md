# Setup

## Existing workspace

Use the [upgrade guide](UPGRADE-RECOVERY.md), not a new database. There is no required directory name. The installer must target the actual existing repository root, not its parent or the extracted upgrade folder.

## Local prerequisites

On Ubuntu:

```bash
sudo apt update
sudo apt install -y php-cli php-sqlite3 php-gd php-mbstring ffmpeg git gh unzip
```

Check `php -v` (8.3+). Run `php bin/console.php check` inside the installed application to see runtime adapters. The optional native SQLite adapter is built with `bash bin/build-native.sh`; this requires g++, sqlite3 development headers and the documented C++ dependencies. Normal PDO SQLite installations do not need it.

For a fresh installation only, run `bash start.sh` in the application directory. Create an owner when prompted. Existing installations keep their login. There is no default production password.

The default addresses are `http://127.0.0.1:8000/`, `/admin` and `/workspace`. Keep the terminal open. This binds to the same computer, not the internet. Public hosting needs HTTPS and a proper PHP-FPM/web-server deployment; see `deploy/`.

## GitHub publishing

One-time terminal sign-in:

```bash
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
```

Use an account with access to the laboratory repository. Source is committed to `main`; generated public files are pushed from administration to `gh-pages`. Configure Pages to use `gh-pages` and `/ (root)`. Review the actual Pages status, not just the push result. Never commit `var/`, `.env`, private uploads, backups or response-service keys.

A browser login authorizes publishing for its active session. The application does not collect your GitHub password. A source push containing `.github/workflows` may require additional workflow permission in your Git authentication.

## Optional public replies

Run `bash responses-service/setup.sh` once in the installed repository after reading its guide. This uses a separate Cloudflare account and is not required for normal editing, publishing or Overleaf ZIP export. Nobody receives submissions from the internet merely by downloading the ZIP.

## Production privacy

Use HTTPS, reliable backups, named accounts and least-privilege roles. Do not upload identifiable patient data. Audit hosting logs and institutional requirements before accepting public responses. The PHP development server is not an internet production deployment.
