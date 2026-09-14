# V6.2 request coverage

| Requested change | Implementation | Relevant boundary |
|---|---|---|
| Actual images instead of simple drawings | Independently selected photographic header/footer bands, local image packaging, custom uploads, tint/height/depth controls and credits | Five bundled photos; two optional internet imports. The owner-supplied laboratory photo is not an open-licensed stock asset. No claim of an interactive 3D model. |
| Dark mode and better visuals | Shared light/dark/system mode, separate dark palette, administrator lock or visitor switch, refined spacing, cards, borders and restrained motion | Fourteen existing presets remain. Colour preferences contain no account information. |
| Better navigation | Five collapsible, searchable administration groups; grouped/flat public menu options and mobile controls | Editing/publishing permissions remain enforced server-side. |
| Automatic research/blog updates and hashtags | Europe PMC/PLOS adapters, dated metadata cards, source/type labels, topic filters, duplicate prevention, local review and opt-in GitHub-scheduled source-headline delivery | Not live breaking-news coverage or a systematic review. No paper bodies, third-party article images or generated research claims copied. |
| Informative/motivational quotations | Two short primary-source excerpts plus four clearly labelled original editorial reflections, all private until approved; administrator-editable attribution, rights and tags; shuffle/rotation/pause | No unreliable random-quote attribution API and no promise of new historical quotations on every refresh. |
| Faster caching | Content/code-fingerprinted local public-render cache; ETags; content-hashed assets; bounded public asset-only Service Worker; administration clear/disable controls | Never caches private API/account pages, forms, HTML, PDFs or video in CacheStorage. Does not solve unverified DNS/carrier/TLS failures. |
| All changes under administration | Appearance, source policy/topics, feed display, quotation approval, cache settings and old laboratory editors | Scheduled source-headlines are authorised by source policy rather than item-by-item review. Use review/local mode for individual approval. |
| Short public README | Project overview and minimal startup, links to dedicated setup/upgrade/operations/rights/testing documents | No personal home-directory commands. Installer asks for the chosen existing clone path. |
| Existing functionality retained | Researcher-owned media, portrait editing, contact/custom fields, projects, independent milestones, method-linked procurement, resource readiness, achievements, questionnaires, Trash, permissions and reviewed publication | New theme/feed functions do not broaden researcher access to other researchers' private records. |

## Primary documentation

Photographic registry with exact credits/licences: `data/photography.json`; upstream botanical notice: `data/photography/SCIKIT-LEARN-IMAGE-CREDITS.txt`.

- https://scikit-image.org/docs/stable/api/skimage.data.html
- https://commons.wikimedia.org/wiki/File:Vintage_laboratory_glassware.jpg
- https://commons.wikimedia.org/wiki/File:Fern_leaves.jpg
- https://europepmc.org/RestfulWebService
- https://plos.org/blogs/about/
- https://plos.org/terms-of-use/
- https://www.gutenberg.org/files/1228/1228-h/1228-h.htm
- https://www.gutenberg.org/files/14986/14986-h/14986-h.htm
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control
- https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows

See [Research feeds and rights](FEEDS-AND-RIGHTS.md) for source-policy, scheduling and image-import limits, and [Verification](TESTING.md) for the executed test scope. Existing researcher and laboratory evidence is retained from the previous release; this upgrade does not add unsupported academic credentials, grants, publication claims or research results.
