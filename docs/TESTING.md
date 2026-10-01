# V7 verification

Verified in the build environment on 1 October 2026. No changes were made to the user's computer, GitHub branches, Cloudflare account or Overleaf projects.

| Suite | Result | Scope |
|---|---:|---|
| PHP core/migration/Git | 36 checks passed | Existing permission, projection, ZIP/site integrity and actual Git operations against temporary local remotes. |
| PHP HTTP application | 84 test cases passed | Preserved V6.2 regressions plus visitor challenge/replay, private receipts, moderation/consent, writing ZIP and export privacy, researcher scoping, album ownership, private/trashed album files, date expiry, public routes and valid exported links. |
| Chromium interface | 45 checks passed | Real temporary PHP/database through an explicit in-memory HTTP/image bridge; owner login, themes, manuscript source/save/ZIP, Overleaf consent form, gallery folders, expiry, quotation changes, public/private visitor replies, mobile widths and no uncaught JavaScript exceptions. |
| Worker + SQLite | 32 checks passed | Actual Worker handler using WebCrypto and Node's real SQLite with a small D1-compatible adapter. Auth, CORS, bounded body, consent, replay/limits, lookup, deletion and no public key leaks. Not Cloudflare deployment. |
| Original V6.2 upgrade/commit | 39 checks passed | Copied original V6.2 ZIP, non-root installation, unchanged passwords, edited biography/private fields, uploads, Git history/index/staged work, protected source edits, backups, idempotent migration and allowlisted source commit. |
| Response provisioning | 13 checks passed | Mocked Wrangler orchestration, cancellation, supported CLI syntax, idempotent database lookup, generated configuration and private persistent key. Does not contact a provider. |
| Trusted LaTeX templates | 3 templates compiled | Packaged report, review and protocol outlines compiled with pdflatex and shell escape disabled, in a temporary developer test only. Not a user-source execution endpoint. |

All PHP sources, shell entry scripts and active JavaScript entrypoints passed syntax checks. The final release manifest and ZIP CRC/paths are checked during packaging.

## Runtime used

PHP 8.4.23 with the bundled source-built native SQLite adapter and FFmpeg/FFprobe. PDO SQLite and GD were unavailable here, so those alternate runtime paths remain unverified in this environment. Node 22.16 with `node:sqlite` was used for Worker contracts. Chromium ran through Playwright.

Direct browser navigation was blocked by the execution environment (`ERR_BLOCKED_BY_ADMINISTRATOR`). Interface tests therefore bridge browser fetch/image requests to a real local PHP server using Python. They do not prove production navigation, physical Android/iPhone behavior, carrier connectivity, real GitHub/Cloudflare publishing, anti-abuse strength under attack, or a complete accessibility/security audit.

No live Overleaf transfer or provider-side compilation was performed. Its documented form payload and locally generated source/archive were tested. The new cloud response service is not deployed or connected. Live research-feed providers and scheduled GitHub Actions were not revalidated; these existing features are retained, not claimed as new live integrations.

## Re-run

From the installed source:

```bash
php tests/test_core.php
python3 tests/test_v7.py
python3 tests/test_browser_v7.py
node --experimental-sqlite tests/test_responses_worker.mjs
python3 tests/test_service_setup.py
python3 tests/test_writing_templates.py
```

Browser tests need Python Playwright, requests and Chromium. Template smoke tests need pdflatex; the normal application does not. Set `TED2_TEST_DRIVER` or the documented PHP SQLite adapter settings for your environment. The original-release installer test additionally requires `TED2_V62_FIXTURE` pointing to an extracted, unchanged V6.2 package, then `python3 tests/test_installer_v7.py`.

Older version-specific test files remain as inherited regression contracts. Run the V7 suite, rather than assuming every older release-number assertion should still apply unchanged.
