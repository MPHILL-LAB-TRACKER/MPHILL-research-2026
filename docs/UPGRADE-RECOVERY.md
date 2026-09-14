# V6 → V6.1 upgrade, preservation and recovery

The target must be the existing `MPHILL-research-2026` clone, not its empty parent Git repository and not the extracted release. This installer is specifically baselined against V6 source hashes. Older V2–V5 installations need the V6 upgrade first; this package does not silently merge arbitrary source versions.

Preflight, with the server stopped and from the extracted release:

```bash
bash upgrade-v6.1.sh --target "$HOME/Documents/MPhill in biomedical sciences (medical microbiology)/GitHub tracker/MPHILL-research-2026" --dry-run
```

Checks include the expected Git remote, exact repository root, release checksums, source customisations, destination symlinks, existing database and SQLite adapter, local server port, and normal-user execution. The dry run writes no application files. The actual operation requires UPGRADE unless the operator deliberately supplies `--yes`.

The installer preserves `.git`, the current branch/index, accounts/password hashes, `.env`, `.venv`, database content, uploaded files and unrelated work. No reset, force-push, second clone or global Git configuration is used. Source files are copied only from the manifest. Extra legacy files are left in place, not automatically removed. Existing .gitignore entries are preserved and runtime exclusions are appended.

An external owner-only folder under `~/TED2-private-backups/v6.1-*` holds source/configuration, a consistent SQLite backup, uploads when present, actual path metadata and the migration report. Backups contain private data; never commit or publish them. The database migration also creates its own private pre-migration SQLite copy, adds absent defaults and durable discovery identities, and records its completion. Existing V6 sessions, account hashes, permissions and owner-selected field values are not reset. Newly introduced draft science facts stay private.

The commit helper supports release paths already staged after an interrupted attempt. It refuses unrelated staged work, lists without paging and commits only the manifest's paths. It does not push; `git push origin main` remains deliberate. Content publication from admin separately targets gh-pages and does not move or overwrite the main source branch.

If preflight fails, correct the reported condition; do not force replacement. If copying or migration fails, leave the server stopped and read the report. Preserve the failed state separately before recovery. Restore source/configuration, database and uploads from the SAME backup set. All PHP/worker processes must be stopped before replacing SQLite files. Keep a separate copy of any WAL/SHM files; stale sidecars must not be mixed with the restored database. Recovery is a deliberate operator procedure, not a blanket Git reset. Start the restored V6 PHP application only after restoring its paired database and source.

Do not run the legacy V5 Python application against a database containing later PHP-only records. Do not delete var or create a new empty installation to bypass a failed upgrade. For an externally configured database, use the exact paths recorded in recovery.json.
