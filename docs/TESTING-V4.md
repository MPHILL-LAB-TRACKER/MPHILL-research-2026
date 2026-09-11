# V4 release validation

Measured in the build environment on Python 3.13.5; these results replace the unverified counts in the earlier preview message.

- **94 backend tests passed**: existing application/content regressions plus V4 media approval, file validation, private contacts, sections, conservative migration, publication PDFs, password verification, CSRF, role restrictions, stale/replayed previews and real Git-object/push behavior against temporary local bare remotes.
- **73 regression browser checks passed** using in-memory Chromium with a TestClient API bridge: existing public pages, corrected portraits, researcher routes, certificate download, administrator editors and individual research workspace.
- **23 V4 browser checks passed**: sidebar search, browse and drag/drop uploads, MP4 upload validation, public media approval, new gallery creation/rendering, private-contact editing, preview preparation, incorrect/correct password dialogs and a real push to a disposable local remote. JavaScript fetch/XHR use an explicit local test bridge; no claim is made about production browser-origin transport.

**25 upgrade/commit checks passed** as a normal non-root account: existing V3 database migration; retained accounts, biographies, uploads, environment and Git staging; external private backup; release-only source commit; repeat upgrade; and safe refusal of customized source. These checks use disposable clones, not the user’s installed workstation.

JavaScript syntax checks passed for both public/admin code. External media requests were deliberately blocked in UI checks. All browser test records/accounts are temporary and are not shipped as laboratory data.

**Live browser navigation was attempted but blocked by this environment** (`net::ERR_BLOCKED_BY_ADMINISTRATOR` on loopback). Live GitHub pushes, GitHub Pages deployment, production HTTPS, antivirus guarantees, and all browser/video-codec combinations were not verified. The full server/browser staging test is included for an environment where navigation is allowed.

## Reproduce

```bash
.venv/bin/python -m pip install -r requirements-test.txt
.venv/bin/python -m playwright install chromium
.venv/bin/python -m pytest -q
.venv/bin/python tests/render_check.py
.venv/bin/python tests/render_v4.py
.venv/bin/python tests/installer_v4.py
# Optional real-origin staging test:
.venv/bin/python tests/browser_check.py
```

Run installer checks as a normal non-root account. They create disposable local clones and a V3 database, use existing dependencies without pip/network, and never touch your real installed database or GitHub. The normal release upgrade, unlike the test, installs the pinned requirements unless explicitly told otherwise.

Reports are in `docs/test-results-v4/`; current screenshots are in `docs/screenshots-v4/`. Older testing documents/screenshots describe historical versions and are retained for context, not presented as new validation.
