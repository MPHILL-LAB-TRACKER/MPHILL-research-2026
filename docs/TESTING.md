# V3 validation report

## Executed checks

**66 backend and content/security tests passed**, using temporary SQLite databases and FastAPI TestClient:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

This includes the existing 46 regression tests and 20 new checks for source-to-profile mapping, all 11 local portrait images, the exact supplied and host-published conference dates, name corrections, certificate bytes and evidence attribution, date validation, public/private boundaries, certificate approval and replacement uploads, denied asset-directory access, admin-only new collections, and a conservative V2→V3 update that preserves owner edits and is repeatable.

**73 in-memory Chromium rendering and interaction checks passed:**

```bash
python tests/render_check.py --output test-results/render
```

The public snapshot was rendered directly in Chromium with remote network requests deliberately aborted. All 11 presentation portraits decoded successfully, the certificate preview rendered, and the participation-certificate PDF downloaded with bytes matching the supplied original. Desktop/mobile layouts, researcher aliases, individual activity pages, the three homepage presentation cards, the seminar card, official-only event links, date-discrepancy labels, and the expired-event archive transition were checked.

Administration forms were connected to the actual application routes through an in-memory TestClient transport. The checks exercised biography edits, alert changes, certificate approval revocation, safe blank defaults for new portrait/certificate records, projects, milestones, manuscript states, accounts, per-researcher progress, and private-data exclusion. Test accounts and temporary records are not included in the shipped seed.

JavaScript syntax checks passed for both public and administrative scripts. No JavaScript runtime errors were recorded during the rendering checks. The supplied PDF was preserved byte-for-byte; the browser download also matched those bytes. All 12 original homepage capability records and all 8 publication records are unchanged.

## Scope limitations

The live-origin test was attempted:

```bash
python tests/browser_check.py --output test-results/browser
```

This environment blocked browser navigation to the local test origin with **`net::ERR_BLOCKED_BY_ADMINISTRATOR`**. This is recorded as **not completed**, not as a passing end-to-end test. No browser policy was changed. In-memory UI checks do not verify browser-origin cookie behaviour, HTTPS, reverse proxies, production deployment, live GitHub Pages connectivity or a remote image server.

The original source Instagram post could not be retrieved. Public conference content uses accessible official organiser/host pages plus clearly distinguished owner-provided notices. The remaining remote photograph references were not verified for live delivery or reuse permission in this release.

Test result files are under `docs/test-results/`. Screenshots are under `docs/screenshots/`. Run the live-origin suite and deployment checks on the actual staging server before production release. No repository commit, production account, server or deployment was created during this update.
