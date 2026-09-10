# Deployment, storage and security

## What runs where

GitHub Pages is a static HTML/CSS/JavaScript host. It cannot execute this Python application or securely store the research database. Reference: https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages

The public `index.html` can remain in the existing `MPHILL-LAB-TRACKER/MPHILL-research-2026` repository. For live editing, the Python application needs a persistent server with an HTTPS address. `/admin` and `/workspace` run on that server. The connected public export contains the server’s public API address only, and fetches approved content with credentials omitted. A backend outage shows an explicit unavailable message rather than silently displaying a potentially revoked cached snapshot.

The application is a custom FastAPI/SQLite content and research manager; it is **not Joomla**, a Joomla extension, or a claim of equivalent feature coverage. Its public-site / administrative-site separation follows the requested interaction model.

## Local development

Run `python start.py`. This creates `.venv`, installs the pinned direct dependencies and prompts for the first owner account. It then binds to `127.0.0.1:8000`, not an external network interface. The `.venv` and `var` directories are generated locally and are not included in the delivery.

A prepared environment can run `python start.py --use-current-python`. Python 3.11+ is required by the launcher; this package was tested on Python 3.13 only. Clean installation on other Python/OS versions was not validated here. On distributions that split venv support from Python, install the OS-provided venv package first.

The first `init` seeds the public dataset and creates an owner. Later `init` calls preserve the existing database and accounts; they do not overwrite edited content from `seed.json`. There is no public registration, no seeded default password and no password in the compiled HTML.

## HTTPS production configuration

On the intended server, run:

```bash
python manage.py configure-production
```

Enter the real public HTTPS origin when prompted. The command writes `.env` with production mode, that origin and the existing GitHub Pages origin in the public-read allowlist. Never commit `.env`.

Then create the first owner locally if not already initialized:

```bash
python manage.py init
python manage.py serve --host 127.0.0.1 --port 8000
```

Put a properly maintained TLS reverse proxy in front of this loopback listener and run the process under your service manager. Proxy HTTPS requests to the loopback listener, preserve the public Host header, and set an upload body limit of 22 MB or less. Do not expose the plain HTTP upstream directly. The upstream checks its configured public origin for writes; it does not trust forwarded headers supplied by arbitrary clients. Request rate limiting sees the direct peer IP, so deployments behind one proxy share that per-IP login limit (40 attempts/15 minutes), in addition to the per-username limit (8 attempts/15 minutes).

FastAPI deployment guidance: https://fastapi.tiangolo.com/deployment/

In production, the application refuses an HTTP `TED2_BASE_URL`, sets Secure session cookies and HSTS, and restricts accepted Host headers. The development loopback site uses non-Secure cookies because it is HTTP. Production configuration cannot itself provision a domain, certificate or server; those must exist before a connected public page is published.

The Dockerfile is an optional deployment path. It runs as a non-root user and stores database/uploads under `/data`. Initialize the image through `python manage.py init` with a persistent `/data` volume, then run the service with the **same** volume and the actual HTTPS origin in `TED2_BASE_URL`, `TED2_PRODUCTION=1`, and the existing GitHub origin in `TED2_PUBLIC_ORIGINS`. Do not use an ephemeral container filesystem for research data. Image build and a production container deployment were not exercised in this environment.

## Roles and publishing boundaries

| Role | Scope |
|---|---|
| Owner | Content, publishing, uploads, account creation, account roles, revocation, public exports, revision logs. |
| Administrator | All content and publishing; no account-management permissions. |
| Researcher | Read assigned projects/profile; create or update assigned private manuscripts, milestones and activity updates; change own password. No public publishing or assignment changes. |

Researchers can request a biography change through a private update with type **Bio change**. They cannot overwrite an approved public profile. Already-public manuscripts and activity are locked to administrators for editing; a researcher submits a new private update when a change needs approval.

A separate explicit field schema controls the public projection. Database records are not returned wholesale. Internal notes, private submission IDs/deadlines, manuscript PDFs and funding amounts/currencies are excluded even when a record’s public status is enabled. Private relationship IDs are removed. Public project progress is an administrator-entered approved value; it is not computed from private tasks.

