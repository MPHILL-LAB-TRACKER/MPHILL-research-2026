# Browser publishing from the existing clone

The local backend performs Git operations for authenticated administrators. Browser JavaScript does not directly execute arbitrary terminal commands. It calls narrowly scoped endpoints protected by the existing session, same-origin and CSRF controls.

## Initial connection

Use GitHub credentials with write permission to `MPHILL-LAB-TRACKER/MPHILL-research-2026`. Existing working noninteractive Git credentials can be reused. Otherwise, in the same computer/account that runs the backend:

```bash
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
```

GitHub authentication and the **local administrator password** serve different purposes. The application never asks for your GitHub account password. An SSH origin is supported when the key/agent and verified host key already work without interactive prompts.

The source clone must have a Git commit identity (`git var GIT_AUTHOR_IDENT`) and exactly one origin push destination matching the intended GitHub repository. Set your real identity through Git configuration if it is missing; do not invent one or store authentication tokens in source files.

## Each publication

Save edits, choose Public for intended records and explicitly approve attached media. Open **Publish to GitHub → Prepare preview**, review the exact files, select **Confirm & publish**, then enter your current owner/admin password. Incorrect passwords do not push. The preview is bound to the preparing account, expires after 30 minutes, and is refused when approved public data or design code changes. Each push requires a new preview and password confirmation.

The publisher uses the current clone's Git object database with a separate temporary index. It does not change HEAD, the checked-out source files or normal staging area. Only the compiled public `index.html`, `.nojekyll` and approved, content-addressed `public-media/` files are committed to **gh-pages**. Existing branch history becomes the new commit's parent. No force-push is used. No second clone is created.

After the first successful browser push, set GitHub **Settings → Pages → Deploy from a branch → gh-pages → / (root)**. The website address remains `https://mphill-lab-tracker.github.io/MPHILL-research-2026/`. A successful Git push is not a successful deployment report: GitHub Pages may still be building. Source commits on `main` and browser-generated public commits on `gh-pages` are deliberately separate.

## Media and privacy

Approved uploads travel with the public release. Portraits and other images are re-encoded without EXIF; videos and PDFs are not anonymized. Use `sudo apt install ffmpeg` on Ubuntu to provide `ffprobe` for supported MP4/WebM validation. No transcoding is performed; a container/codec can validate without being supported in every browser.

The runtime library holds private media until explicit approval/public visibility. Private contacts, accounts, research notes, unpublished manuscript attachments, internal funding values and the SQLite database are excluded from public projection. Links between records are filtered against public visibility. Public PDFs and videos must be reviewed for confidential information and redistribution rights.

Removal affects a future published tree, not copies people downloaded or previous Git history. Never upload patient-identifiable data for public publication. PDF checks are basic structural checks, not antivirus scanning.

## Troubleshooting

**Repository not ready:** launch `manage.py serve` from the actual installed clone, not the parent workspace or extracted ZIP.

**Git operation failed:** check your connection, `gh auth status`, `git remote -v`, `git var GIT_AUTHOR_IDENT` and repository write/branch permissions in the terminal. Password re-confirmation is not a substitute for GitHub authorization. Git command errors returned by the application are deliberately sanitized to avoid exposing credentials.

**Content changed:** prepare and review a new preview; the old one cannot be used to publish a different release.

**Video refused:** install `ffprobe`, use a supported MP4/WebM codec and keep the file at or below 50 MB. The application also limits the complete release to 400 MB.

**Website unchanged:** verify that the push succeeded, Pages uses `gh-pages` and its deployment completed. Saving a local form alone does not update GitHub. Existing browser caches may require a refresh.

## Optional exports

The administration screen offers a portable public ZIP and a single HTML snapshot. Both use current approved database content. Single HTML embeds approved local assets and can become large for video. ZIP/browser publishing stores assets as separate files. Remote source image URLs, external links and citations can still require the internet.

The seed-only command `manage.py build-public` is for constructing the initial release snapshot. To export existing admin edits at the terminal, use `manage.py export-public --output index.html` instead.

Official setup references: [GitHub CLI authentication](https://cli.github.com/manual/gh_auth_login), [Git credential helper](https://cli.github.com/manual/gh_auth_setup-git), [Pages publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).
