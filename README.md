# TED² Research Workspace V5

**Manage content and media locally. Change the public design. Review a preview and confirm your administrator password to publish.**

This is the complete application, not a public-HTML-only update. It upgrades the existing V4 clone and database. It retains the supplied laboratory content, corrected researcher names and portraits, publications, conference notices and certificate. There are no new invented researcher achievements or research claims.

## Install in your existing workspace

Save `TED2-Research-Workspace-v5.zip` in your existing **GitHub tracker** folder (beside the actual clone). Stop the running server with **Ctrl+C**, then run as your normal `paul` account:

```bash
cd "$HOME/Documents/MPhill in biomedical sciences (medical microbiology)/GitHub tracker" &&
unzip "TED2-Research-Workspace-v5.zip" &&
bash "./TED2-Research-Workspace-v5/upgrade-v5.sh" --target "$PWD/MPHILL-research-2026"
```

Confirm the repository/database paths and type **UPGRADE**. Do not run the installer with sudo. It verifies the release checksums, makes a private backup outside the clone under `~/TED2-private-backups/`, installs pinned requirements, migrates the content conservatively, and rebuilds the root public page from your approved database content. Your `.git`, `.venv`, `.env`, accounts, uploaded files, private research and changed biographies are retained. Customized source files cause a stop instead of a silent overwrite. The installer makes no commit or push.

After a successful upgrade, commit the complete source and start the backend:

```bash
cd "$HOME/Documents/MPhill in biomedical sciences (medical microbiology)/GitHub tracker/MPHILL-research-2026" &&
bash scripts/commit-v5.sh &&
git push origin main &&
.venv/bin/python manage.py serve
```

Type **COMMIT** when requested. The helper stages only release-manifest files, not the database, `.env`, runtime uploads or backups. It refuses unrelated already-staged work. Do not substitute `git add .`.

Open `http://127.0.0.1:8000/admin`, use your existing login, and confirm **V5** is displayed. Keep the server terminal running. The public local site is `http://127.0.0.1:8000/` and the researcher workspace is `/workspace`. Use Ctrl+Shift+R once after upgrading to discard an older browser view. V5 also sends no-store headers and versioned admin asset URLs.

For video validation and conversion, install FFmpeg once:

```bash
sudo apt update && sudo apt install -y ffmpeg
```

This is the system-package command only; never run the application or upgrade script with sudo. Image/text editing works without FFmpeg. The media page reports whether video tooling is available.

## What you can control

| Administration area | V5 controls |
|---|---|
| **Website studio** | Direct shortcuts to homepage content, profiles, files, custom pages, contacts, fields, theme, Trash and publishing. |
| **Record editors** | Visible Delete, clear optional values, hide selected optional fields from the public output, add assigned contacts/fields, and upload media without leaving the record. |
| **Photos & videos** | Drag-and-drop or browse files; batch uploads, captions, alternative text, attribution, preview, private/public visibility and explicit approval. |
| **Contact information** | Add email, telephone, website, address or other contact; assign to a researcher or to the laboratory, choose homepage display, reorder, edit and delete. |
| **Custom fields** | Add labelled text, multiline text, email, URL, number or date fields to a selected researcher, project, publication, section or other supported record; edit, hide/private or delete them. |
| **Pages & sections** | Add, edit, hide, order and delete custom panels, galleries and pages; attach images, videos and PDFs; link pages in navigation. |
| **Theme & colours** | Four starting palettes; custom primary/accent/background/surface/text/muted/border colours; fonts, base text size, width, rounded corners, spacing, hero arrangement, custom logo, header/footer text, homepage block order/visibility and navigation visibility. |
| **Trash & restore** | Reversible removal, restore privately, and separate password-confirmed permanent deletion. |
| **Publish to GitHub** | Prepare a release, inspect it, enter the current administrator password and publish the exact approved public files. |

