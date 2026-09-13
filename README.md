# TED² Research Workspace V6

**PHP management and rendering · optional C++ utilities · researcher-owned media · a public website that remains on GitHub Pages.**

V6 replaces the running Python application with a PHP 8.3+ application. It preserves the existing SQLite database, Argon2 passwords, researchers, publications, uploaded files and private research. It adds server-rendered profile URLs, a reorganised studio, ownership-aware uploads, anonymous forms and session-authorised publishing.

**PHP does not replace the HTML/CSS a browser displays.** The PHP application generates those pages. GitHub Pages serves the generated public files; it does not run PHP or C++. This split keeps the existing public address and lets it remain available when the local management computer is off. Native code is optional, not a claim of automatically better mobile compatibility or unlimited traffic capacity.

## Upgrade the existing V5 installation

Download the complete `TED2-Research-Workspace-v6.zip` into the same `GitHub tracker` folder as the previous packages. Stop the running V5 server with **Ctrl+C**.

Install the PHP runtime and image/database extensions once on Ubuntu:

```bash
sudo apt update &&
sudo apt install -y php-cli php-sqlite3 php-gd php-mbstring ffmpeg git gh unzip
```

PHP **8.3 or newer** is required. FFmpeg is already installed on the user's current machine; reinstalling an already-installed package is not necessary. On systems where PHP is installed without the Argon2 password algorithm, use a PHP build with Argon2 support before migrating accounts.

Run the upgrade in the existing workspace:

```bash
cd "$HOME/Documents/MPhill in biomedical sciences (medical microbiology)/GitHub tracker" &&
unzip "TED2-Research-Workspace-v6.zip" &&
bash "./TED2-Research-Workspace-v6/upgrade-v6.sh" \
  --target "$PWD/MPHILL-research-2026"
```

Review the paths and type **UPGRADE**. Do **not** run the installer with sudo. It validates the release files, verifies the actual Git clone, checks for source conflicts, creates a private source/configuration/database/upload backup, overlays the PHP release, and migrates the original database. It does not switch branches, commit unrelated files, change passwords or push to GitHub.

Private backups are placed under `~/TED2-private-backups/v6-.../`. The migration log lists media that need an ownership review. Known legacy media attached to exactly one researcher are assigned to that researcher. Conflicting attachments become **Ownership needs review** and are withheld from public output until resolved. Existing owner-edited content is retained.

Then commit the release source and start the PHP application:

```bash
cd "$HOME/Documents/MPhill in biomedical sciences (medical microbiology)/GitHub tracker/MPHILL-research-2026" &&
bash scripts/commit-v6.sh &&
git push origin main &&
bash start.sh
```

Type **COMMIT** when prompted. The helper stages release paths only. It stops when unrelated changes are already staged. Never use `git add .` to publish an installed workspace with private local data.

Open:

```text
http://127.0.0.1:8000/admin       Owner / administrator
http://127.0.0.1:8000/workspace   Researcher account
http://127.0.0.1:8000/            Public local preview
```

Use the existing username and password. V5 sessions are revoked during migration, so sign in again. Leave the terminal running. **Use `bash start.sh` for V6—not `.venv/bin/python manage.py serve`.** Old Python source and its virtual environment are left in the clone for controlled rollback; they are not used by the V6 runtime.

For a fresh installation only, extract the release and run `bash start.sh`. The launcher imports the supplied public seed and prompts for the first owner account. There is no default owner password.

## Your main workflow

**Edit / upload → save → view the local website → Publish & deployment → Prepare preview → review → confirm & push → check deployment.**

Login authorises publishing for that session. There is no second password field on every push. Sessions expire after 30 minutes of inactivity or eight hours total; an expired session requires sign-in again. Account password changes and account-permission changes revoke sessions. Destructive permanent deletion still requires explicit password confirmation.

The publisher uses the **same clone**, an isolated Git index and the existing terminal Git credentials. It writes only approved public pages and media to `gh-pages`, without switching `main` or including staged source changes. It does not copy the database, `.env`, raw backups, unpublished records or private responses into that branch.

Authenticate GitHub CLI once, using a GitHub account that can write to this repository:

```bash
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
```

GitHub credentials are separate from the local admin login. SSH authentication already configured in Git can also be used. The application does not collect a GitHub password or embed a personal token into the public site.

### Deployment verification

The publishing screen checks the Pages source and distinguishes **commit pushed**, **deployment pending/not started**, **deployment failed** and **deployment success**. With owner permission and a suitable GitHub CLI login, **Configure Pages** sets `gh-pages / (root)` after explicit confirmation. The branch must exist first. The repository's default branch remains `main`.

When API permissions or GitHub CLI are unavailable, status is labelled **unverified**, not successful. A successful Git push alone is never presented as proof that Pages changed. Use **Check status** after the push or open the GitHub deployment run. Deployment completion is not synchronous with the push.

The public site address remains:

```text
https://mphill-lab-tracker.github.io/MPHILL-research-2026/
```

## What administrators can control

