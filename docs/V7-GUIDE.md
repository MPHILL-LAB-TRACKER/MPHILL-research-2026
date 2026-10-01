# The V7 research studio

## A focused administration structure

**Research desk** contains the writing workspace, private notebook, researcher profiles, methodology/procurement, independent milestones, projects and publications. **Website studio** contains media, researcher collections, design and page editing. **Research intelligence** contains source-reviewed feeds and quotations. **Conversations** contains the visitor inbox, Q&A and questionnaires. Account and publication controls remain role restricted. Use the sidebar search to locate a section.

## Visitor conversations

Open **Visitor inbox**. With no gateway configured, same-host PHP visitors can submit a message; the application stores it privately. Deploy and connect the optional gateway to accept visitors while the local machine is off. The published form accepts a nickname or no name and an optional researcher selection. It returns a secret response key, which the visitor saves and later enters into **Check a reply**. Losing that key cannot be remedied by revealing the message to an unverified stranger.

An administrator can answer privately, close or delete the message. Sharing the visitor message and reply publicly requires the visitor's explicit consent plus administrator approval. Researchers do not automatically see the private response inbox. This is asynchronous correspondence, not live chat, email forwarding or medical advice. Do not submit patient identifiers or confidential scientific results.

Messages remain in the selected service, never in public Git commits. The local and cloud inboxes are separate; connecting a gateway does not migrate old local messages. Disabling visitor responses requires synchronizing a connected gateway as well as updating/publishing settings. The connection panel offers **Synchronize public researcher options**, which sends the enabled flag and approved researcher labels. Latest 200 messages are shown in the management inbox; delete resolved items according to retention policy before the 5,000-message capacity limit.

## Writing and private notebook

See [Writing](WRITING.md). Notebook records separate question, method, observation, interpretation and next action. Checkboxes prompt checks of sample traceability, controls, units and raw-data links; they do not certify an experiment. A note cannot become public directly. Create an approved public research update when appropriate. Methodology/procurement and milestones remain available without mandatory project creation.

## Researcher folders and albums

The public Gallery begins with **General laboratory** and alphabetically ordered researcher folders (respecting configured priorities). Create a named album with either a researcher owner or general-laboratory scope. A file's owner must match the album. Move a file by editing its album selection; uploading into an album assigns its scope. Titles, captions, alternate text and display filenames remain independent of stored secure filenames.

Both the file and its parent album must be public/approved for public export. A private, missing or trashed album hides its files from anonymous visitors, even if the file was approved earlier. The owning researcher and authorized administrators retain private access. Changing an album owner is blocked until its contents are deliberately reconciled. The upgrade does not move existing files between researchers.

## Current notice board and historical record

Announcements can be **Automatic**, **Closed** or **Cancelled**. Automatic notices expire after `expires_on`, otherwise `end_date`, otherwise `start_date`, in the configured laboratory time zone. An undated notice stays open until closed. End dates are inclusive. Closing or expiration removes a notice from the rotating homepage; it does not delete the archived activity or certify attendance.

PHP excludes expired items during render/build. Browser enhancements re-check the static snapshot on load, rotation and periodically, so an old approved release does not keep advertising an expired conference. With JavaScript unavailable, the text represents the last published snapshot until it is rebuilt. Private date changes require publishing again. Five-second notice rotation, effect, pause and reduced-motion preferences are preserved.

## Quotations and resources

V7 adds **32 distinct original science reflections**, labelled original and offered under CC0. They are not attributed to historic scientists. Existing source-checked historical quotations remain available. Use Science quotations to add, approve, hide or edit items and topic tags. Theme controls select the original library, topic filter and daily ordering. The existing random rotation avoids repeating an item until cycling through its pool. Fewer than two approved matching items cannot provide variety.

The open-science shelf links to literature, reporting guidance, writing, analysis and data resources. These are external services with their own licences and terms, not bundled installations or institutional endorsements. Administrators control all links and homepage inclusion. Scheduled research feeds are retained with their existing approval/publishing policies.

## Biomedical presentation

Four compositions—**Biomedical**, **Journal**, **Atlas** and **Minimal**—alter page structure, hierarchy and treatments without erasing edited colours or branding. Four additional palettes bring the preset total to eighteen. Photographic headers/footers, custom logos, existing decorations, light/dark/system modes and gallery layout options are preserved. The public site uses server-rendered content and progressively enhanced controls rather than a loading screen that depends entirely on JavaScript.

Public caching remains bounded and excludes accounts, messages, questionnaires, authoring source, PDFs and videos. A network/carrier failure is not automatically solved by a new theme; the existing low-data and connection-check tools remain available.
