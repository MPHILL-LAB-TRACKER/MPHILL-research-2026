# V6.1 source basis and request coverage

## Existing project content

The release extends the delivered V6 PHP package and the repository source checked at main `b3ee191f18e6252c232392a16e89f8e7677d36e0`. At the read performed for this task, gh-pages was `c1b644ac7380f8f02ead49486affcc964300e595` and contained V6's separate public page folders. No live branch or Pages setting was changed by the build.

Original team names, corrected names, user-supplied portraits, publication records, research descriptions, notices and certificate are retained. Procurement lists are blank until an authorised user enters the real methodology and requirements. The supplied team presentation contains project topics, not an approved procurement specification or quantified protocol; no consumable quantities or experimental conditions were inferred from it.

## Primary external sources

- NHGRI, Polymerase Chain Reaction Fact Sheet: https://www.genome.gov/about-genomics/fact-sheets/Polymerase-Chain-Reaction-Fact-Sheet — supports the short draft fact that PCR copies a selected DNA segment. No experimental procedure is generated.
- EMBL-EBI, Europe PMC programmatic access: https://www.ebi.ac.uk/training/online/courses/embl-ebi-programmatically/europe-pmc-programmatically/ — supports use of the Articles REST API and the distinction between different research record types.
- EMBL-EBI, Analysing publications and funding with the Europe PMC REST API: https://www.ebi.ac.uk/training/events/analysing-publications-and-funding-europe-pmc-rest-api — primary explanation of publication metadata, query filtering and API use.
- Europe PMC, Preprints: https://europepmc.org/Preprints — source for the draft reminder that indexed preprints are not necessarily peer-reviewed results.
- Europe PMC, Open access subset: https://europepmc.org/downloads/openaccess — licence information for reuse of full articles. The application imports only selected metadata and links; it does not copy full-text articles.
- GitHub, HTTPS and Pages: https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https — explains HTTPS and potential mixed-content/DNS problems. This does not diagnose the user's carrier.
- GitHub, publishing source: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site — public deployment follows the selected branch/folder.

The source endpoints were not all reachable from the build environment. Live Europe PMC fetching and the user's mobile-data path remain unverified. Metadata fixtures exercise bounded retrieval, scheduling, errors, approval and deduplication without misrepresenting fixtures as real discoveries. Three draft facts are private and source-linked; the laboratory must review sources and wording before approving them.

Open availability is not a blanket reuse licence. Source attribution, article type, limitations, licences and any retraction/withdrawal notices must be checked when selecting a public scientific claim. No automatic summarisation of full articles is included.

## Complete feature map

| Request | Implementation and boundary |
|---|---|
| Wi-Fi and mobile data | Smaller display images, no required remote frontend library, no video preload, no-JS core content, low-data/connection pages, HTTP/private-host media export guard and diagnostic script. The actual carrier issue remains unconfirmed; no physical mobile-network test. |
| Admin portrait editing | Direct-upload save-state regression fixed; own/admin preview route; remove upload plus bundled fallback; crop/shape and approval. Roles enforced in PHP. |
| More themes and aligners | 14 palettes; 19 SVG motif choices plus None; independent header/footer; three sizes/contrast levels; all theme-coloured, including admin. |
| Methodology-aligned procurement | Methods/work packages, required method-step explanation, researcher ownership, optional project, available/ordered/needed/expired quantities, private notes/costs and admin-controlled public projection. No invented protocol. |
| Five-second notice board | Default 5; range 3–120; fade/slide/settle/none, three layouts, pause/manual controls and reduced-motion handling. |
| Better borders and structure | Six border styles, three content structures and three researcher-directory layouts. |
| Easier questionnaires | One-place question card builder, drag/up/down, type/help/required flags, transactional save; guided one-at-a-time or full forms. Public responses require public PHP hosting. |
| More useful tracking | Resource-readiness dashboard, private next actions, stock/condition/expiry warnings, overdue milestones and printable checklist. |
| Admin control | Existing record editor, private/public control, themes/logos, contacts/custom fields, media titles/captions/order, removal/Trash/restore, researcher grants and publish retained. Security/schema-required fields remain protected. |
| Did you know and discoveries | Private source-backed facts, opt-in scheduled metadata updates, researcher/general queries, DOI/source tombstones, human approval, expiry/review fields, public nonrepeat pool. No unattended publishing or invented claims. |
| Automated freshness | Local worker started/stopped with launcher; configurable interval/lookback; due checks/error backoff; no work while computer off and no live PHP on GitHub Pages. |