| Studio area | Controls |
|---|---|
| Researchers & collaborators | Names, affiliations, biographies, research areas, scholarly links, public/private contacts, portraits, alphabetic sorting and priority. |
| Milestones & progress | Responsible researcher, status, optional target date, weight and summary. **A project is optional.** |
| Achievements | Researcher, date, recognition, evidence note, certificate and homepage visibility. No project prerequisite. |
| Photos, videos & files | Batch drag/drop or browse, owner assignment, visible title, caption, alt text, credit, transcript, public filename, ordering, approval, removal and restoration. |
| Pages & sections | New text/media panels, profile sections, galleries and standalone pages; order, placement, navigation label and public/private state. |
| Theme, logos & layout | Vintage, modern, clinical and night presets; custom palette, typography, spacing, width, corners, homepage order, hero position, optional header/footer decorations and logo controls. |
| Contact information / custom fields | Researcher-specific or laboratory contacts; labelled fields attached to supported records; optional field clearing/hiding. |
| Anonymous Q&A | Moderate incoming questions; write answers, reject, delete or approve for publication. |
| Questionnaires | Publish an anonymous questionnaire with separately ordered text, long-text, single-choice or rating questions; review/delete private responses. |
| Literature watch | Opt-in source-linked paper metadata, private by default, with researcher review and approval. |
| Leadership & acknowledgements | Editable PI, administrator and supervisor acknowledgements, selected researcher, text, priority and homepage visibility. |
| Accounts & permissions | Owner-created accounts, linked researcher, profile/research editing rights, password resets and access revocation. |
| Trash & restore / activity log | Restore accidental deletion, permanently remove with confirmation, and inspect management actions. |

Essential identifiers, owner-account safeguards and security boundaries remain protected. Custom fields can be removed; optional built-in fields can be cleared/hidden. V6 is a structured laboratory CMS, not an arbitrary PHP/JavaScript execution interface.

## Media ownership and presentation

Every library item is either **General laboratory**, owned by **one named researcher**, or awaiting an ownership review. Selecting a researcher record offers only that researcher's media. General files do not silently appear on each researcher's profile. Researcher-owned items do not enter the general laboratory gallery.

Within a record, drag the selected media cards to reorder them; **up/down buttons** provide a touch/keyboard alternative. Save the parent record to keep its attachment order. The media library also supports drag/up/down ordering for its filtered gallery. The visible title, caption and download filename are independent fields. A file is stored under an opaque server filename for safety; renaming the public download does not rename arbitrary filesystem paths.

Image formats: **JPEG/JPG, PNG, WebP, GIF, BMP, TIFF**. Images are decoded and re-encoded to JPEG/PNG, resized to a maximum 2,000-pixel edge. Animated GIF/TIFF inputs become a still frame. Portrait orientation and crop should be reviewed in the preview.

Video formats: **MP4, WebM and MOV**. FFprobe validates the stream; FFmpeg normalises it to MP4/H.264/AAC with fast-start metadata and a maximum 1920×1080 frame. The public player uses controls, `playsinline` and no preloading of the whole video. This improves compatibility but is not a guarantee for every codec/device combination.

PDF is supported for documents and certificates. Dedicated certificate/manuscript slots remain PDF-only; the adjoining media editor accepts photographs and videos. Input limits are **20 MiB per image/PDF** and **80 MiB per video**; processed videos must also remain under 80 MiB and under one hour. A public release is limited to 400 MiB of media. SVG/HTML/scripts and arbitrary executable uploads are rejected. This validation is not a malware scanner for PDF contents.

Public visibility and approval are separate. Researcher-supplied replacement portrait/library binaries lose their prior approval until an administrator reviews them. Downloaded copies and earlier Git commits cannot be revoked by changing local visibility.

## Theme and layout

The same colour and font tokens drive **both** interfaces. Presets are starting points; all palette controls remain editable. Header/footer laboratory decoration has independent `none`, `vintage` and `modern` settings plus alignment options; the decoration does not fill the page body. Main laboratory logo, institutional logo, footer logo and favicon each have an upload and explicit approval control.

Themes use system font families, not remotely loaded font files. Vintage uses restrained serif headings; modern uses clean system sans-serif; clinical uses a humanist heading stack; night uses a darker palette. Public pages keep spacious blocks rather than compressing all descriptions into one long line. The notice board rotates every **15 seconds**, pauses on hover/focus and when the tab is hidden, and provides previous/next/pause controls. Reduced-motion preferences disable automatic rotation and arrival animation by default.

## Accounts and researcher isolation

Owners manage accounts. Administrators edit all content and publish; researcher accounts cannot publish, alter themes, read private responses or manage other accounts.

Each researcher account is linked to **one** researcher record. The owner separately grants **edit own profile/media/contacts** and **edit assigned research**. Existing V5 researcher accounts preserve research editing but do not automatically receive the new profile-editing privilege; grant it under Accounts & permissions. Cross-profile reads/writes/uploads and incompatible media links are rejected by the PHP backend, even when an API request is crafted manually.

