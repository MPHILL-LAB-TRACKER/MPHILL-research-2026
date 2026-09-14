# Administration and publishing

## Navigation

The sidebar is grouped into **Workspace**, **Website**, **Research intelligence**, **Questions & feedback** and **Administration**. Groups collapse; searching opens matching groups. Public navigation separates primary researcher/research/publication pages from secondary laboratory and discovery links. Menu controls work on narrow screens; Escape closes open secondary menus.

## Appearance

Open **Website → Theme, logos & layout**. Choose the header or footer in the photographic picker, select an installed image, then save. New photographic decoration replaces line-art rendering; the older motif fields are kept only as recovery data. Images are illustrative, not proof of a discovery or institutional partnership.

Five photographs are bundled. Two additional openly licensed glassware/fern choices have source-verified download buttons. Downloads require internet access, use HTTPS and check a fixed source checksum before saving. A failed download never replaces the current selection. Imported images are packaged with the next public release; public visitors do not depend on Wikimedia servers. Custom header/footer photos use the image upload fields and approval checkbox. Captions and credits are editable.

Light, dark and system appearance share the saved theme palette. Visitors may choose a mode when the administrator enables the switch. The choice contains no credentials and is stored locally in that browser. Disabling the switch enforces the administrator's selected default. Dark palette fields are independent of the light palette. Fourteen existing presets, borders, layouts, logo replacements and homepage ordering remain available.

## Research management

All previous researcher-owned profile, media, contact, milestone, methodology and procurement controls remain. Administrators may edit every researcher; researcher accounts require explicitly assigned editing rights and may not edit other researchers' private work. Project links are optional for independent milestones. Procurement requirements remain tied to the documented method and responsible researcher; the application does not invent experimental quantities.

Files remain separate from their display titles and captions. Upload approval, record visibility and researcher ownership are separate checks. Removing public content requires a new publication. Trash, restore and password-confirmed permanent deletion are unchanged.

## Research pulse and quotations

Use **Research intelligence → Research pulse & automation** for an overview. Configure public topics and sources under **Homepage & contact**. Topic terms are public when exported; never enter confidential hypotheses there. Private researcher literature queries remain in the separate **Private literature checks** feature.

`Review` policy places incoming headlines in a private queue. `Source-headlines` policy may expose source title, date, author attribution and link automatically, with an explicit unreviewed-headline label. Source failures preserve dated items; a failed check does not become a successful fresh update. Administrators can edit, hide or delete local headline records. Deletions create deduplication tombstones to avoid re-importing the same item.

Quotes require explicit approval, source/rights information and public visibility. Two short historical excerpts and four original editorial reflections are included privately. Original reflections are not attributed to a historical scientist. Approved quotes rotate, can pause or step manually, carry tags and can be shuffled without repeating an item before completing the pool. Rotation pauses during focus/hover, when the page is hidden, and for reduced-motion preferences.

The `pulse` and `quotes` homepage blocks are independent of the original facts block. Move them through **Sections & navigation → Homepage blocks** or disable their display switches. Other existing notice-board controls remain available.

## Fast loading without stale private pages

A local public-render cache uses a content/code fingerprint and administrator-set lifetime. Changes to public records invalidate the key immediately. Clear it through **Administration → Performance & cache**. Private/API/form routes return `no-store` and never enter that rendering cache.

Local HTTP responses use ETags. Content-hashed media and versioned styles/scripts can receive immutable cache headers. Unversioned resources revalidate. A public-only service worker is generated for GitHub Pages: it stores only versioned CSS/JavaScript and content-hashed JPEG/PNG/WebP images, capped by entry count and one MiB per file. It never caches HTML, API responses, admin pages, questionnaires, PDFs or videos. Each release has its own site-specific cache name; old caches are cleared when the new worker activates. Disabling asset caching takes effect after publication and a subsequent online visit. Existing downloads/Git history cannot be recalled.

## Publish and verify

Prepare an exact preview, review it and confirm publication using the logged-in owner/admin session. The publisher pushes public files to `gh-pages` without switching your working branch or staging private files. A Git push and a Pages deployment are separate events; check both in the publishing screen. Pages should use `gh-pages` and `/ (root)`.

Do not force-push or change the default source branch to solve a display mismatch. Compare the published commit and deployment first. Automatic source headlines are a separately labelled public stream; they do not silently publish private laboratory changes.
