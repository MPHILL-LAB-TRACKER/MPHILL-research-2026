# Sources, inspirations and request coverage

## Technical primary sources checked for V7

- Overleaf developer interface: https://www.overleaf.com/devs — ZIP data-URI POST hand-off. No unofficial password integration, iframe assumption or synchronization claim.
- Cloudflare D1: https://developers.cloudflare.com/d1/get-started/ — optional persistent response database. Wrangler reference: https://developers.cloudflare.com/workers/wrangler/commands/d1/ .
- GitHub Pages: https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages — generated static-site hosting, separate from visitor-response processing.
- eLabFTW: https://github.com/elabftw/elabftw — reviewed as a laboratory-notebook design reference: separate experiments, metadata, ownership and publication decisions. **No source code copied.** Its licence remains its own.
- SciNote: https://github.com/scinote-eln/scinote-web — reviewed for the distinction between structured working records, researcher responsibilities and inventory/workflow organisation. **No source code copied or endorsement claimed.**

The new Worker, response-key flow, authoring helpers and V7 interface are original implementations extending the existing application; they are not eLabFTW/SciNote installations. The resource shelf is curated outbound linking, not bundled third-party web apps.

## Request coverage

| Request | Implementation / boundary |
|---|---|
| Any visitor can respond | Same-host PHP responses; optional independently hosted Worker/D1 for static GitHub Pages. Deploy/connect once. |
| Read replies directly | Private response-key lookup without visitor accounts; administrator approval and visitor consent for shared conversations. |
| More varied daily quotes | 32 original CC0 science reflections, topics, daily ordering, shuffle and pause; existing historical records preserved. |
| LaTeX / Overleaf | Private researcher-owned source editor, three templates, import, actual ZIP and explicit official one-way hand-off. No unsafe local TeX execution. |
| Close expired notices | Laboratory timezone, inclusive end/override dates, manual closure/cancellation, client refresh and historical activity archive. |
| Researcher gallery folders | General and per-researcher collection routes plus owner-matched named albums. Private albums suppress anonymous file access/export. |
| Fresh public and admin appearance | Biomedical editorial composition, 4 compositions/18 palettes, preserved photo bands, responsive dark/light UI and reorganised research desk. |
| Interesting research tools | Structured private bench notes, reproducibility reminders, manuscript stage/next-action fields and 9 editable open-science resource links. |
| Preserve tracking | Existing methodology/procurement, uploads, biographies, milestone/project controls, permission gates, publication flow and caches retained. |

## Content rights

Owner-supplied laboratory text, branding, named portraits and certificate remain unchanged; inclusion is not an open licence or a new authentication of their claims. The previously corrected **Ms Jaydine Feris** name is retained even though the earlier slide had a typo. Public references remain attached to existing publications and notices.

The 32 new reflections are original editorial writing offered under CC0-1.0. They are explicitly not quotations from Faraday, Curie or other named scientists. The old primary-source quotation records retain their own evidence labels and approval states. Literature, preprints and blog perspectives remain distinct; no feed title is promoted into a verified clinical discovery without review.

Photographic assets and optional downloads retain the credits in `data/photography.json`, Sources and `docs/FEEDS-AND-RIGHTS.md`. No new stock photographs, faces or scientific images were generated or silently copied for V7. No font files are distributed. Each external resource retains its own terms and licence; public access does not imply unrestricted reuse.
