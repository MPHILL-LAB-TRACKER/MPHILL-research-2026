# Upgrade V2/V3 to V4 in the existing clone

This is a source-and-content upgrade, not a new account/database installation. Stop the local server first. Run commands as the account that owns your existing workspace, without sudo.

```bash
unzip "$HOME/Downloads/TED2-Research-Workspace-v4.zip" -d "$HOME/Downloads"
bash "$HOME/Downloads/TED2-Research-Workspace-v4/upgrade-v4.sh"
```

The default target is the confirmed **MPHILL-research-2026** subfolder, not the empty parent Git repository. For another existing installation, pass `--target "/absolute/path/to/the/clone"`. Read the detected paths and type `UPGRADE`.

## What the installer does

It checks Python 3.11+, the existing virtual environment, actual Git root, an existing database and the release SHA-256 manifest. It refuses a listening server, unsafe/symlink destination, or locally customized source that cannot safely be replaced. The release hashes detect accidental changes; they are not a signed publisher identity.

It creates a mode-0700 private backup under `~/TED2-private-backups/`, containing the affected previous source, `.env`, a consistent SQLite copy and uploads. It installs the pinned Python dependencies into the existing `.venv` (internet required), copies the V4 source, previews and applies the content migration, then rebuilds the root `index.html` from approved public database content. That replaces the previous compiled HTML, which is retained in the backup.

`.git`, branch/commit history, staged work, `.venv`, `.env`, accounts and uploaded files are not replaced. The migration preserves owner-edited database fields that differ from both release baselines. Review `preserved_owner_fields` in its report. Existing custom photos can remain active; the newly supplied V4 photographs are selectable in the profile editor. Re-running unchanged content migration does not overwrite newer edits.

The installer does not commit or push. The package deliberately contains no live `var/`, passwords, database, Git credentials or manuscripts.

## Commit and start

From the installed clone:

```bash
cd "$HOME/Documents/MPhill in biomedical sciences (medical microbiology)/GitHub tracker/MPHILL-research-2026"
bash scripts/commit-v4.sh
git push origin main
.venv/bin/python manage.py serve
```

The commit helper asks for `COMMIT`; only manifest-listed release files are staged. Existing unrelated staged work causes a stop so it can be committed separately. Your GitHub authentication remains managed by Git. A push rejection does not justify a force-push: inspect and reconcile remote changes before retrying.

Open `http://127.0.0.1:8000/admin` with your existing account. No new owner account is required. Profile/media edits remain local until published from the admin screen.

## Source conflicts or failures

A customization warning means **no source has been copied at that point**. Keep the local customized file and compare it with its release counterpart; merge deliberately rather than deleting it. Changes made inside the admin are database changes, not source customizations.

If a failure occurs after backup/copy starts, keep the printed backup directory and leave the server stopped. Some source files or the migration may already have changed. The installer does not pretend this is an atomic rollback. The backup contains the previous affected source and database; restore them together, not just the database against incompatible source. Preserve any new files/uploads produced after the backup before restoring.

For a dependency-only retry with already-verified installed dependencies, `--no-deps` skips pip. It does not bypass manifest or source-customization checks. It is not needed for normal use.

Keep all private backups out of Git. The source commit helper refuses common already-tracked runtime paths, but it is not a general secret scanner: review the changes and public seed content before pushing.
