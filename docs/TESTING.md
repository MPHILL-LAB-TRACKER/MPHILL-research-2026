# Validation report — 10 September 2026

## Results

**46 / 46 backend and security regression tests passed.**

Command:

```bash
python -m unittest discover -s tests -v
```

The assertions exercise the real FastAPI routes with temporary SQLite databases, not mocked authorization. They cover anonymous denial, `/admin` role checks, researcher assignment boundaries, public publishing restrictions, public-field allowlists, private relationship filtering, CSRF/Origin checks, password changes, login throttling, session expiration/revocation, protected documents, photo approval, rejected upload types, request limits, audit events, explicit publication types and optimistic edit conflicts.

**43 / 43 in-memory Chromium UI checks passed, with zero JavaScript runtime errors.**

Command:

```bash
python tests/render_check.py
```

This renders the actual public and management templates in Chromium without navigating the browser to a network URL. Forms call the real application through a local FastAPI TestClient bridge. The bridge supplies a same-origin test Origin header and retains test cookies. Document redirects are captured as intended destinations. Therefore these checks validate UI rendering, form payloads, page state and application behavior, **not real browser cookie policy, live network navigation, TLS or a deployed origin**.

UI checks include desktop/mobile overflow, mobile menus, corrected names, legacy profile routing, three Kadhila papers, researcher/publication search, sign-in, biography updates reflected in the public projection, project and milestone assignment, weighted progress, manuscript stages, private notes, account creation and the researcher-only workspace. The test accounts and sample project/manuscript/milestone/update records are temporary; they are not in the delivered public dataset.

**Python and JavaScript syntax checks passed.** Python modules were compiled, and both public/admin scripts passed `node --check`. The compiled public page was rebuilt after the final script formatting changes.

## Live-browser limitation

`tests/browser_check.py` starts a real loopback HTTP application and is supplied for staging validation. In this environment the managed Chromium policy blocks all URL navigation, producing `net::ERR_BLOCKED_BY_ADMINISTRATOR` on the first local-page visit. No policy was modified or bypassed. The live-navigation run did **not** pass and is not included in the successful check counts above. Run it in an unrestricted local/staging browser before deployment.

## Image limitation

External image requests were intentionally aborted in the successful rendering checks. This tests the reference-photo and initials fallbacks; it does not establish remote source availability, image-file download success, licence permission or browser third-party privacy behavior. Two named portrait URLs are included, but no researcher photograph files were downloaded in this environment.

## Environment tested

Python 3.13; FastAPI 0.128.2; Starlette 0.50.0; Uvicorn 0.48.0; python-multipart 0.0.29; argon2-cffi 25.1.0; Pillow 12.3.0; HTTPX 0.28.1; Playwright 1.57.0; system Chromium. These are the direct package versions used here, not a claim that they will remain the latest or free of future advisories.

Clean dependency installation, other operating systems/Python versions, a Docker build, live TLS/reverse-proxy configuration, institutional account policies, penetration testing, production backups/restores and the actual GitHub deployment remain untested. No production server was created or changed.

## Delivered evidence

`test-results/backend-tests.txt` contains the full unit-test output. `test-results/render-report.json` records the named UI checks and scope limitations. Screenshots in `screenshots` show the actual rendered interface. Where a screenshot contains a `UI test` label or account name, it is clearly temporary test data, not an assertion about laboratory activity.
