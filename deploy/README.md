# Hosting modes and production boundaries

**Local-first / GitHub Pages:** `bash start.sh` runs PHP on loopback. Only this computer can reach administration. Browser publishing generates crawlable static public pages and approved media on `gh-pages`. That website continues to work while the computer is off. Anonymous submissions and remote researcher logins cannot be received by a laptop that is offline or by GitHub Pages.

**Hosted PHP:** use a PHP 8.3+ hosting account or an HTTPS reverse proxy with Nginx and PHP-FPM. Set the document root to `public/`, never the repository root. Keep database and uploads outside the web root. Set `TED2_BASE_URL` to the exact external HTTPS origin and `TED2_PRODUCTION=1`. Retain `TED2_PUBLIC_URL` as the canonical public site address. The host must forward the original Host header. `nginx.conf` is an explicitly labelled Ubuntu 24.04 deployment example, not an automatically installed service. Adapt the FPM socket to the PHP version installed on that host.

If keeping the GitHub public site, set **Website settings → Public submission site** to the hosted application's HTTPS base URL. Published Questions pages will link to its live forms. Do not enter localhost there. The hosted server must remain available for incoming questions and researcher logins. There is no anonymous endpoint secret embedded in the public export.

The bundled PHP built-in server is for local development. It is not a production hosting strategy or a high-traffic benchmark. Nginx/PHP-FPM configuration, TLS, backups, file permissions, malware scanning, capacity and monitoring require deployment-specific validation. Long media conversion jobs currently run in the upload request (bounded to 300 seconds); for a large multi-user installation use a dedicated worker queue rather than increasing concurrent conversions without limits.

## Git credentials on a hosted server

Publishing uses the OS service account's Git/SSH/GitHub CLI credentials, not the web login password. Keep those credentials outside the web root and restrict them to the intended repository. Existing terminal credentials work for a local CLI server running as `paul`; they do not automatically transfer to a different FPM service account. Never copy a broad personal token into JavaScript or the database.

## Literature notifications

Enable a researcher's literature watch and specify their query in their profile. New results enter a private review queue. A manual button is available in Literature watch. For periodic checks, use your service account's scheduler to execute the complete command below once daily after deploying to `/srv/ted2`:

```bash
cd /srv/ted2 && php bin/console.php literature-sync
```

This command is bounded, opt-in, metadata-only and uses Europe PMC. It is **not** an always-running job installed automatically. In-app review items are not emails or browser push notifications. A failed network request records an error, never a invented discovery. Published claims require the researcher to read and assess the underlying source.

## Anonymous response privacy

No name, email, login ID, raw IP address or browser fingerprint is stored in response records. Short-lived hashed rate-limit identifiers are used to prevent abuse. Free text can itself reveal identity. Hosting providers, reverse proxies and GitHub can retain IP logs; the application cannot promise network anonymity. Avoid collecting patient information, personal clinical records or confidential unpublished results in these forms. Manage consent/retention through the editable privacy notice and delete responses when no longer needed.
