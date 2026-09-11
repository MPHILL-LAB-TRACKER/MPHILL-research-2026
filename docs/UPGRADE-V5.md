# V5 upgrade and recovery

Use the complete V5 ZIP and `upgrade-v5.sh --target` with the existing repository root, not its parent or another extracted release. Stop the application before running. The installer refuses a listening configured local port, wrong repository root, missing database/environment, unsafe symlink destinations, checksum failures or source files that differ from both the new release and recorded prior release baselines.

## What is preserved

The installer does not replace `.git`, `.venv`, `.env`, the existing database or its adjacent upload directory. It copies application source after verification and runs the conservative content migration. The original V4 baseline has been added to the comparison data. Owner-edited values differing from shipped baselines are preserved; Trash tombstones prevent deleted seed records from returning. Existing owner credentials are unchanged. The new theme is inserted only when absent.

The old `index.html` is backed up and rebuilt from the current approved database using the V5 renderer. A previously embedded public snapshot is not treated as the source of truth over the database. Approved uploads may be embedded in this rebuilt file; browser publishing uses separate files and is preferred for large videos.

Source and data backups are created under `~/TED2-private-backups/v5-<timestamp>-<unique>/`, with a mode-0700 parent and a mode-0600 SQLite copy. The backup contains `source/`, `ted2.sqlite3`, and `uploads/` when present. The source backup includes the old config/manifest and release-owned files, not the `.git` object store. Dependencies are installed into the existing virtual environment; that environment is not itself copied into the backup. Printed reports identify preserved owner fields.

## Failure and recovery

Stop on an error. Do not delete the existing database, reinitialize the application, use `git reset --hard`, or rerun under sudo. The installer prints the backup directory before copying source. A failed upgrade may have copied some code; it is not an atomic filesystem transaction. Keep the server stopped until repaired.

For a full rollback, retain the current failed state separately and restore the old source files, old configuration and database together from the printed private backup, with the server stopped. Restore the adjacent uploads when necessary. Remove any V5-only source files not present in the older release before returning to that older application. Reinstall the older pinned requirements into the virtual environment. Do not restore old files over newer data without deciding whether edits made since backup must be kept. Keep backups outside the public repository.

The upgrade does not commit or push. After it succeeds, review `git status`, use `bash scripts/commit-v5.sh`, then `git push origin main`. The helper refuses existing staged work and tracked runtime data. It stages only manifest-owned paths; it is not an all-purpose Git wrapper.

V5's browser publication targets the existing repository's gh-pages branch and requires a preview plus current administrator password. It does not change the source checkout, force-push, automatically change GitHub Pages settings, or erase historical Git content.
