# V6.2 → V7 upgrade and recovery

## Upgrade without replacing the working database

Stop the running application with Ctrl+C. Extract the complete V7 ZIP into a separate folder of your choice. Inside that extracted folder, run:

```bash
bash upgrade-v7.sh
```

At **Path to your existing repository**, enter only the actual clone's absolute folder path. Do not paste shell commands into this prompt. Review the source, target, database and backup locations, then type `UPGRADE`.

The installer verifies its release manifest and compares overlapping source against the original V6.2 release. It refuses customized source, symlink targets, the wrong repository, root/sudo execution or a detected running local server. Backups are private and outside the clone. It preserves `.git`, the current branch/index, `.env`, `.venv`, accounts, password hashes, uploaded files and edited records.

V7 adds missing fields, new private tables, 32 original openly reusable reflections and nine curated resource links. Existing edited content and quotation approvals are unchanged. Intentional tombstones are respected. New reflections can be disabled together in the theme or edited/removed individually. Existing media ownership is retained; albums are initially empty until deliberately assigned.

Only after **V7 installed.** appears, open a terminal in the existing installed clone and run:

```bash
bash scripts/commit-v7.sh
git push origin main
bash start.sh
```

Run each command only after the previous succeeds. Type `COMMIT` at the commit helper prompt. It handles already staged release files, refuses unrelated staged work and never stages runtime/private files. No `git init`, force push, broad `git add .` or second clone is needed.

Refresh administration with Ctrl+Shift+R. Review and publish from administration to update the website. Pushing application source alone does not publish your edited database content.

## Recovery

If migration fails, leave the server stopped and read the printed private backup's `migration-report.txt` and `recovery.json`. It includes the old source/configuration archive, consistent SQLite database backup and uploads archive. Preserve the failed installation for comparison rather than deleting it. Restore a consistent source/database pair together; do not mix a newer migrated database with older code without review.

The upgrade does not modify or delete an independently deployed response gateway. Its messages and backups live in that separate account. Preserve its private deployment directory and key independently. Do not post recovery archives, passwords or keys in a public issue.
