# TED² Research Workspace V6.1

**PHP laboratory management, editable portraits, methodology-linked procurement, visual theme controls and reviewed research updates.**

This is the complete application and an in-place upgrade for the existing **V6** clone. It does not create another repository or replace the existing accounts, edited biographies, private research or uploads. The public GitHub website is generated from approved database content; it is not the administration server.

## Upgrade the existing installation

Save `TED2-Research-Workspace-v6.1.zip` in the existing **GitHub tracker** folder. Stop the current PHP server with **Ctrl+C**. Run as the normal `paul` user, not with sudo:

```bash
cd "$HOME/Documents/MPhill in biomedical sciences (medical microbiology)/GitHub tracker" &&
unzip "TED2-Research-Workspace-v6.1.zip" &&
bash "./TED2-Research-Workspace-v6.1/upgrade-v6.1.sh" \
  --target "$PWD/MPHILL-research-2026"
```

Review the source, target and database paths; type **UPGRADE**. A private source/configuration/database/upload backup is created outside the repository under `~/TED2-private-backups/v6.1-*`. Locally customised source files cause a stop, not silent replacement. Existing `.git`, `.env`, `.venv`, accounts, database content and uploaded files are retained. The migration only fills absent V6.1 fields and adds private starter facts. It does not replace an owner's existing theme colours, homepage section selection or profile edits.

After the upgrade succeeds:

```bash
cd "$HOME/Documents/MPhill in biomedical sciences (medical microbiology)/GitHub tracker/MPHILL-research-2026" &&
bash scripts/commit-v6.1.sh &&
git push origin main &&
bash start.sh
```

Type **COMMIT** when prompted. The helper explicitly stages the release's source paths, never `.env`, the database, uploads or private backups. It supports release files already staged from an interrupted commit, refuses unrelated staged work, and prints without the Git pager. It never force-pushes or switches branches. The source commit and the public website publication remain separate operations.

Open **http://127.0.0.1:8000/admin** and sign in with the existing account. Refresh with **Ctrl+Shift+R** once. The heading should show **V6.1**. Keep the server terminal running. This URL works only on the server computer; it is not a public mobile-data address.

Existing PHP 8.3+, SQLite, image-processing and FFmpeg dependencies remain applicable. A normal Ubuntu installation uses `php-cli php-sqlite3 php-gd php-mbstring ffmpeg`. The optional C++ worker remains available through `bash bin/build-native.sh`; it is not required with PDO SQLite installed and is not downloaded as a binary.

## Public website publication

In administration choose **Publish → Prepare preview → Open exact preview → approve the release → Confirm & push to GitHub**. Check the returned commit and deployment status. The existing authenticated admin session authorises the push; the application does not request the admin password again for each publication. An expired session requires sign-in again. GitHub authentication is separate and must already work for the operating-system account running PHP.

The PHP source belongs on **main**. Generated approved pages and media are pushed to **gh-pages** through an isolated Git index without changing the working branch or staged work. GitHub **Settings → Pages** must use **Deploy from a branch → gh-pages → / (root)**. Do not change the repository's default branch or merge gh-pages into main. A push is not proof of a finished deployment: use **Check status** and inspect GitHub Actions if it reports not-started, running or failure.

Changes made in administration appear locally after saving. They appear online only after a successful public publication and deployment. No database, unapproved upload, private procurement detail, questionnaire answer or login credential is part of that export. Previously downloaded files and older Git commits cannot be recalled by unpublishing.

## Portraits and researcher editing

The V6 defect was in the direct-file editor: it received the new upload ID, then reread the old hidden file value when saving. V6.1 saves the updated record snapshot instead. This also covers the direct logo, certificate and image fields that used that path.

Open **Researchers & collaborators → the person**. A portrait panel at the top supports **drag-and-drop or Browse**, immediately previews the attached local picture and provides **Remove portrait and bundled fallback**. Add the credit, set **Portrait permission → Approved**, and save when the picture is authorised for public use. Crop position can be centre, top or bottom; shape can be portrait, square or circle. A successful file upload is not permission to publish an unrelated photograph.