This is structured content management, not unrestricted execution of HTML, JavaScript or arbitrary server commands. Required names/titles, stable record IDs, relationships and permission controls are protected. Optional built-in public fields can be cleared or hidden; custom fields are independent deletable records. There is no UI to drop core database columns. Hiding a navigation link does not delete the underlying page or revoke access to its still-public records; make those records private or move them to Trash to remove them from the public output.

## Upload photos, videos and documents

Open a researcher, project or other content record, then use the **Photos, videos & files** shortcut. Drop files or choose **Browse**. Alternatively upload through **Photos & videos** and select them in the record's attachments. Check approved sharing only when you have permission to publish; save the parent record to attach the uploaded files. Upload success alone does not save other form changes. The library can retain private unattached items for later use.

| File type | Accepted input and processing | Per-file limit |
|---|---|---|
| Images | JPG/JPEG, PNG, WebP, GIF, BMP, TIFF. Sanitized and resized; transparency preserved. GIF uses its first frame; TIFF its first page. | 20 MiB; maximum 40 megapixels |
| Video | MP4/M4V, WebM and MOV. FFprobe validation is mandatory. Compatible files are accepted; supported MOV/other input codecs are converted to browser-friendly H.264/AAC MP4 using FFmpeg when necessary. | 80 MiB; up to 2 hours; conversion timeout 180 seconds |
| Documents | PDF, with basic signature and active-action checks. These checks are not an antivirus guarantee. | 20 MiB |

Conversion is not a guarantee for every codec or very large/long video; the application reports validation and conversion errors. Animated GIF playback is not retained: upload MP4/WebM for moving media. HTML, SVG, scripts and executable files are deliberately rejected. Images have metadata stripped on re-encoding. Already-compatible videos may retain their original encoded file and metadata; review personal/location details before sharing.

**The portrait slot accepts images; a certificate/manuscript/publication PDF slot remains PDF-specific.** Use the new adjacent **Photos, videos & files** attachment panel for mixed media instead of putting a video into a certificate field. Public PDFs and media require explicit approval. Researchers cannot give themselves administrator publishing rights.

## Add or remove researcher information

From a researcher editor select **Add contact for this researcher**. The assignment is prefilled; enter the label, kind and value, then choose Private/Public and whether it belongs on the homepage. A private researcher cannot expose their linked contact through a public contact record.

Use **Add custom field** for information beyond the built-in form, such as office hours or a specific research interest label. Select the target type and record, choose the value type, enter the value and save. Private fields stay out of public API responses, snapshots and publishing files.

Use **Clear value** to remove an optional value. Use **Hide optional fields from the website** to suppress a supported built-in field without deleting its local data. This removes it from the serialized public output, not merely its CSS. It does not provide confidentiality for data already published in old snapshots or Git history.

Public profile contacts are distinct from private email, phone, address and internal notes. Publish only information that the researcher has approved for public use.

## Delete, restore and permanently remove

**Delete** moves an ordinary record to Trash and removes it from the active local website and new public exports. Publish again to apply that deletion to the GitHub website. An earlier static site does not update merely because the local database changed.

**Restore privately** retains the record's data but returns it as Private for review. Republish deliberately after approval. Linked contacts and fields remain excluded while their parent is private or trashed.

**Delete permanently** in Trash requires your current administrator password and the word **DELETE**. Referencing records or linked accounts must be unlinked first; the dialog lists blockers. This prevents silently breaking a researcher's associated work. Permanent deletion removes the active record, owned runtime files and audit payloads for that record while preserving a minimal deletion/audit marker. IDs remain reserved so a later migration cannot recreate a deleted seed entry. It does not wipe historical backups, Git commits, published copies or browser caches. Back up and review before confirming.

Website settings and theme configuration cannot be deleted; edit/reset their fields or hide homepage blocks instead. An attachment can be detached without deleting the shared media item; delete the media record separately when it is no longer needed.

## Change the public design

