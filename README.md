# TED² Laboratory — Website & Research Workspace V3

**A public laboratory website, an owner/admin content manager, and an individual research workspace.**

This update continues the cream-and-forest-green design of the existing TED² website. Detailed researcher work and publications stay on dedicated pages; the homepage adds concise activity alerts and a researcher-recognition teaser. The homepage retains all twelve descriptions from the supplied Tissue Engineering document.

## Start here

| What you need | Use this |
|---|---|
| Update the existing public GitHub page immediately | Upload this package’s root **`index.html`**, replacing the existing file. This is a standalone public snapshot. |
| Edit profiles, upload photos and track research locally | Extract the complete package and run **`python start.py`**. |
| Make admin changes update the live GitHub website | Host the Python application behind HTTPS, then use **Administration → Publish & export → Connected public page** and upload that file as the repository’s `index.html`. |

**A GitHub Pages upload alone does not activate the admin system.** GitHub Pages hosts static files; the authenticated database-backed application needs a server. The connected public page lets the existing public address remain unchanged while edits and private research live on the separate server.

## What changed in V3

The public website now has **11 locally bundled portraits extracted from the labelled photographs in `Team.pptx`**, with matching team roles, affiliations, postgraduate programmes and research topics. These images also work in the standalone HTML without a remote image server. The roster remains **10 researchers and 2 collaborators**, and all **8 existing publication records** and **12 homepage research descriptions** are preserved.

Names follow the new presentation: **Dr Albertina Shatri, Ms Denise Bouman, Dr Maneria Halweendo, Ms Charity Maepa, Ms Nonku Phili and Ms Jaydine Jeris**. The corrected **Ms Vevangapi Mbatara** entry is retained. Existing internal record IDs are deliberately stable; both legacy and corrected-name profile links continue to work. Prof Nailoke Pauline Kadhila is not pictured in the supplied presentation, so her previous profile, selected bibliography and remote portrait reference are retained.

A new **Alerts** section on the homepage lists the three requested conference presentations, with a separate **Coming soon — Nanomedicine in Health** seminar-series notice. Each conference notice also appears on its named researcher’s profile. Detailed activity pages link to official organiser websites, not Instagram. Dated notices leave the upcoming homepage list after their end date and remain in the Activity archive; this does not imply that a planned presentation actually took place.

**Date discrepancy requiring confirmation:** the laboratory supplied **17–18 November 2026** for Dr Albertina Shatri’s and Ms Naungwe Simasiku’s NCRST presentations. NCRST’s available official call lists **17–18 September 2026** for the 2026 Biennial National Research Symposium. The website keeps the supplied November schedule and visibly flags this discrepancy rather than silently replacing either source. UNAM’s official SANORD page confirms **22–25 September 2026**. Named presentation participation is laboratory-reported, not independently confirmed from a speaker programme. The supplied Instagram post could not be retrieved; no caption or changed date was inferred from it.

**Mr Paulus Hamutenya’s Falling Walls recognition** is on his profile, with a homepage teaser, certificate preview and downloadable original PDF. The note describes progression from 90 candidates to the top 16 without a top-three finish. The website distinguishes this owner-reported result from the certificate, which confirms participation on **25 August 2026**. The source PDF is preserved byte-for-byte and embedded in the standalone HTML.

The two new owner/admin sections are **Homepage alerts & events** and **Achievements & certificates**. They support private/public visibility, named researcher links, date evidence, homepage display controls and explicit certificate publication approval. Researcher accounts do not acquire administrative publishing rights.

The disliked grayscale cell photograph remains removed. The TED² and UNAM logos remain embedded; the existing background laboratory photographs remain remote references. See [the source and image audit](docs/PHOTO-AND-CONTENT-AUDIT.md) for attribution and limitations.

## Updating an existing V2 installation

For a static GitHub Pages site, replace only `index.html` with the V3 compiled file. Its team portraits and certificate require no separate asset upload. The static file does not enable the server-backed admin system.

For an already-running management application, replace its source files with this package **without deleting or replacing `var/`, `.env`, the database, or uploaded files**. Stop the application, activate its existing virtual environment, and run:

```bash
python manage.py upgrade-content
python manage.py upgrade-content --apply
python manage.py serve
```

The first command previews changes without writing. The second makes a private pre-update SQLite backup, applies the supplied content, and preserves owner-edited fields that differ from the V2 baseline. It does not replace accounts, private projects, manuscript records or upload files. Review any `preserved_owner_fields` in the report. Repeating the update does not reapply unchanged content.

A fresh installation needs only `python start.py`; it imports the V3 seed normally. After upgrading a hosted server, export a new **Connected public page** and replace the repository’s `index.html` so the public design also receives the new Alerts and certificate components.

## Editing the new sections

**Conference and seminar alerts:** open **Website content → Homepage alerts & events**. Edit the title, description, linked researchers, dates and official host URL. Keep unresolved NCRST dates marked **Date conflict**, with the public evidence note. Once the organiser confirms the dates, update the schedule, date-evidence status and note together. For an undated seminar, use **Date to be announced** and leave its date fields empty. Select **Show in homepage Alerts** and **Public** when ready.