Owners and administrators can edit every researcher profile. A researcher account can edit only the assigned profile when the owner explicitly grants profile-editing permission. Private/public approval and account privileges remain protected server-side. The researcher-specific upload pickers continue to exclude other researchers' files; general laboratory images and videos remain in the laboratory gallery. The original supplied portraits, corrected names and laboratory materials are retained.

## Theme, layout and header/footer decoration

Open **Theme, logos & layout**. There are **14 palette presets**: Vintage, Modern, Clinical, Night, Botanical, Desert, Ocean, Lavender, Graphite, Copper, Ivory, Forest, Arctic and Heritage. Custom colours, heading/body fonts, width, spacing and corners remain editable. Save the selected palette to apply it to both public pages and administration.

The visual decoration gallery has **19 illustrated motifs plus None**: test tubes, glassware, microscopes, pipettes, DNA, molecules, cells, laboratory grid, leaves, fern, botanical plants, mountains, dunes, landscape, waves, savannah, geometric, vintage and modern. Choose Header or Footer, then select a motif. Each end has its own choice; size and contrast are adjustable. The vector outlines inherit theme colours, are bundled with the application and do not require a third-party image service.

There are six border choices: None, Fine line, Double line, Corners, Inset and Botanical. Public content structure can be Cards, Editorial or Compact; researcher directories can use Grid, List or Compact. Existing controls for logos, header/footer alignment, homepage section order, custom pages, captions, media order and visibility are retained. Required IDs, authentication rules and schema-critical fields cannot be removed through the editor; optional fields can be cleared/hidden and custom fields can be added/deleted.

## Notice board

The default rotation is **five seconds**. In the theme editor, open **Notice board & research facts** to set **3–120 seconds**, choose None/Fade/Slide/Settle and select Spotlight/Split/Stack layout. Existing on/off controls still apply. Prev/next/pause buttons are available; hovering, keyboard focus, a hidden tab or reduced-motion preferences pause rotation. All notices remain readable without JavaScript. No animation is required to reveal the main content.

The separate reviewed-science board has its own interval and maximum pool size. It avoids repeating a fact within the available pool in the same browser tab; after the pool is exhausted it can start a new cycle. This is not an unlimited supply of unique facts.

## Methodology, procurement and resource readiness

**Methodology & work packages** records a researcher, the actual protocol/version/section reference, a public summary, status and optional project. Detailed methodology notes and next actions are private. Do not enter unapproved clinical or patient information.

**Procurement lists** records each consumable, reagent, equipment item or service against a named researcher. Link the methodology when available and enter the actual method-step/reason for the requirement. A project is optional. Quantities accept decimals and explicit units. Record required, available and ordered quantities; condition; expiry; required-by date; order state and priority. Supplier, costs, storage and internal troubleshooting/next-action notes remain private.

**Resource readiness** shows usable stock, shortfall, quantity still to source, expiry/condition warnings, missing method linkage and overdue milestones. Only items with confirmed ready condition and non-expired recorded stock count as available. A print control provides a local checklist. These calculations use the entered numbers: they do not validate scientific suitability, infer a protocol or place orders.

A linked methodology must belong to the same researcher. Public procurement must not expose a private linked method; keep the item private, publish the approved method summary, or unlink and review the standalone public explanation. Admins control public visibility. Assigned researchers can work on their private records, not another researcher's list or public-approval flags. An admin can leave everything private for the researcher/management team or explicitly share selected requirements on the public resource page, researcher profile and optional homepage section.

No investigator-specific equipment or reagent list has been invented from a project title. Populate requirements from the actual authorised methodology. The supplied team slides do not establish quantities or procurement specifications.

## Easier questionnaires

Create the questionnaire, then choose **Open question builder**. Add question cards, edit wording/help/type/choices, mark required answers and reorder by dragging or up/down buttons. Save all questions together. Removed questions go to Trash; existing response snapshots retain their original question wording. Concurrent edits are rejected instead of overwriting another editor's changes.

The public form defaults to one question at a time with Back/Next, progress, validation and an editable thank-you message. A questionnaire can instead show all its questions. Choice/rating controls are touch-friendly. Questions-and-answers remain moderated. No name or email is requested in anonymous responses; free text and hosting logs can still identify someone, so the system does not promise absolute network anonymity.

