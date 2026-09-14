# Upgrade V6.1 to V6.2

Use the complete V6.2 release archive. Stop the existing PHP server and local worker before upgrading. Extract the archive wherever convenient; do not extract it over the working application by hand.

From the extracted **V6.2 package directory**, run:

```bash
bash upgrade-v6.2.sh
```

The script asks for the path to your **existing Git repository**, then shows the source, target, database and backup locations. Enter `UPGRADE` only after checking those locations. Paths containing spaces are supported. No new clone or `git init` is required. Do not run the installer with `sudo`.

An explicit `--target` argument is also supported. To avoid embedding anyone's private directory layout in instructions:

```bash
read -r -p 'Existing repository path: ' TARGET
bash upgrade-v6.2.sh --target "$TARGET" --dry-run
bash upgrade-v6.2.sh --target "$TARGET"
```

The dry run validates paths, package hashes and overlapping source changes without applying the upgrade. Automated installations must supply `--target` explicitly before using `--yes`.

## Preservation and migration

The installer uses the original V6.1 checksums to detect customised source. It refuses an unknown overwrite instead of silently discarding local code. It preserves `.git`, the staging index, `.env`, any existing Python environment, accounts, password hashes, database edits and uploads.

A private backup under `~/TED2-private-backups/` contains source/configuration, a consistent SQLite copy, uploads and the migration report. New settings are additive: existing colours, profiles, project content, questions, procurement and media are not reset. Two new homepage block choices, `pulse` and `quotes`, are added near the existing facts block. They can be reordered or hidden; no external headlines or quotation records are automatically approved during migration.

V6.2 initially imports six **private** quotation records. The photographic header/footer selectors use new fields; old line-art settings are retained for recovery but no longer rendered by the V6.2 layout. A newly imported optional photograph is stored privately until it is selected for the public design and included in a publication.

## Commit and run

From the **existing application repository** after a successful upgrade:

```bash
bash scripts/commit-v6.2.sh
git push origin main
bash start.sh
```

The commit helper supports release files already staged from an interrupted attempt. It refuses unrelated staged work. It commits source files only; it neither publishes local research nor uploads the database. When a push fails, stop and resolve that error before assuming the release is on GitHub.

Use the local admin to prepare, review and publish the generated site to `gh-pages`. Committing PHP on `main` is not a website publication. Review the deployment status separately.

## Recovery

Keep the application stopped after a failed migration. Read `migration-report.txt` and `recovery.json` in the printed backup directory. Restore the source archive to the same target and the database backup to the recorded database path; restore the uploads archive only when necessary. Do not replace a newer database with an older one without first backing up the newer data. Keep Git history and separately staged work intact. Contact your system administrator before restoring an installation containing subsequent research edits.
