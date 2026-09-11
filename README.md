# TED² Laboratory — Research Workspace V4

**Edit locally. Upload photographs and videos. Preview the approved website. Confirm your admin password to publish it to GitHub.**

V4 upgrades the existing Python/FastAPI application and SQLite database; it does not require another clone. The public website retains its cream-and-forest-green design, research descriptions, researcher pages, selected publications, conferences and certificate. The local owner/admin account continues to work.

## Upgrade your existing installation

Stop the server with **Ctrl+C** first. Download this release ZIP to Downloads, then run:

```bash
unzip "$HOME/Downloads/TED2-Research-Workspace-v4.zip" -d "$HOME/Downloads"
bash "$HOME/Downloads/TED2-Research-Workspace-v4/upgrade-v4.sh"
```

The installer targets your verified existing workspace:

```text
~/Documents/MPhill in biomedical sciences (medical microbiology)/GitHub tracker/MPHILL-research-2026
```

Read the displayed paths and type **UPGRADE**. Do not run the installer with sudo. It verifies the package, backs up source/configuration/database/uploads outside the repository, updates the code, and migrates V2/V3 content conservatively. It preserves `.git`, `.venv`, `.env`, accounts, private research and uploads. Your previous root `index.html` is backed up, then rebuilt from the current approved database content. Source customizations cause a stop rather than a silent overwrite. Changes made through admin are stored in the database and are preserved when different from the previous release. See [Upgrade and recovery](docs/UPGRADE-V4.md).

Start V4 in the **same clone**:

```bash
cd "$HOME/Documents/MPhill in biomedical sciences (medical microbiology)/GitHub tracker/MPHILL-research-2026"
.venv/bin/python manage.py serve
```

Open `http://127.0.0.1:8000/admin` and use your existing login. Keep that terminal running. The public local view is `http://127.0.0.1:8000/`; researcher accounts use `/workspace`.

## What is new

| Area | V4 behaviour |
|---|---|
| Website studio | Clear content shortcuts, sidebar search, grouped forms, private contact fields separated from public information, and a direct link from editing to publishing. |
| Media library | Drag-and-drop or browse local JPEG/PNG/WebP photographs, MP4/WebM videos and PDFs. Batch uploads, progress, captions, credits, image descriptions, video transcripts, preview and explicit publication approval. |
| Editable sections | Add text/media panels and galleries to four homepage positions, individual researcher profiles, or new standalone pages with navigation links. Choose layout, order and visibility. Text is escaped; this is not an arbitrary HTML/script editor. |
| Profiles | Public professional information and public contact details, separate private email/phone/address, portrait uploads, research interests and scholarly links. Existing permission boundaries remain. |
| Publishing | Compile current approved database content and media, preview the exact release, then enter the current owner/admin password for that push. No manual HTML download or terminal commit is needed in this workflow. |
| Content corrections | Ms Jaydine **Feris**; the first supplied portrait for Ms Naungwe Simasiku; the second for Prof Nailoke Pauline Kadhila. Legacy profile routes still resolve. |
| Homepage photograph | The third supplied laboratory photograph appears in the hero panel and as a faint background. Small arrival/float movement lasts under five seconds and stops; reduced-motion preferences disable it. An admin setting disables it too. |

All twelve team portraits are now locally bundled. Existing owner-uploaded/edited portraits take priority and are not silently discarded during migration. The new supplied photo choices remain selectable in the profile editor. No new publications, experimental outcomes, funders or progress percentages have been invented.

## One-time GitHub connection

On Ubuntu, install missing utilities:

```bash
sudo apt update
sudo apt install -y git gh ffmpeg unzip
```

`ffmpeg` supplies `ffprobe`, which is required to validate video uploads. Photos, text editing and publishing do not depend on video tooling.

Authenticate Git as your normal account in the server computer's terminal:

```bash
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
```

Use the GitHub account with write access to `MPHILL-LAB-TRACKER/MPHILL-research-2026`. This is **separate** from your local admin password. GitHub credentials are handled by Git/GitHub CLI, not collected by the application. No GitHub token belongs in a profile, website setting, public HTML or source file. An already-working noninteractive SSH setup is supported too.

## Publish from the browser

1. Edit and save the content. Set intended records to Public and approve their attached media.
2. Open **Publish to GitHub → Prepare preview**. Open and review the exact generated public site.
3. Click **Confirm & publish**, enter your current local owner/admin password, and confirm. Password confirmation is required for every push; stale previews must be rebuilt.
4. After the **first successful push**, open the repository's **Settings → Pages** and select **Deploy from a branch → gh-pages → / (root)**. Save once.

