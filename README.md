# TED² Research Workspace

**A biomedical research website and private laboratory studio, built with PHP.**

From a first question to a published result: organize the team, plan resources, keep working notes, draft manuscripts and share approved research. Private records stay in the management application; reviewed public pages can be published to GitHub Pages.

## V7

- **Conversations:** moderated visitor messages, private reply keys and an optional always-online response gateway.
- **Writing:** researcher-owned LaTeX drafts, real project ZIP exports and an explicit Overleaf hand-off.
- **Collections:** researcher folders and named albums with approval, captions and file ordering.
- **Research desk:** structured private bench notes, methodology-linked procurement and independent milestones.
- **Fresh presentation:** four new compositions, eighteen colour presets, photographic headers/footers, light/dark/system appearance and responsive navigation.
- **Current information:** elapsed-notice removal, an activity archive, 32 original rotating science reflections, reviewed literature feeds and an open-science resource shelf.

Existing accounts, content, portraits, uploads, permissions and publishing controls are retained.

## Start

PHP 8.3+ with SQLite, fileinfo, OpenSSL and Argon2 support. GD is recommended; FFmpeg/FFprobe handles video processing. No TeX engine or Node.js is required for normal local operation.

For an existing **V6.2** installation, extract V7 separately and run `bash upgrade-v7.sh` inside the extracted folder. Enter the path to your existing Git clone when asked. After upgrading, start the installed application with `bash start.sh`.

**An online reply service must be deployed once before internet visitors can submit to a GitHub Pages website.** Local PHP responses work while the PHP server is running. Overleaf receives only a saved draft you explicitly approve for transfer; it is not two-way synchronization.

[Setup](docs/SETUP.md) · [Upgrade](docs/UPGRADE-RECOVERY.md) · [V7 guide](docs/V7-GUIDE.md) · [Visitor service](responses-service/README.md) · [Writing](docs/WRITING.md) · [Tests](docs/TESTING.md) · [Sources and rights](docs/SOURCES-AND-COVERAGE.md)
