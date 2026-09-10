<p align="center">
  <img src="assets/images/ted2-wordmark.png" alt="Tissue Engineering & Drug Development Laboratory" width="560">
</p>

<h1 align="center">TED² Laboratory</h1>
<p align="center"><strong>Tissue Engineering &amp; Drug Development · University of Namibia</strong><br>A source-grounded research website, built with HTML, CSS and JavaScript.</p>

<p align="center">
  <a href="#publish-in-your-existing-repository">Publish</a> ·
  <a href="#preview-locally">Preview</a> ·
  <a href="#edit-the-website">Edit</a> ·
  <a href="#research-content-and-verification">Research sources</a> ·
  <a href="#photographs-and-logos">Images</a>
</p>

---

## About this repository

This learning project presents the Tissue Engineering & Drug Development Laboratory through a restrained cream-and-forest-green design informed by the supplied laboratory logo and [Strikingly reference website](https://auburn-mint-phnps5.mystrikingly.com/4).

The homepage contains **all 12 research descriptions** from the supplied Tissue Engineering document. It introduces the people by name, but **their work and publications appear on separate profile pages**, not on the homepage. Collaborators and laboratory-reported projects also have individual pages.

The repository includes a **prebuilt website** and the small, dependency-free generator that produced it. Nothing needs compiling or installing merely to open or publish the website.

**Included:** 20 static pages · 11 individual profiles · 3 collaboration pages · 5 selected research records · 1 compiled single-file edition.

## Choose an edition

| Edition | Open this file | Best use |
| :-- | :-- | :-- |
| **Multi-page website** | `index.html` | Learning, normal repository maintenance and accessible static hosting. Keep the accompanying folders. |
| **Compiled single file** | `TED2-single-file.html` | A portable website in one HTML file. Layout, scripts, logos and all views are embedded. Internal navigation requires JavaScript. |

Both editions initially use the original online photograph URLs. Logos and the public-site QR code are included locally. **Neither edition is fully offline with photographs until the optional image-caching command has succeeded.**

The multi-page edition exposes readable page content and working profile links without JavaScript. Search, mobile-menu enhancement and citation copying use JavaScript. The single-file edition uses `#/...` routes; it is not necessary to set up server rewrite rules.

## Publish in your existing repository

You do **not** need another repository.

1. Extract the package. Upload its **contents**, including the folders, into your existing repository. Place `index.html` at the repository root, not inside an extra enclosing folder. Keep your existing repository history and review files before replacing any of your own work.
2. Commit the uploaded files to the branch you use for the website. The generated HTML is already included; there is no dependency installation or build step on GitHub.
3. Open **Settings → Pages**. Under **Build and deployment**, choose **Deploy from a branch**. Select the branch containing these files, choose **`/ (root)`**, and save.
4. Use the published address shown by GitHub Pages after deployment completes. No particular repository name, account name or custom domain is hardcoded into this project.

The `.nojekyll` file is included. All internal asset and page paths are relative, so the site can live under a repository subdirectory as well as a custom-domain root.

For a one-file deployment instead, upload `TED2-single-file.html` under the name **`index.html`**. Its internal views, styles, scripts and logos are embedded; the remote-photo limitation still applies. Do not replace the multi-page source `index.html` with this edition when continuing to maintain and rebuild the full project.

Official instructions: [GitHub — configuring a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

## Preview locally

**No tools required:** open `index.html` in a browser while keeping the extracted directory intact. Alternatively, open `TED2-single-file.html`.

For a localhost preview, run the following from the repository folder with **Node.js 22 or later**:

```bash
npm start
```

Open `http://127.0.0.1:8080`. Stop the preview with `Ctrl+C`.

A different port is supported:

```bash
node scripts/serve.mjs 8090
```

There are **no npm packages to install**. The preview server binds to localhost, serves only files inside the project directory, refuses dotfiles and does not provide a public production server.

## Website structure

```text
.
├── index.html                  Homepage: all supplied research content
├── researchers.html            Searchable researcher directory
├── collaborators.html          Collaborators and lab-reported projects
├── publications.html           Searchable, filterable research records
├── sources.html                Sources, verification notes and image credits
├── 404.html                    Static not-found page
├── TED2-single-file.html        Compiled portable edition
├── profiles/                   Nine researchers + two collaborators
├── projects/                   Three source-linked collaboration pages
├── assets/
│   ├── css/styles.css          Colours, typography, layout and responsive rules
│   ├── js/site.js              Menus, search, filtering and citation copying
│   └── images/                 Extracted logos and public-site QR code
├── data/
│   ├── site.json               Editable content and source-of-truth records
│   ├── publications.bib        Generated bibliography export
│   └── build-manifest.json     Generated page and photo-cache inventory
├── scripts/
│   ├── build.mjs               Builds both editions using Node alone
│   ├── serve.mjs               Local preview server
│   ├── validate.mjs            Data, path, anchor and content-integrity checks
│   ├── download-images.mjs     Optional caching of the reference photographs
│   └── test-server.mjs         Local HTTP server smoke tests
├── docs/
│   ├── CONTENT-AUDIT.md        Research verification decisions and gaps
│   ├── IMAGE-CREDITS.md        Image origins and caching instructions
│   └── TESTING.md              Test commands, results and limitations
├── .nojekyll
├── .gitignore
└── package.json
```

## Edit the website

### Content

Edit **`data/site.json`**. The collections correspond directly to the site:

| Collection | What it controls |
| :-- | :-- |
| `research` | The complete homepage descriptions and section anchors. |
| `people` | Supplied names, roles, topics, documented activities, links and profile notes. |
| `publications` | Titles, authors, year, record type, DOI, linked researchers and verification notes. |
| `projects` | Collaboration pages, source-backed membership and provenance. |
| `sources` | The source directory and each source’s evidential limits. |
| `images` | Exact reference-photo addresses, local cache names, alternative text and credits. |

After saving changes, regenerate both editions and check the result:

```bash
npm run build
npm test
```

Equivalent one-command check:

```bash
npm run check
```

**Generated files are not the editing source.** Direct changes to `index.html`, profile pages, bibliography export or the single-file edition are overwritten by the next build. Edit the JSON for content, the CSS/JavaScript for presentation and behaviour, or `scripts/build.mjs` for the HTML templates.

### Design

The beginning of **`assets/css/styles.css`** defines the colour and typography variables. The design uses system fonts and Georgia; there are no external font downloads, paid libraries or font files to distribute.

### New people and papers

Follow the structure of an existing record. Every person needs a unique `id`; publication `people` entries refer to those IDs. Every research output or collaboration needs a real `sourceId`. The builder generates the appropriate profile and collaboration pages automatically.

Preserve the distinction between `peer-reviewed`, `author-listed` and `catalogued` records. Do not assign a DOI, academic identifier, paper, affiliation or portrait from a name resemblance alone.

The validator intentionally checks the original baseline roster and research-topic counts. When deliberately expanding that baseline, update those explicit count assertions in `scripts/validate.mjs` as part of the same reviewed change.

## Research content and verification

**Source review date: 10 September 2026.** This is a reviewed snapshot, not a live publication aggregator.

The included bibliography contains **three publisher-checked journal articles associated with Prof Davis Mumbengegwi**. It also contains **two differently qualified university research records associated with Dr Albertina Shatri**: one found through an indexed author profile and one through a bibliographic catalog. Those university records are not presented as verified journal articles.

The laboratory report on the May 2025 nanoendodontic informed-consent event supports the documented activity for Dr Albertina Shatri and Dr Silas Bere. Laboratory-reported collaborations are clearly labelled; an article’s coauthors are not automatically promoted to formal institutional partners.

For other members, the profile states that a confidently attributable public record was not confirmed. This **does not mean that the person has no work or publications**.

There is one unresolved name/title discrepancy: the supplied roster says **“Dr Manelia Halweendo”**, while a laboratory report says **“Ms Melania Halweendo”**. The website retains the supplied roster entry and does not silently attach the report’s activities to it.

See [the complete content audit](docs/CONTENT-AUDIT.md) and the website’s `sources.html`. Bibliographic records are selected works by listed researchers, **not necessarily TED² laboratory outputs or a complete career bibliography**.

## Photographs and logos

The supplied Word document provided the TED² wordmark, laboratory icon and UNAM logo. They have been extracted and included. The original uncropped logo is retained at `assets/images/ted2-logo-original.png`.

Four reference photographs are connected using their actual Strikingly CDN addresses. **The delivery environment could inspect those images through web retrieval but could not download their binary files into the package.** As shipped, those four images therefore load online. A deliberate branded fallback is shown when a photograph cannot load; the page content remains readable.

After confirming permission to reuse the photographs, cache them on a network-connected machine:

```bash
npm run images
```

The script downloads the original photographs with a fixed PNG/JPEG output format, checks the returned type and size, saves each successful download atomically, and rebuilds **both** editions. If a download fails, an existing cached copy is preserved and the affected uncached image keeps its original URL. Failure exits with a nonzero status and a visible explanation.

After a successful cache, commit the new photographs and regenerated pages. No API key, npm package or image-generation service is needed. There is no guarantee that third-party image hosts will remain available indefinitely.

The QR code points to the **public original laboratory website**, not the private Strikingly editor link from the supplied document. It does not claim to encode your as-yet-unspecified GitHub Pages address.

Full attribution and ownership notes: [Image credits](docs/IMAGE-CREDITS.md).

## Accessibility and privacy

The implementation includes semantic headings, visible keyboard focus, a skip link, mobile navigation, Escape-to-close behaviour, labelled search/filter fields, readable no-results states, reduced-motion support and printable content. Initials replace missing portraits. These measures are not a claim of formal WCAG certification.

There is no analytics script, tracking pixel, contact-data database or fake form submission. The contact action opens the user’s email application. Remote photographs still cause requests to their third-party hosts; caching them locally removes that image-host dependency.

## Testing

```bash
npm run check
```

Checks include the baseline roster, complete homepage text, profile generation, bibliography source links, local file paths, anchors, duplicate HTML IDs, image alternative text, unsafe external-tab links and accidental reintroduction of the old template placeholders. The script does not imply that every external URL is live or that every scientific claim is independently validated.

See [Testing](docs/TESTING.md) for the delivered test report and browser-rendering limitations.

## Ownership and publication approval

This repository is an educational implementation based on supplied laboratory materials and public sources. It is not presented as independent proof of institutional approval. University marks, source photographs, publication material and supplied research text retain their respective ownership. No licence for third-party assets is granted by their presence in this repository.

Confirm institutional branding, member names and the right to publish images before presenting this as an official laboratory website. No licence has been added to replace or override the existing repository’s licensing decisions.