V4 uses your **existing clone and origin**, but writes only generated public files to a dedicated **`gh-pages`** branch. It does not switch your checked-out branch, stage your files, push `main`, create another clone or force-push. This allows local source work to remain untouched while the website is published. A branch is a stream of commits within the same repository, not another installation.

The public URL stays:

```text
https://mphill-lab-tracker.github.io/MPHILL-research-2026/
```

A successful push is not proof that GitHub Pages has finished deploying. The UI makes that distinction; check the repository's Pages/Actions deployment status. Published static files remain available while the local computer is off. Saving locally alone does not publish. See [Publishing details and troubleshooting](docs/PUBLISHING-V4.md).

## Uploads and privacy

Uploads start private unless an administrator explicitly selects approval/publication. Only approved public records/files enter releases. Private contact details, review notes, unpublished manuscript PDFs, internal funding amounts, accounts, database files and server configuration are excluded. Researchers cannot use the administrator publisher or change other researchers' private work.

| Upload | Application limit | Notes |
|---|---|---|
| Portrait | 5 MB | JPEG, PNG or WebP; re-encoded without EXIF. |
| Homepage/library image | 10 MB | Under 20 megapixels; browser/keyboard or drag-and-drop. |
| Video | 50 MB | H.264/AV1 MP4 or VP8/VP9/AV1 WebM with accepted audio tracks; `ffprobe` required. Browser codec support varies; H.264 MP4 is the straightforward choice. No transcoding is performed. |
| PDF | 20 MB | Basic structural/active-action checks, not an antivirus guarantee. |
| Complete public release | 400 MB | Application safety limit; compress or externally host long recordings. |

Images are re-encoded to strip metadata. Video/PDF metadata is not automatically anonymized. Confirm rights and consent before publication and review recordings/documents for personal or confidential information. Unpublishing removes files from the next release, **not existing downloads or Git history**. Media and text are not a place for patient-identifiable clinical data.

Public snapshot and portable ZIP export are still available. The ZIP and automated publisher keep videos as separate files rather than bloating the HTML. A single-file snapshot embeds approved local assets, including videos and approved publication PDFs, and may be large. Remote external links/images can still need an internet connection.

## Editing source locally

`web/assets/public.css` controls styling, `web/assets/public.js` public layouts/routes, and `web/public.html` the page shell. Admin files are `web/assets/admin.js` and `admin.css`. Public export compiles these local files with **current approved database content**. Do not use `manage.py build-public` to publish database edits: it generates the initial example snapshot from `data/seed.json`.

To commit the complete upgraded source from the same clone, use:

```bash
bash scripts/commit-v4.sh
git push origin main
```

The commit helper shows changes and asks for **COMMIT**. It stages only release-manifest files, refuses unrelated staged work, and never stages the database, `.env`, uploads or backups. The separate `git push` uses your existing GitHub authentication. Review the generated homepage before pushing because it contains approved public content. Browser publishing later writes the public site to `gh-pages`, not the source to `main`.

The installer leaves source modifications visible in your current branch. Browser publishing does not commit them to `main`; review and version source changes separately using explicit file paths. Never run `git add .` indiscriminately in a workspace containing private data.

For a fresh, separate installation only, `python3 start.py` creates an environment and owner account. Existing installations must use the upgrade instructions above, not initialize a replacement database. Python 3.11+ is required; this release was tested on Python 3.13.

## Validation and limitations

See [V4 testing](docs/TESTING-V4.md). Tests exercise the backend, privacy/permissions, media, migration, real Git operations against temporary local repositories, and browser UI via an explicit in-memory API bridge. Live GitHub pushing, GitHub Pages deployment, production HTTPS, and live browser/server navigation were not verified in the build environment. No credentials or live databases are included.

## Documentation

- [Upgrade/recovery](docs/UPGRADE-V4.md)
- [Publishing and authentication](docs/PUBLISHING-V4.md)
- [Testing](docs/TESTING-V4.md)
- [Source/photo audit](docs/PHOTO-AND-CONTENT-AUDIT.md)
- [V3 historical README](docs/V3-README.md)

The official GitHub instructions underpin the one-time setup: [GitHub CLI login](https://cli.github.com/manual/gh_auth_login), [Git credential helper](https://cli.github.com/manual/gh_auth_setup-git), and [GitHub Pages publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site). Their authentication/hosting requirements are separate from application-level password confirmation.