Receiving responses from internet visitors requires a publicly hosted PHP application and a configured **Public submission site**. GitHub Pages cannot execute PHP or store form submissions. A static export without a configured public endpoint clearly says that online submissions are not connected; it does not pretend to send them. The local guided form works while the local PHP server runs.

## Did you know? and automated research review

Three source-backed starter facts are included as **private, unapproved** drafts. Review their primary sources, edit the wording and set approval/public visibility before sharing them. Facts can have review and expiry dates, a researcher, homepage visibility and a source link. Enable the **Facts** homepage block deliberately; migration does not alter an owner's existing homepage block selection.

**Discovery automation** controls general laboratory discovery checks. Individual researcher profiles retain their topic query and opt-in. The default check interval is 24 hours, configurable from 1 to 168 hours, with a configurable 1–365-day lookback. Keep queries specific to the laboratory's real work. Each watch retrieves at most 50 source matches per check; this is a bounded alert feed, not an exhaustive literature review.

`bash start.sh` now runs a separate lightweight metadata worker alongside the local PHP server. It only checks explicitly enabled watches. It stops when the launcher stops; nothing installs a global cron job or runs on the laptop while it is off. Production PHP-FPM hosting must schedule `php bin/console.php literature-sync` or run the worker under a service manager. The worker has a lock, due-time checks, an error backoff and a status panel. A failed source request records an error and does not fabricate results.

Europe PMC provides the research metadata. New items enter the **private literature-review queue**, with title, author/journal/date when supplied, source URL and evidence caveat. DOI/source identities are retained after deletion, preventing reimport of the same item. Cross-profile matches may be kept for each researcher; the public science board deduplicates them. A human must read the source, distinguish a preprint from a peer-reviewed result, write/approve the summary, choose public/homepage visibility and publish the website. The scheduled job does not silently rewrite public scientific claims, fetch full articles or auto-push to GitHub. No email or browser-push service is configured.

## Mobile data and network troubleshooting

The published website has no Wi-Fi-only rule. V6.1 improves the site-controlled parts: smaller locally generated display images; lazy image loading; click-to-play videos with `preload="none"`; server-rendered content; no mandatory external fonts/scripts; responsive layouts; a dependency-free **Low-data view**; and a tiny **Connection check** page. Publication rejects automatically loaded media addresses using HTTP, localhost or private network addresses. Optional external HTTPS image references can still depend on their source host; locally upload critical images.

**The reported mobile-carrier failure has not been reproduced or diagnosed.** A website change cannot repair a carrier route, DNS resolver, TLS interception or device certificate problem. No physical Android/iPhone/mobile-data test was performed in the build environment. Do not disable TLS verification, clear data or change DNS blindly.

After publishing V6.1, open these on the affected phone with Wi-Fi switched off:

- `https://mphill-lab-tracker.github.io/MPHILL-research-2026/connection-check/`
- `https://mphill-lab-tracker.github.io/MPHILL-research-2026/light/`

If the tiny page loads but the full page does not, capture the full-page browser error and test the low-data view. If neither page loads on mobile data but both work on Wi-Fi, record the carrier, browser/OS and exact error. A 404 means the new route is not published; check the deployed commit/version first.

A read-only comparison script is included:

```bash
bash scripts/diagnose-connectivity.sh
```

Run it on normal Wi-Fi, then on the computer connected to the phone's mobile-data hotspot. It checks DNS, verified HTTPS, IPv4/IPv6 and public route responses without changing network settings. IPv6 failure alone is not a website failure when IPv4 works. The exact outputs are needed before claiming the carrier problem is fixed.

## Reference material and delivery limits

Primary information sources and feature coverage are listed in [Sources and requirements](docs/SOURCES-AND-COVERAGE.md). See [Upgrade and recovery](docs/UPGRADE-RECOVERY.md), [Deployment](deploy/README.md) and [Testing](docs/TESTING.md).

The application is delivered as source code. It has not been installed on the user's computer, pushed to the live repository or load-tested in production. The complete source ZIP and manifest contain no user database, passwords, environment secrets, native executable or private uploads. A deployable public site is generated from the user's actual approved database rather than a demonstration database.