Open **Theme & colours**. Choose Forest & cream, Clinical blue, Burgundy & ivory or Midnight, or enter your own palette. The sample updates as you edit; the contrast indicator warns about hard-to-read combinations but does not certify accessibility. Save, then use **View local website** to inspect the full result.

Set fonts, text size, content width, corner radius, spacing and hero image position. The homepage block checklist supports up/down ordering and visibility. An uploaded logo requires approval; leave it unapproved to retain the existing bundled logo. Header tagline and footer text are editable. The motion preference from Website settings remains available and visitor reduced-motion preferences are respected.

Section headings and laboratory details are editable in Website settings; the twelve research descriptions have their own editors. Style changes are included in the password-confirmed public release.

## Publish to the existing GitHub website

Your browser calls the local authenticated backend. The backend runs Git inside the existing clone using a separate temporary index; it does not send a terminal password from the browser. The local owner/admin password is requested for **each** push. It is not the GitHub password and is never supplied to Git.

GitHub authentication must already work on that computer under the account running the server. One-time setup, when needed:

```bash
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
```

Open **Publish to GitHub → Prepare preview → Review preview → Confirm & publish**. Enter the current local admin password. A wrong password is rejected and repeated failures are rate-limited. Changes made after preview generation require a new preview. The preview is bound to the preparing administrator and expires after 30 minutes.

Only generated public `index.html`, `.nojekyll` and approved hashed `public-media/` files are committed to **gh-pages**. Source stays on **main**. Existing working-tree changes, staged files, private uploads, `.env` and database files are not added by this publishing path. No force push is used. Git push success does not mean the GitHub Pages deployment has finished.

After the first successful publication, set GitHub **Settings → Pages → Deploy from a branch → gh-pages → / (root)** once. This updates the same public address:

```text
https://mphill-lab-tracker.github.io/MPHILL-research-2026/
```

The browser publisher does not change GitHub repository settings. The local admin is not made public by this process. Leaving the local computer off does not remove the already published static website, but no further edits reach it until the backend runs and you publish again.

The source-commit helper is only for application releases, not routine content publishing. An embedded snapshot containing many videos can be large; use the browser publisher for media-rich updates. Source-release files over 90 MiB are refused by the helper as a safety guard.

## Accounts, permissions and maintenance

Owners manage accounts, roles, access revocation and password resets. Administrators manage content, deletions, themes and public releases; account administration remains owner-only. Researchers retain their assigned private workspace and cannot edit themes, delete other records or publish.

The V5 upgrade makes a SQLite backup before content migration. Runtime data lives at the existing configured database path, normally `var/ted2.sqlite3`, with `uploads` alongside it. Never upload runtime directories, `.env` or private backups into the public Git repository. Do not expose this development server to the internet without the production HTTPS/security setup in `docs/DEPLOYMENT-AND-SECURITY.md`.

See [upgrade and recovery](docs/UPGRADE-V5.md), [V5 test report](docs/TESTING-V5.md) and the bundled test scripts. Earlier V3/V4 documentation and tests remain as historical references; this README and V5 scripts are the current installation instructions.

## Fresh installation and tests

A fresh installation can run `python3 start.py` and create its own first owner. Do not use this to replace your already installed database. Python 3.11 or newer is required; the delivered build was exercised on Python 3.13.5/Linux.

```bash
python -m pip install -r requirements-test.txt
python -m pytest -q
python tests/render_v5.py
python tests/installer_v5.py
```

The browser test requires Playwright plus Chromium and uses an explicit ASGI transport bridge. The separate `tests/browser_v5.py` attempts actual local HTTP browser navigation for unrestricted environments; that route was blocked by the delivery environment and is not claimed as verified. The installer test must run as a normal, non-root user. No test included here needs your live GitHub credentials; Git integration tests use temporary local bare repositories.

Primary platform documentation: [GitHub publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site), [GitHub CLI credential setup](https://cli.github.com/manual/gh_auth_setup-git), [FFmpeg documentation](https://ffmpeg.org/ffmpeg.html).
