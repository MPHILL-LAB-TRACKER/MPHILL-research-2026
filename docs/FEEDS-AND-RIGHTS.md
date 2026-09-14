# Research feed, quotation and image rights

## Providers and editorial policy

The reading desk has two allowlisted adapters: **Europe PMC** research/preprint metadata and **The PLOS Blog** science-publishing/innovation headlines. It does not accept arbitrary feed URLs, copy article bodies, reuse third-party article images or generate claims about clinical effectiveness. A bibliographic entry is not a verified discovery. Preprints and blog perspectives have distinct labels.

Public topic filters select relevant records; date windows remove older automatic records. Source IDs, DOI and normalised titles are used for deduplication. Local deletion history prevents re-import. A source outage is recorded with the last successful check, not replaced by invented results. Blog title/abstract searches are limited by the provider's returned page; this is a curated reading feed, not an exhaustive systematic review.

Official background:
- https://europepmc.org/RestfulWebService
- https://www.ebi.ac.uk/europepmc/webservices/rest/search
- https://plos.org/blogs/about/
- https://plos.org/terms-of-use/

## Delivery choices

**Local**: enabled checks run while `bash start.sh` is running. Publication through the normal admin workflow is still needed to update a static snapshot. For an always-on PHP deployment, the public reading stream can reflect the server's enabled local checks without a new static export.

**GitHub-scheduled**: commit the supplied `.github/workflows/science-pulse.yml` to the default branch, allow Actions, set the public reading policy to `source-headlines`, select `github-scheduled`, and publish V6.2 once. The export includes `science-config.json` containing only public topic/policy settings. The scheduled worker reads that file from `gh-pages` and writes metadata alone to a separate `science-feed` branch. Public pages fetch `feed.json` directly, so no Python/PHP backend or laptop uptime is required for that stream. A digest prevents a feed for an older policy from being accepted after a changed policy is published.

The workflow requests a run every six hours at minute 23. Requested application intervals shorter than six hours do not make this workflow run more often. GitHub may delay a schedule, disable inactive-repository schedules or restrict Actions through organisation policy. The workflow can also be run manually in Actions. It does not trigger another Pages build, publish the local database or update lab achievements.

For **item-by-item public moderation**, use local/review mode. In cloud source-headline mode, source/topic/date controls are the moderation boundary; deleting a local headline does not remove the independently maintained cloud feed. Disable a source, narrow a topic or return to review mode and republish to change that boundary. This distinction is visible in the reading-desk policy description.

Sources: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule

## Quotation collection

Historical excerpts are intentionally short and point to original texts:
- Charles Darwin, *On the Origin of Species*, concluding paragraph: https://www.gutenberg.org/files/1228/1228-h/1228-h.htm
- Michael Faraday, *Experimental Researches in Electricity*, 1839 preface: https://www.gutenberg.org/files/14986/14986-h/14986-h.htm

The remaining four seed items are original editorial reflections, clearly labelled as such and offered under CC0. No quotation is automatically attributed from a generic quote API. All seed quotations begin private. Administrators may add reviewed source-backed quotations; published changes enter the next rotation pool. The software rotates approved quotes—it does not promise to find a new historical quotation every day.

## Photographic assets

Exact attribution, source, licence and modifications are in `data/photography.json` and the public Sources page.

Bundled assets:
- Laboratory bench: previously supplied by the site owner. **Not an openly licensed stock photograph.** Retained under the owner's instruction; obtain any participant/photographer permissions needed before external reuse.
- Retinal photograph: Mikael Häggström, CC0, distributed in scikit-image.
- Hubble deep field: NASA/ESA credit, public-domain statement in the scikit-image source documentation.
- Launch photograph: SpaceX, public-domain/CC0 statement in scikit-image documentation.
- Botanical macro: scikit-learn sample image, CC BY 2.0. The exact upstream attribution notice is copied into `data/photography/SCIKIT-LEARN-IMAGE-CREDITS.txt`; it credits danielbuechele and links the Flickr account vultilion. That upstream attribution is reproduced rather than silently resolving the discrepancy.

Optional source-verified imports:
- Vintage laboratory glassware — LukaszKatlewa, CC BY 4.0: https://commons.wikimedia.org/wiki/File:Vintage_laboratory_glassware.jpg
- Fern leaves — Antilived, CC BY-SA 3.0: https://commons.wikimedia.org/wiki/File:Fern_leaves.jpg

Imported/resized CC BY-SA image derivatives remain under the same share-alike image licence; this does not relicense unrelated application code. Cropping/resizing/recompression is disclosed. Optional imports were not downloaded in the build environment; they are not falsely presented as bundled files. Every installed image is served locally once selected, not hotlinked to its provider.

Other official source: https://scikit-image.org/docs/stable/api/skimage.data.html

## Caching references

- https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control
- https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers

Cache improvements are not a fix for unresolved mobile-network DNS, TLS or routing problems. Physical cellular connectivity and production load must be tested independently.