Publication PDFs are downloadable publicly only when the specific publication record is public and its **Allow public download** flag is set. Local portraits require a public person record, the correct linked upload ID and **Approved** photo permission. Other files remain protected. Never treat an unguessable filename or a hidden navigation button as authorization.

## Authentication and request protection

Passwords are hashed with Argon2id. Session cookies contain random opaque tokens; only their SHA-256 hashes and server-side session data are stored. Cookies are HttpOnly and SameSite=Strict. Sessions expire after eight hours, or after thirty minutes of inactivity. Login rotates the session. Sign-out, password changes and account modifications revoke sessions. CSRF tokens and strict Origin checking protect state-changing routes. Login accepts same-origin JSON requests only. Public CORS reads do not enable credentials; management endpoints do not opt into cross-origin access.

A form with expired authentication preserves its text in the open page. Sign in again in another tab, return, and save. Changes are not written to browser localStorage. Saving uses record-version checks: a stale editor gets a conflict message instead of overwriting another person’s changes.

Session guidance: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html

Password guidance: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html

## Uploads and operational limits

Portraits: JPEG/PNG/WebP, maximum 5 MB / 20 megapixels; decoded and re-encoded as JPEG, maximum 1200 × 1200, metadata removed. SVG and HTML are rejected. Documents: PDF only, up to 20 MB, signature/end-marker checks, common active-action markers rejected, delivered as attachment with a sandbox content policy. These checks are **not malware scanning or a complete PDF parser**. Add an antivirus/content-scanning process before accepting files from untrusted external users. The intended writers are named laboratory accounts, not anonymous uploaders.

Uploads live outside the web root and are served only through a permission-checking endpoint. Files are immutable on disk. Detaching/unpublishing removes public access but does not permanently erase revision history or old files. Plan retention and server-side housekeeping under the institution’s policy. No automated retention policy or antivirus service is included.

This is a single-instance SQLite implementation for a small laboratory. Do not put its SQLite file on network storage or run independent replicas against separate copies. Larger/high-concurrency deployments should migrate the storage layer to a server database before scaling. There are no email invitations, SSO, two-factor authentication, automated mail alerts or patient-record functions in this version. It is not an institutional data-compliance certification. Do not store patient identifiers or regulated clinical datasets here without institutional assessment and additional controls.

## Backup and recovery

Create a private backup from the server command line, choosing a fresh path outside the public repository:

```bash
python manage.py backup ../ted2-private-backup.zip
```

The backup contains a consistent SQLite snapshot and all referenced immutable uploads. It contains **password hashes, active session records, private research and documents**. Store it encrypted with restricted access, off-server where appropriate; this command does not encrypt it. Test restoration before relying on a backup schedule.

To restore: stop the application; unpack `ted2.sqlite3` and the `uploads` directory into the configured private data directory (normally `var`); remove any stale `ted2.sqlite3-wal` / `ted2.sqlite3-shm` files after shutdown; restrict directory/file permissions; start the application. Before admitting users, revoke restored sessions:

```bash
python -c "import sqlite3; from manage import environment, store; environment(); db=store(); c=sqlite3.connect(db.path); c.execute('DELETE FROM sessions'); c.commit(); c.close()"
```

The operator must know the owner username to reset its password:

```bash
python manage.py reset-password owner
```

Here `owner` is an example username, not a pre-created account. Replace it with the actual account name. Password entry is interactive and does not appear in shell arguments or command history. Resetting a password does not reactivate a disabled account.

## Before real deployment

Review dependency advisories and update through a tested environment; the delivered versions are the direct versions exercised here, not a promise of indefinite security. Configure HTTPS and service supervision, persistent storage, off-site encrypted backups, access ownership and photograph permissions. Run the HTTP tests and the live-origin browser test on the actual staging deployment. Verify HTTPS cookies, reverse proxy limits, public CORS reads from the GitHub Pages origin, private-file denial, restores and account recovery. No production server, TLS certificate, domain, remote image delivery or live GitHub deployment was tested or created for this delivery.
