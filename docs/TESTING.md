# V6.1 verification report

## Executed checks

| Suite | Result | Scope |
|---|---:|---|
| PHP core/migration/Git | **36 passed** | Original regression checks, account hash preservation, public/private projection, repeatable exports, real temporary Git pushes, original branch/index preservation, changed-preview rejection and publishing permissions. |
| PHP HTTP application | **52 tests passed** | Includes all 32 V6 HTTP regressions and 20 V6.1 cases. Real local PHP HTTP server, native prepared-statement SQLite adapter, login/CSRF/permissions, portraits, themes, ownership, methods/procurement, questionnaire batching, facts, source deduplication, worker due-time fixtures, network-safe export and new routes. Theme/motif subtests are not counted as extra tests here. |
| Chromium interface | **49 checks passed** | Real PHP API through an explicit in-memory browser transport; login, all 14 preset choices/19 ornament options, saved theme shared by both interfaces, browse portrait replacement/removal/approval, scoped media, methodology/procurement UI, readiness calculations, question builder/reorder/answers, notice controls and mobile layouts. No JavaScript page errors. |
| Original V6 upgrade/commit | **36 checks passed** | Actual original V6 release copied into a temporary local Git repository. Original V6 PHP created the database. Non-root installer preserved password hash, edited biography/private data, uploads, environment, Git branch/history/index, owner colours and selected homepage sections. It also upgrades the verified legacy V5 VERSION file still present on the V6 main branch. It rejected wrong folder/root/custom source/unrelated staged work; resumed release-only staged work; produced private backups and an idempotent migration. |
| Syntax | **Passed** | PHP lint for every PHP source; Node syntax checks for site/admin JavaScript; Bash syntax checks for launcher, installer and commit/diagnostic scripts. |
| Release integrity | **Passed at packaging** | Every packaged path checked against the SHA-256 release manifest; ZIP extraction/CRC check; no database/runtime/private uploads/secret environment/native binary shipped. |

### Portrait defect reproduced and covered

V6's direct upload received a new upload ID but subsequently reconstructed the form from the old hidden input. V6.1 passes the updated form snapshot to saveEditor. The browser regression selects a replacement JPEG, checks that the new ID persists in the real PHP record, verifies the editor image, removes all portrait fallbacks, then restores and approves the picture. Anonymous portrait-preview requests are rejected; authorised own/admin requests work.

### Procurement and approval boundaries

Tests cover optional project/method relationships, a required explicit method-step explanation, decimal/negative quantity handling, same-researcher references, private-method publication blocking, expired-stock exclusion, shortfall/to-source calculations, and exclusion of private supplier/cost/action details from exports. Assigned researchers cannot read/edit another researcher's private method or procurement list. Starter facts require explicit approval; expired facts are removed from public projection. No real methodology, order or experimental result is fabricated for tests.

### Questionnaire and discovery checks

Batch question saving/reordering is atomic. Stale versions are rejected. Removed questions enter Trash and existing response snapshots are retained. The browser submits a guided anonymous questionnaire to the real PHP server.

Research source fixtures exercise bounded ingestion, DOI/source deduplication even after record deletion, private review status, check intervals and optional watches. These fixtures are marked as test metadata and never included in the release seed. No live Europe PMC fetch is claimed. No unattended public claim-writing or Git push is performed by the research worker.

## Important limits

- Build runtime: PHP **8.4.23**, compiled optional C++ SQLite adapter and FFmpeg/FFprobe. **PDO SQLite and GD were not installed in the environment and were not executed.** Normal installations may use those PHP extensions; the release still contains both code paths.
- Direct Chromium navigation to localhost was attempted and failed with **ERR_BLOCKED_BY_ADMINISTRATOR** in the environment. Browser tests therefore use an explicitly declared fetch/image bridge to a real HTTP PHP server. This is not a live end-to-end browser/network deployment test.
- The public GitHub URL could not be loaded directly by the browsing environment. Current repository branches and export structure were inspected with the GitHub connector. This does not test the user's network.
- No physical Android/iPhone, mobile carrier, VPN, DNS resolver, TLS interception, production host, performance/load test or live GitHub publication was verified. **The reported Wi-Fi-only/mobile-data problem remains unconfirmed.** Low-data/connection routes and a read-only network comparison script are included to isolate it.
- Responsive checks passed at widths **320, 390, 430 and 768 pixels**, including horizontal-overflow checks and mobile navigation; they are Chromium viewport simulations, not hardware certification.
- Temporary local Git repositories were used for actual push tests. No push to the user's repository, Pages settings change or installation on the user's computer occurred.
- Screenshots are test previews, not the user's live database. Resource examples in screenshots are nonexperimental demonstration data.

## Reproduce

Runtime prerequisites: PHP 8.3+, SQLite via PDO or the compiled optional adapter, image processing through GD/FFmpeg and Git. Browser/HTTP test prerequisites: Python 3, requests, Playwright and Chromium. Test commands create temporary databases/repositories, not modifications to the operator's live database.

```bash
php tests/test_core.php
python3 tests/test_v61.py
python3 tests/test_browser_v61.py
```

Set `TED2_TEST_DRIVER=pdo` for browser/HTTP execution with PDO installed, or use the default native adapter after `bash bin/build-native.sh`. Set `CHROMIUM_PATH` only when Chromium is not discoverable. The browser report always identifies its explicit in-memory transport.

For the original-release migration test, extract the original V6 ZIP beside the V6.1 folder, or set `TED2_V6_FIXTURE` to its actual extracted path. Then run:

```bash
python3 tests/test_installer.py
```

That test runs the installer as a non-root account (nobody when executed by root in a test container) and requires the completed release manifest. It does not contact a remote Git service. The original fixture is not bundled into V6.1; ordinary runtime and unit tests do not depend on an old ZIP being present.