**Recognition and certificates:** open **Website content → Achievements & certificates**. Edit the achievement and evidence note, select the researcher, and control the homepage teaser. The supplied Falling Walls document is available under **Owner-supplied certificate**. To replace it, upload a PDF, save the record, and deliberately approve **Publish certificate PDF**. A replacement upload takes priority over the bundled PDF. Unchecking approval removes the document from future public API responses and exports; previously downloaded snapshots cannot be recalled.

**Team photographs:** each updated profile has a **Portrait supplied in Team.pptx** selection. An approved uploaded portrait overrides that selection. Choosing the empty option removes the bundled fallback; revoking portrait approval stops public delivery of the bundled image. The supplied photographs were used at the owner’s request, not assigned an open reuse licence.

## Local setup

Python 3.11 or newer is required; the delivered application was tested on Python 3.13. From the extracted folder:

```bash
python start.py
```

Use `python3 start.py` on systems where Python 3 is named `python3`.

The launcher creates an isolated `.venv`, installs dependencies, imports the public seed data and asks you to choose the first **owner username and password**. There is no default password or public account registration. Initial dependency installation needs internet access. The launcher binds only to your computer’s loopback interface.

After startup:

| Page | Local address |
|---|---|
| Public website | http://127.0.0.1:8000/ |
| Owners and administrators | http://127.0.0.1:8000/admin |
| Researcher workspace | http://127.0.0.1:8000/workspace |

Keep the terminal running while using the local site. Press Ctrl+C to stop it. Your edits remain in `var/ted2.sqlite3`; uploads remain in `var/uploads`. They are not stored only in the browser. **Keep this directory private and back it up.** Never upload `var`, `.env`, backups or unpublished manuscripts into the public GitHub repository.

For an existing prepared Python environment:

```bash
python -m pip install -r requirements.txt
python manage.py init
python manage.py serve
```

Running `init` again preserves existing content and accounts. Rebuilding the public seed file does not overwrite your running database.

## The administration area

The sidebar provides structured forms for homepage alerts, achievements/certificates, researchers/collaborators, publications, research projects, manuscripts, milestones, activity updates, collaborations, funders, homepage descriptions, site contact details and sources. Long text is entered as text, not executable HTML. Research interests and author lists use one item per line. Relationships use profile/project selectors, not manually typed IDs.

**Edit a biography:** open **Researchers & collaborators**, choose the profile, change the biography or research interests and select **Save changes**. Keep the record Private while reviewing it; select Public when its public fields are approved.

**Upload a portrait:** save the profile first, open **Uploaded portrait**, choose JPEG/PNG/WebP, then press **Upload portrait**. Add the photographer/source and set **Portrait permission → Approved** when permission has been confirmed. Press **Save changes** to attach the upload. An approved uploaded portrait takes priority over the presentation image and remote image URL. A successful upload alone does not save the rest of the form.

**Add a publication:** enter the actual title, year and author list; associate the relevant researchers; supply the DOI or source URL; choose the correct evidence type. University catalogue records and author-listed work remain distinguished from publisher-verified journal articles. Public PDF downloads require a separate deliberate flag and appropriate distribution rights.

**Create active research:** add the title, lead, research team, public summary, stage and dates. Link collaborations and funders only where the relationship is documented. Assign milestones to members of that project team. New records start private.

**Track each researcher:** open **Researcher progress** and choose the person. Their assigned projects, manuscripts and activity appear together. Internal completion is calculated from weighted milestones: completed milestone weight divided by total assigned milestone weight. A separate administrator-approved public progress field prevents private work from changing the public figure automatically.

**Manage manuscripts:** use the pipeline stages **Idea → Drafting → Internal review → Submitted → Under review → Revisions → Accepted → Published**. The board groups these stages for an overview. Private reviewer notes, submission references, internal deadlines and manuscript files stay out of the public feed even when a public title/status is approved.

**Manage collaborators and funders:** create the relationship or funder record and link it to a project. The site can publish acknowledgements and source evidence. Internal amounts, currency and notes remain private. The supplied historical collaboration reports were preserved without inventing current grant awards or active-project statuses.

**Review changes:** the activity log records actors, actions and timestamps. Each record has readable saved revision history. Concurrent edits use version checks; a stale form receives a conflict message rather than overwriting another person’s work. Records can be unpublished by choosing Private; this version preserves historical records rather than permanently deleting them through the UI.

## Accounts and permissions

| Role | Allowed actions |
|---|---|
| **Owner** | All content controls, publishing, uploads, account creation, roles, password resets and revocation. |
| **Administrator** | All content controls and publishing, but no account-management permissions. |
| **Researcher** | View assigned projects/profile; update assigned private manuscripts, milestones and research activity. No access to other researchers’ private work, publication approval or account roles. |