An assigned researcher may edit the professional text of their already-public profile. Those edits enter the next administrator-reviewed public release. New records start private, and researchers cannot independently approve public visibility or media. Private phone, address and email fields are excluded from public pages and export.

## Anonymous forms need a reachable server

The anonymous module is implemented locally and for PHP hosting. It does not send names, emails or account IDs with responses. Incoming questions are private until moderated; questionnaire responses stay private. Only administrators can read or remove them. Set a clear purpose and privacy notice before collecting responses.

**GitHub Pages cannot receive or store these submissions.** To accept responses from internet visitors, host the PHP application behind HTTPS, then enter that HTTPS address under **Website settings → Public submission site**. The published Questions page links to the live forms. Until configured, it explicitly says submissions are not connected—there is no non-working submit button disguised as an active service.

Do not publish the local `127.0.0.1` URL as an online form address. A laptop-only installation can receive submissions only from its own local session. Internet researcher logins likewise require hosted PHP. Hosting providers may record access logs, and identifying details may be typed into free text; no claim of absolute network anonymity is made.

## Discoverability and scholarly integrity

Every researcher has a real route such as `/researchers/paulus-hamutenya/`, with server-rendered content, a unique title, canonical URL, ProfilePage/Person structured data and a sitemap. Legacy hash links are redirected by a small compatibility script. The page's substantive content and directory links are present without JavaScript. JavaScript progressively adds filtering, navigation and the notice board.

After publishing, verify the website in Google Search Console. The verification-token field is under Website settings; submit the generated `sitemap.xml`. Search engines decide whether and when to index/rank a page. Typing a name into a search engine cannot be forced to redirect users to this site, and a new language does not guarantee rankings.

The original twelve research descriptions, twelve people, eight publication records, conference notices and certificate evidence are retained. Prior name corrections are retained. The PI and site-admin acknowledgements are provided; the co-supervisor acknowledgement is a private editable record for confirmation before public display. No new grant, achievement, experiment, confirmed conference date or publication has been invented.

## Literature watch: factual metadata, not automatic scientific advice

Enable literature watch on an individual profile and enter a Europe PMC search query. **Check opted-in topics** fetches up to 50 recent metadata matches per enabled researcher from the preceding 90 days. The response includes source title, author string, journal/year and source/DOI links, not generated claims about a breakthrough. Duplicate records are avoided. New matches are private and unapproved. Failed requests report failure.

The command can also be scheduled on an always-on host:

```bash
php bin/console.php literature-sync
```

No recurring job, email service or browser push subscription is installed automatically. Results are an **in-app review queue**, not a guaranteed exhaustive surveillance service. See `deploy/README.md` for hosting/scheduling boundaries.

## Optional C++ utilities

Normal operation uses PHP PDO SQLite. The package also contains a real C++17 utility with a private prepared-statement SQLite protocol and metadata keyword-ranking mode. It has no web listener and accepts no shell commands. It is optional; adding it is not claimed to make a browser faster.

To compile on Ubuntu:

```bash
sudo apt install -y build-essential libsqlite3-dev libjson-c-dev
bash bin/build-native.sh
```

The binary is created privately in `var/native/`. To test the native SQLite adapter explicitly, set `TED2_SQLITE_DRIVER=native` in your private `.env`. It is also a fallback where PHP's SQLite driver is unavailable. No architecture-specific executable or font files are distributed in this release.

## Maintenance and tests

Runtime: PHP 8.3+, Argon2id support, Fileinfo, PDO SQLite; GD recommended; FFmpeg/FFprobe for video. The delivered code was exercised under PHP 8.4.23 with the C++ SQLite adapter and FFmpeg fallback image processing. The PDO/GD branches need deployment-specific verification; they were unavailable in the build environment.

```bash
bash bin/build-native.sh
php tests/test_core.php
python3 tests/test_http.py
```

Python is used only by the test drivers, not by the V6 application. The tests use temporary data and local Git remotes; they do not log in to or push the live repository. `tests/test_browser.py` adds an optional Chromium/Playwright interface check and documents its in-memory transport. See `docs/TESTING.md` for exact evidence and limitations.

The original-V5 installer integration test is also supplied as `tests/test_installer.py`; it requires an extracted V5 fixture and that fixture’s Python dependencies.

Useful commands:

```bash
php bin/console.php check
php bin/console.php migrate
php bin/console.php build "$HOME/TED2-public-preview-$(date +%Y%m%d-%H%M%S)"
```

A command-line build uses the current approved database, not the original seed. Back up the database and uploads together; do not publish runtime files. For external hosting, read `deploy/README.md`. Do not expose the PHP built-in development server directly to the internet.

## Reference documentation

- GitHub Pages hosting model: https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages
- GitHub Pages publishing source: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
- GitHub CLI authentication: https://cli.github.com/manual/gh_auth_setup-git
- PHP built-in server warning: https://www.php.net/manual/en/features.commandline.webserver.php
- Google crawlable/server-rendered pages: https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics
- Accessible carousel behaviour: https://www.w3.org/WAI/tutorials/carousels/animations/
- Europe PMC developer services: https://europepmc.org/developers
