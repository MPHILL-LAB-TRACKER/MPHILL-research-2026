# Upgrade safeguards and recovery

The upgrade is an in-place source migration, not a new empty account installation. It validates checksums and the expected Git remote, refuses overwritten symlinks, stops for conflicting source files, confirms the current local server is stopped, and backs up source/configuration, SQLite data and uploads outside the repository.

It adds V6 tables and fills missing fields without resetting owner-edited values. Existing accounts and Argon2 hashes remain. Old sessions are revoked. Existing V5 researcher accounts retain research editing but require a deliberate owner grant for the new profile editor.

Each backup folder contains `source-and-config.tar.gz`, `ted2.sqlite3`, `uploads.tar.gz` when uploads exist, `recovery.json`, and `migration-report.txt`. `recovery.json` records the actual source and database paths, including an externally configured database. These archives contain private data: keep them private and never upload them to the Git repository.

If installation fails, do not restart or repeatedly force the installer. Read the error and migration report first. No automated force-reset or blanket Git cleanup is used. For rollback, stop PHP; preserve the failed upgrade for diagnosis; recover the previous source/configuration from its archive and the paired database/uploads from the same backup. Remove stale SQLite `-wal`/`-shm` files only after all processes are stopped and a separate copy is retained. Start the old V5 Python launcher only after restoring a consistent pre-upgrade backup. Do not alternate V5 and V6 against one live database after making V6-specific edits.

A safe preflight is available:

```bash
bash upgrade-v6.sh --target "$HOME/Documents/MPhill in biomedical sciences (medical microbiology)/GitHub tracker/MPHILL-research-2026" --dry-run
```

The installer does not publish, configure GitHub Pages or erase `main` history. The source commit helper stops on pre-existing staged work. Browser publication uses a separate temporary index and leaves source-stage changes untouched.