Only the owner sees **Accounts & permissions**. Create an account, select Researcher and link it to the correct profile. Share its initial password privately; the researcher can change it after signing in. Account changes and password resets revoke existing sessions. The last active owner cannot be disabled or demoted.

Researchers use `/workspace`, not `/admin`. For a biography change they submit a private update of type **Bio change**, which an administrator reviews. Published records are locked to administrators; researchers can propose new changes through private updates rather than silently altering approved public content.

## Connecting the existing GitHub page

The earlier V2 delivery recorded that the repository file matched Git object `e629357a55226376268d61ad1a9900ac8c13b69e` at its time of inspection. V3 does not claim a fresh repository comparison. This package was prepared for download; **no repository commit, deployment or server account was created**.

Deploy the Python application to your chosen persistent HTTPS server. Run `python manage.py configure-production` there and enter its real origin. Complete HTTPS/proxy/service setup and initialize the owner. Sign in to `/admin` and open **Publish & export**. Download the **Connected public page**, rename it `index.html`, and upload it to the existing repository, replacing the current public page.

Once connected, public saves appear on the next page load; no HTML editing is needed for each biography or project update. The public file sends no administrator credentials to the server and contains no private records. The API allows public reads from `https://mphill-lab-tracker.github.io`. If the public origin later changes, update `TED2_PUBLIC_ORIGINS` on the server.

Do not publish a connected page that points to `127.0.0.1`. That address refers to each visitor’s own computer, not your laboratory server. A local HTTP export is explicitly labelled in the admin screen.

For full deployment and backup instructions, see [docs/DEPLOYMENT-AND-SECURITY.md](docs/DEPLOYMENT-AND-SECURITY.md).

## Public snapshots versus live content

The supplied root `index.html` is a read-only **snapshot** with CSS, JavaScript, logos and public seed data embedded. It can be opened directly or hosted on GitHub Pages. It has no fake localStorage login and no embedded administrator secret. Staff access explains how to run the complete application.

The admin’s **Public snapshot** export includes only currently approved public fields. Approved local portraits and published achievement-certificate PDFs are embedded; remote photographs and other linked public PDFs remain dependent on their sources. A snapshot does not receive later changes and cannot be recalled after someone downloads it.

The admin’s **Connected public page** export contains the UI and the actual server origin, but no record data. It reads approved content at page load and displays an explicit connection error if the backend cannot be reached.

## Code organization

```text
index.html                 Compiled public snapshot for the existing repository
start.py                   Local setup and launcher
manage.py                  Initialize, serve, configure, build, reset, back up
requirements.txt           Tested direct Python dependencies
backend/
  app.py                   API, roles, uploads, exports and account operations
  schema.py                Shared editor fields and validation
  security.py              Argon2 passwords, server sessions, Origin/CSRF checks
  db.py                    SQLite storage, transactions and audit events
  public.py                Explicit public-field projection
  build.py                 Single-file public compiler
web/
  public.html              Public page template
  admin.html               Sign-in / private-workspace shell
  assets/                  Editable public and admin CSS / JavaScript
  images/                  Original extracted TED² and UNAM marks
data/seed.json             Verified public starting content; no private accounts
tests/                     Backend/security, offline UI and staging browser tests
docs/                      Evidence audit, deployment notes and testing report
```

Rebuild the root snapshot after editing the source public seed or design:

```bash
python manage.py build-public
```

For running content, use the admin forms and export controls instead of editing `seed.json` after initialization.

## Testing

```bash
python -m unittest discover -s tests -v
```

**66 backend/content/security regression tests passed.** The new source mappings, certificate access controls, alert-date validation and non-destructive content upgrade are checked alongside the existing permission and API regressions.

**73 in-memory Chromium rendering/interface checks passed.** These include offline delivery of all 11 supplied portraits, the certificate preview and byte-identical PDF download, homepage events, researcher links, mobile layouts, admin editing and publication approval. Real browser network navigation was blocked by this environment and is not reported as a passing live-origin test. See [docs/TESTING.md](docs/TESTING.md).

```bash
python -m pip install -r requirements-test.txt
python -m playwright install chromium
python tests/render_check.py
python tests/browser_check.py
```

The final command is the **live local-server browser test** for an unrestricted staging environment. It is included but could not run here because the managed browser blocks URL navigation. Do not confuse that unexecuted deployment check with the successful in-memory UI checks. Python/JavaScript syntax checks also passed. Full details are in [docs/TESTING.md](docs/TESTING.md).

## Boundaries

This is a functional small-laboratory implementation, not an independent security audit or institutional compliance approval. It does not provision hosting, domain names, email, SSO, two-factor authentication or malware scanning. Do not store patient-identifiable data without a separate institutional assessment. Clean dependency installation, Docker deployment, TLS behavior on a real domain and image reuse rights were not established by the local test run.

No fabricated project status, grant, manuscript stage or progress number is included. Empty research areas are deliberate: they become useful as the laboratory enters its real information.
