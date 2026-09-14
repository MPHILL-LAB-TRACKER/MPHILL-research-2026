# Setup

## Requirements

Use PHP 8.3 or newer with PDO SQLite, Fileinfo, OpenSSL and Argon2 password support. PHP-GD is recommended for images. FFmpeg/FFprobe is required for videos and also provides an image-processing fallback. Git is required for publishing; GitHub CLI is used for Pages status and configuration.

On Ubuntu, install the missing dependencies through your system package manager:

```bash
sudo apt install php-cli php-sqlite3 php-gd php-mbstring ffmpeg git gh unzip
```

This package does not require Composer or a JavaScript build service. No font files or third-party browser libraries are included. Optional native utilities are built with `bash bin/build-native.sh`; normal PDO SQLite installations do not need them.

## Choose a directory

Extract or clone the application into any directory you control. Run `bash start.sh` from that application directory, not a parent directory. On first run choose an owner username and password. On later runs existing accounts and data remain intact.

The public local page is at `http://127.0.0.1:8000/`, administration at `/admin` and researcher access at `/workspace`. Leave the terminal running. Ctrl+C stops the server and local source-check worker.

Private runtime data lives in `var/` unless `TED2_DB` specifies another path. Keep `.env`, databases, uploads, session data and backups out of public Git. The included ignore rules protect normal runtime paths but cannot undo files previously committed elsewhere.

## Publishing identity

In your terminal, as the same operating-system user running PHP:

```bash
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
```

The public website publisher is configured for this laboratory's repository. Repository selection is deliberately not a free-form URL field in administration. Fork deployments must review `php/Publisher.php`, the reading-feed URL in `public/assets/experience.js`, `TED2_PUBLIC_URL` and the installer repository check together.

Adding the optional scheduled workflow may require permission to modify Actions workflows. For a GitHub CLI OAuth login that reports a missing `workflow` scope, use `gh auth refresh -h github.com -s workflow`. Fine-grained tokens or organisation policies may instead require repository administrator changes. Never put a token into the public code or paste it into a support conversation.

## Public PHP hosting

The local PHP development server is not a production web server. Review `deploy/` for PHP-FPM/Nginx and HTTPS guidance before hosting admin or anonymous submissions publicly. Separate public exports from private application storage. GitHub Pages does not execute PHP.
