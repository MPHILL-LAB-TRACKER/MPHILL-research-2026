# V6.2 verification

## Executed suites

| Suite | Result | What was exercised |
|---|---:|---|
| PHP core, migration and Git | 36 checks passed | Existing accounts/password hashes, private/public projection, repeatable exports, real pushes to temporary local Git remotes, preserved branch/index, changed-preview rejection and publishing permissions. |
| PHP HTTP application | 66 tests passed | V6/V6.1 regression cases plus photographic assets, appearance modes, approval/source validation, metadata deduplication, error status, cache invalidation, ETags, public projection, ownership and administrative rights. The tests execute a real PHP HTTP server. |
| Chromium interface | 32 checks passed | Five navigation groups/search; shared appearance; photographic selection/save; source/quote/cache panels; portrait replacement; independent milestones; resource tracker; quote approval/rotation/tags; mobile navigation/overflow; reduced-motion; no uncaught JavaScript exceptions. |
| Service Worker behavior | 25 checks passed | Public immutable-asset cache hit; bounded eviction; release invalidation; unrelated-cache preservation; disabled-cache behavior; bypass of HTML, admin/API/forms, PDFs, video and range requests; private/no-store rejection; oversized responses; blocked/quota-limited storage fallback. |
| Cloud feed CLI policy | 10 checks passed | Disabled/review/local policies produce no cloud output; policy digest/interval checks; stale-item expiry; no fabricated successful-source timestamp; metadata-only output. These checks make no external requests. |
| Original V6.1 upgrade and source commit | 39 checks passed | Original V6.1 package as the fixture; normal-user installer; path prompt with spaces; wrong target/root/custom source rejection; preserved account hash, biography, private fields, uploads, environment, Git history/branch/index, colour choices and homepage ordering; private starter quotes; backup permissions; safe resume of already-staged release files; repeatable migration. |
| Syntax | Passed | All PHP files linted; browser scripts checked with Node; shell launch/upgrade/publishing scripts checked with Bash. |
| Release | Verified at packaging | ZIP CRC and SHA-256 for every manifest file; no runtime database, uploaded private data, credentials, font files or compiled native executable shipped. |

## Test environment and limits

PHP 8.4.23 used the compiled optional C++ SQLite adapter; FFmpeg/FFprobe performed image/video processing. PDO SQLite and GD were unavailable and were not executed. The delivered application retains those normal PHP extension paths.

Chromium uses an explicitly declared fetch/image bridge to the real local PHP server. Direct browser navigation is blocked in this environment. Interface checks are not equivalent to a deployed browser/network test. Mobile checks are viewport simulations, not physical Android/iPhone certification.

Public source adapters were exercised with explicit bibliographic/blog fixtures. Live Europe PMC/PLOS retrieval and the GitHub-hosted scheduled workflow were not executed. The CLI checks validate policy handling and output boundaries; they do not claim to validate GitHub scheduling or remote credential permissions. Git pushes in the core suite used temporary local remotes only.

Optional Wikimedia glassware/fern imports were not downloaded here. Four external photographic assets were sourced from installed, documented example-image distributions; the fifth is the existing owner-supplied laboratory photograph. The latter is not openly licensed. The rights registry makes that distinction.

No real carrier/Wi-Fi comparison, production load benchmark, public PHP deployment, live GitHub push, Pages settings change or installation on the user's computer was performed. Caching cannot establish that the earlier mobile-data connection problem is fixed. Public HTML is deliberately not stored in the Service Worker cache; deleting an old downloaded file or Git history is outside cache invalidation.

Screenshot contents are temporary testing records, not the user's live database. Historical quote approval in screenshots is a test action; the six release seed records remain private until approved by an administrator.

## Reproduce

Use PHP 8.3+, Git, SQLite support, image/video support, and Node for the cache/script checks. HTTP/browser tests also require Python 3, requests, Playwright and Chromium. Python is a testing dependency, not the application runtime.

```bash
php tests/test_core.php
python3 tests/test_v62.py
python3 tests/test_browser_v62.py
node tests/test_cache_sw.mjs
php tests/test_cloud_policy.php
```

The build used `bash bin/build-native.sh` and the native test driver. Use `TED2_TEST_DRIVER=pdo` where PDO SQLite is installed; set `CHROMIUM_PATH` only if Chromium is not discoverable.

For the original-release upgrade test, extract the V6.1 archive separately and set `TED2_V61_FIXTURE` to that extracted application directory. Then run:

```bash
python3 tests/test_installer_v62.py
```

The upgrade test requires the complete current release manifest and uses a temporary repository. It runs as a non-root user (nobody when invoked as root in a suitable test container). The old archive is needed only for this explicit release-migration test, not ordinary application operation or unit tests. Previous test files are retained as historical contracts; V6.2 overrides intentional differences such as photographic rather than line-art output.
