# TED² V6 — verification report

Release: **6.0.0**. Verification date: **13 September 2026**.

## Executed tests

| Suite | Actual result | What was exercised |
|---|---:|---|
| PHP core, migration and Git | **36 named checks passed** | V5 field/password preservation, idempotent migration, prepared statements and rollback, deterministic public export, directory order, private-data exclusion, real local Git push, stale-preview/replay rejection and researcher publishing denial. |
| HTTP regression | **32 test cases passed**, including parameterised logo/theme checks | Real HTTP requests to a temporary PHP application; session/CSRF/origin/host validation; record CRUD; optional milestone project; researcher isolation; actual image and MP4 processing; range responses; themes; logo slots; contacts; media ownership; trash/restore; anonymous questionnaires/moderation; static export. |
| Chromium interface | **27 named checks passed** | Real admin JavaScript, form submission, upload, scoping, caption/filename editing, theme save on both interfaces, optional milestone project, publishing form without repeat-password input, responsive navigation and homepage carousel controls. |
| In-place upgrade and source commit | **29 named checks passed** | Original V5 package copied into a temporary Git clone, original Python-created database/password hash, non-root installer, external backup, preservation of environment/uploads/history/staged work, fail-closed custom-source handling, release-only commit and repeat dry run. |
| Source syntax | Passed | PHP syntax checks, Bash parser checks, JavaScript syntax checks and C++17 compilation with warnings enabled. |

The Git suites used **real temporary local bare repositories**, never the user's remote repository. The installer suite used the original V5 package and the original V5 database initializer. Source commits were made only in temporary test clones.

## Browser transport — important limitation

Direct Chromium navigation to the local application was blocked by the build environment's browser network policy. The browser suite therefore loaded HTML/CSS from a real temporary PHP server and used an explicit in-memory bridge for HTTP requests and images. This exercised the actual JavaScript and backend, not fabricated API responses, but it is **not an end-to-end production-browser navigation test**.

Rendered widths were 1440 px desktop and 390 px mobile. Screenshots are available with the release handover. No JavaScript exceptions or horizontal page overflow were observed in the checked screens. There was no physical iPhone/Android device, Safari/WebKit or Firefox test. Universal device support is not claimed.

## Runtime actually exercised

- PHP **8.4.23** CLI application server.
- Included C++17 prepared-statement SQLite adapter and native metadata-ranking mode.
- FFmpeg/FFprobe image fallback and H.264/AAC video normalisation.
- Linux, Chromium, Python HTTP driver and Playwright interface driver.
- The container did not provide PHP PDO SQLite or GD. Those supported adapters **were not exercised here**; they require deployment verification. Normal Ubuntu installation uses `php-sqlite3` and `php-gd`.

## What has not been verified

There was no live GitHub publication, Pages configuration change, production TLS/FPM deployment, public anonymous-form submission from an external device, Europe PMC network refresh, load/concurrency benchmark or search-engine indexing/ranking test. No claim is made that language choice alone increases traffic capacity.

Git push, Pages source selection and Pages build/deployment status are now separate states. A status request that cannot authenticate is shown as unknown, not success. GitHub permissions and internet connectivity remain deployment requirements.

Literature watch was checked for opt-in behaviour and PHP/C++ metadata-ranking agreement. An actual Europe PMC network fetch was unavailable; failed requests report an error and do not create invented findings.

## Re-run

From a development copy (not against a production database):

```bash
bash bin/build-native.sh
php tests/test_core.php
python3 tests/test_http.py
```

The optional interface test needs Playwright, requests and a Chromium executable:

```bash
python3 -m venv .venv-tests
.venv-tests/bin/pip install playwright requests
CHROMIUM_PATH=/usr/bin/chromium .venv-tests/bin/python tests/test_browser.py
```

The V5 upgrade integration test additionally needs the extracted V5 release and its Python dependencies; it constructs temporary copies and never edits that source fixture:

```bash
TED2_V5_FIXTURE="../TED2-Research-Workspace-v5" python3 tests/test_installer.py
```

`TED2_TEST_DRIVER=pdo` selects PDO SQLite for HTTP/browser verification on a host where it is installed. Test credentials exist only in test code and temporary databases, not in a delivered database or deployed default account. Runtime and browser-output folders are excluded from the ZIP and Git commit helper.

## Release integrity

`release-manifest.json` lists the SHA-256 of each source/asset file, excluding the manifest itself. The companion ZIP checksum covers the complete archive. Packaging verification checks each file and rejects runtime databases, passwords, `.env`, uploads, compiled native binaries, `.git`, Python environments and font files. Checksums detect corruption; they are not a cryptographic publisher signature.
