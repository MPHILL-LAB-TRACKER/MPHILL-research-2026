# V5 verification report

The release was developed against repository main commit `10d16ac2a6e4fd8ca1a47d412856a0e5fcacd8e9` (V4). Live repository reads used the connected GitHub service. No remote source branch or public website was changed during this task.

## Backend and content tests

`python -m pytest -q`: **116 passed, 6 subtests passed** on Python 3.13.5/Linux. This includes the existing 94 regression tests and 22 V5 tests. Tests cover role and CSRF boundaries, password rejection, current-version conflict checks, record Trash/restore and purge dependencies, private projection of linked contacts/custom fields, field hiding, protected core fields, theme input validation, public logos, media permissions and migration preservation. Generated JPEG/PNG/WebP/GIF/BMP/TIFF files and real FFmpeg-generated MP4/MOV clips were passed through the upload validator. MOV conversion was exercised with FFmpeg/FFprobe installed.

## Browser interface acceptance

`python tests/render_v5.py`: **36 checks passed**, no unhandled script errors. Chromium rendered the real admin/public JavaScript and CSS with a temporary SQLite database. Fetch/XHR were explicitly bridged to FastAPI TestClient; the browser did not use real localhost HTTP for those API calls. Checks included JPEG upload from a profile, researcher contact/custom-field assignment, clear/hide controls, public rendering, theme save/application, homepage/navigation hiding, Trash/restore/permanent deletion, MP4 upload, native video element, wrong password rejection and successful password-confirmed push to a real temporary local bare Git remote. The source branch stayed unchanged and public output excluded private source/database files. A 390-pixel viewport was checked for horizontal overflow.

Native video element presence and upload validation were tested, not every browser's actual codec playback. Test screenshots show synthetic acceptance-test records, not changed live researcher data. Optional screenshot capture can be enabled with `TED2_TEST_SCREENSHOTS=1`; some captures stalled in the restricted environment, so the final acceptance run did not depend on screenshots.

A separate real HTTP browser test (`tests/browser_v5.py`) was attempted. The local server and health request succeeded, but Chromium navigation was denied with `net::ERR_BLOCKED_BY_ADMINISTRATOR`. Consequently live end-to-end HTTP/browser login and navigation are **not verified here**. The test is included for use on an unrestricted local workstation; its results must not be confused with the in-memory acceptance report.

## Upgrade and commit verification

**27 installer/commit checks passed.** The checks use an ordinary non-root test account, a disposable Git clone, the original V4 source ZIP, an existing owner account, an owner-edited biography and retained runtime upload. They exercise the actual V5 installer with already-installed dependencies, the migration, source commit allowlisting, refusal of unrelated staged work, preservation of Git state and refusal of customized source. The machine-readable result is `docs/test-results-v5/installer-report.json`.

## Scope and remaining limits

No live GitHub push, actual GitHub Pages deployment, remote credential setup, external image delivery or production HTTPS hosting was exercised. The supplied source/upgrade scripts do not grant GitHub write access. Dependency installation on the user's computer still requires internet access. Large/long video transcodes, every codec, every browser and every possible theme contrast combination were not tested. Prior publication copies and Git history are not erased when a local record is deleted.

Existing V3/V4 reports retained in the package are historical; this file describes V5. Package SHA256 verification detects accidental byte changes but is not a cryptographic publisher signature. The final ZIP is checked for archive integrity and every listed release file against its manifest.
