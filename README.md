# The Steven Schrembeck Archive

A shared home for Steven’s writing, podcasts, audio fiction, videos, presentations, and the people who remember him.

- [Archive website](https://steven-schrembeck-archive.opzero.sh/)
- [GitHub Pages copy](https://jcameronjeff.github.io/steven-schrembeck-memorial/)
- [Complete collection download](https://steven-schrembeck-archive.opzero.sh/downloads/steven-schrembeck-complete.zip)
- [GitHub release downloads](https://github.com/jcameronjeff/steven-schrembeck-memorial/releases)
- [Jeff Cameron’s original remembrance](https://remembering-steven-schrembeck.opzero.sh/) — a separate personal post, linked from the archive.

## Keep a full copy

Install [Git LFS](https://git-lfs.com/), then:

```sh
git clone https://github.com/jcameronjeff/steven-schrembeck-memorial.git
cd steven-schrembeck-memorial
git lfs pull
git lfs fsck
```

The `collection/` folder contains every saved original and supporting file. Audio and video use Git LFS. `collection-manifest.json` records each file’s byte size and SHA-256 checksum. A clone made without Git LFS contains small pointers in place of recordings; use `git lfs pull` to retrieve the actual files.

For a copy without Git, download the complete ZIP or **all** the GitHub release ZIP parts. Extract the parts into the same folder, then open `START-HERE.html`. Each part is a normal ZIP with complete files. Keep the checksums and caretaker guide with the collection.

## What is here

The October 10, 2026 recovery edition catalogues 111 entries: 19 captured articles, 64 original podcast/interview recordings, 25 videos and presentations, one novel linked externally, and two adaptations of *An Unwelcome Audience*. Lighthouse Horror’s adaptation is saved, bringing the audio file total to 65; The Podcast Inside Your House download returned HTTP 403. The novel has paperback and Kindle links, with no saved book file.

The later recovery of *The Technology That Centers You with Steven Schrembeck | 79* adds the publisher’s original MP3, a 1080p YouTube video, and the publisher-supplied transcript. Its old Buzzsprout audio link returned 404; the current podcast feed points to a working Spotify-hosted enclosure. Both formats have source metadata, checksums, and complete decode checks. The transcript is unreviewed. The recovery edition includes these files in the website, complete download, Git repository, and release ZIP parts. Earlier release snapshots remain available.

Seventeen articles have dedicated reading pages. Two captures retain the source’s “Unpublished” status. Two personal photographs are integrated into the site rather than given a separate gallery. Original source URLs appear beside saved copies. Explore brings all media together with type and collection filters, search, and date or title sorting. Downloads contains the complete archive and individual files. Old Archive, Timeline, and Writing & audio URLs forward to their replacements.

The compiled book, *The Small Moments Are Everything*, has a web reading edition with chapter navigation and an EPUB download. Its current ten-chapter edition is retained in `content/small-moments/`; the site builder preserves its paragraphs and editorial notes. The book is an edited selection from recordings, distinct from the 109 original catalogued works.

The archive is ordinary HTML, CSS, JavaScript and files. Core reading and links work without JavaScript; search and menus are progressive enhancements. No account, database, external fonts or analytics are required. Machine transcripts are marked as unreviewed. Original MKV videos may require a desktop player.

## Contribute and deploy

See [CONTRIBUTING.md](CONTRIBUTING.md) to share files through an invitation form or a GitHub pull request. Accepted contributions are added to Explore and Downloads automatically. The [Vercel website](https://steven-schrembeck-memorial.vercel.app/) deploys from `main`, with previews for proposed changes. [Deployment and caretaker instructions](docs/vercel.md) cover private uploads, review, and operation.

For a Vercel build without downloading all recordings, run `npm ci`, `npm run build`, and `python3 scripts/validate.py --site output/vercel`. This builds the current site and links to originals in Git LFS.

## Build and preview

Python 3.10+ builds the site using the standard library. ReportLab is needed only to regenerate the memory PDF.

```sh
python3 scripts/build.py
python3 scripts/make_pdf.py  # optional; requires reportlab
python3 scripts/collection_manifest.py
ln -s ../collection site/collection-files  # once, for local preview
python3 scripts/validate.py
python3 -m http.server 4318 --directory site --bind 127.0.0.1
```

Open `http://127.0.0.1:4318/`. `python3 scripts/package.py` creates a complete offline ZIP and release parts in `output/`. Those ZIPs include local copies of all media. The complete ZIP’s re-download link intentionally points to the online archive.

## Publication

GitHub Actions publishes `site/` to GitHub Pages after `scripts/prepare_pages.py` links large media directly to GitHub LFS and includes the other preserved files. This keeps the published Pages site below its size limit and independent of the OpZero deployment. Original media remains independently downloadable from the repository with LFS and the release archives.

The OpZero project is `25db8358-6294-4fff-be12-6077bdbdde42`, with Cloudflare Pages project `steven-schrembeck-archive-od6hvu-z56w`. Its frontend is the same static website. The small read-only Pages Worker serves media and the complete ZIP from the fixed R2 prefix `memorial/steven-schrembeck-archive-20261010/` in `opzero-src`. No other bucket paths are exposed.

For an authorized Cloudflare deploy, install Wrangler and esbuild, provide `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`, then run `node scripts/deploy-pages.mjs`. The token needs Pages deployment access. R2 objects can also be restored to any ordinary web server under `collection-files/`; Cloudflare is not necessary for reading a full downloaded copy.

The initial preservation workflow hydrates LFS from a temporary upload Worker, checks every media hash, uploads the LFS objects, builds ZIPs, and publishes the release. Its temporary upload secret is removed after completion. Future maintainers should use their own authenticated storage upload path rather than assuming that temporary endpoint remains active. Never commit credentials, `.private/`, or deployment tokens.

## Preservation status

Internet Archive, Wayback, Perma.cc, and copies held by trusted people remain to be arranged. Add verified archive URLs to the caretaker guide when those copies exist. Source retrieval notes describe historical gaps; the related-work records document later additions. Hosting is useful, but retaining independent complete copies is the preservation strategy.

The original materials retain their respective authorship and source credits. This repository does not assign a new blanket license to Steven’s work or others’ contributions.
