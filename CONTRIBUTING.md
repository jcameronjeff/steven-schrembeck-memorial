# Share a file or memory of Steven

There are two ways to contribute. Every contribution is reviewed before it becomes part of the public archive.

## Without Git

Ask the archive caretaker for an invitation link to the [contribution form](https://steven-schrembeck-memorial.vercel.app/contribute.html). Choose one photo, document, recording, or video, or write a memory. Add a title, the name you want credited publicly, and any context or original source link.

Uploads remain private until accepted. The form shows a receipt when the server confirms delivery. Save that receipt. Submit additional files separately. Each file can be up to 1 GiB; contact the caretaker for larger originals. Invitation links are private, reusable until expiry, and should not be posted publicly.

Only submit material you have permission to publish. The credit, context, and original file will become public after review, including any identifying information inside the file. Preserve the original wording and explain uncertainties rather than guessing dates or attribution.

## With Git

Install Git, Git LFS, Node.js 24, Python 3.10+, and the GitHub CLI. You can contribute without downloading every existing recording:

```sh
git lfs install
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/jcameronjeff/steven-schrembeck-memorial.git
cd steven-schrembeck-memorial
npm ci
```

Create a metadata file **outside the checkout**, such as `../memory-metadata.json`:

```json
{
  "title": "A memory from our team",
  "name": "Your preferred public credit",
  "context": "Where this came from and what you remember.",
  "source": "",
  "date": "",
  "consent": true
}
```

Use a known date in `YYYY-MM-DD` form or leave it blank. Then:

```sh
npm run contribute -- add /path/to/original.pdf --metadata ../memory-metadata.json --slug team-memory
npm run contribute -- check
npm run build
python3 scripts/validate.py --site output/vercel
```

The importer copies the original into `collection/contributions/team-memory/files/`, computes its SHA-256 checksum, and writes public metadata beside it. All files in a contribution's `files/` directory use LFS automatically. Do not upload those files using GitHub's web file editor; it bypasses the local LFS upload hook.

If you have repository write access, start from the latest `origin/main` with only this new contribution changed, then run:

```sh
npm run contribute -- pr --slug team-memory
```

This checks the file, creates a contribution branch, refreshes the archive manifest, commits the contribution, uploads its LFS object, and opens a pull request. Review the preview before merging. It refuses unrelated local changes or branch history.

Without repository write access, fork the repository and clone your fork instead. After importing, create a branch, run `python3 scripts/collection_manifest.py`, commit only your contribution folder and `collection-manifest.json`, and push to your fork. Open a pull request to this repository's `main`. Fork previews require maintainer authorization; upload functionality is disabled in previews. Fork LFS files should be verified by the maintainer before merge.

Do not edit historical retrieval records to imply that a new contribution was part of the original recovery. Contributions appear automatically in Explore and Downloads. Existing release ZIPs are dated snapshots; creating a new contribution does not rebuild a release ZIP.

## Caretaker: invitations and review

See [Vercel operations](docs/vercel.md) for credentials. Run these commands using a protected environment file containing `BLOB_READ_WRITE_TOKEN` and `CONTRIBUTION_INVITE_SECRET`:

```sh
node --env-file=.private/caretaker.env scripts/submissions.mjs invite https://steven-schrembeck-memorial.vercel.app 7
node --env-file=.private/caretaker.env scripts/submissions.mjs list
node --env-file=.private/caretaker.env scripts/submissions.mjs review RECEIPT_ID
node --env-file=.private/caretaker.env scripts/submissions.mjs download RECEIPT_ID
```

Inspect the downloaded original in `.private/submissions/RECEIPT_ID/`. Check attribution and permission, and consider any personal information inside the file. Then import only accepted material:

```sh
node --env-file=.private/caretaker.env scripts/submissions.mjs import RECEIPT_ID --slug descriptive-name
npm run contribute -- pr --slug descriptive-name
```

The importer strips private receipt fields. Nothing is published until the pull request is merged. After confirming publication and the archived checksum, delete the staging copy:

```sh
node --env-file=.private/caretaker.env scripts/submissions.mjs delete RECEIPT_ID --confirm
```

Use the same delete command for rejected submissions. An interrupted upload may have an `incoming/` object without a receipt; inspect these in the private Blob store and remove abandoned uploads manually. Keep invitation and storage credentials out of Git and never send them to contributors.
