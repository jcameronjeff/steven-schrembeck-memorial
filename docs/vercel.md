# Vercel deployment and private contributions

The Vercel project `steven-schrembeck-memorial` in the `opzero` team is connected to `jcameronjeff/steven-schrembeck-memorial`. Production follows `main`; branches and pull requests receive previews through Vercel's GitHub integration. Existing Cloudflare and GitHub Pages deployments remain available.

`vercel.json` runs `npm ci` and `npm run build`, publishing `output/vercel`. The Python builder supports ordinary LFS pointers; it does not need to download the full archive. The build regenerates the file inventory, validates contribution metadata/checksums, copies small preserved source files, and links LFS originals to GitHub at the deployed commit SHA. The deploy fails if an LFS pointer would be served as a real file.

`api/upload.mjs` and `api/submission-status.mjs` run as Node.js Vercel Functions. The client uploads directly to private Vercel Blob storage with a scoped, expiring token. A signed provider callback saves the review receipt; the browser waits for that receipt before confirming delivery. No upload is copied into Git or made public automatically.

## Production configuration

The project needs a **private** Blob store and these production-only environment variables:

- `BLOB_READ_WRITE_TOKEN`: attached by the Blob store connection.
- `CONTRIBUTION_INVITE_SECRET`: at least 32 random characters, used to sign invitation links. Store a protected caretaker copy; rotate it to revoke all outstanding invitations. Already-issued upload tokens can remain valid for up to one hour.

Do not attach these credentials to untrusted branch or fork previews. The site and contribution form render in previews; upload requests fail closed with a clear unavailable message. Production is the place for uploads and end-to-end checks. Do not enable Vercel's Git LFS download setting: builds work directly from pointers.

The initial private store is named `steven-schrembeck-submissions`. Maintain a local `.private/caretaker.env` with the two variables above (mode `0600`). Git ignores `.private/`, `.vercel/`, and `.env*`. Use `vercel env pull .private/production.env --environment production` to retrieve readable production credentials; sensitive invite secrets must come from their saved original or be rotated. Never print or commit the environment file.

## Checks and publication

```sh
npm ci
npm test
npm run build
python3 scripts/validate.py --site output/vercel
```

GitHub Actions runs those checks for pushes and pull requests using an LFS-pointer checkout. After a merge, confirm Vercel reports a Ready production deployment for the merged SHA. Check the homepage, Explore, one original media download, and `/contribute.html`. A successful CLI deployment alone does not prove Git auto-deployment is connected.

To test intake, generate a short-lived invitation, submit a clearly labeled temporary text file, confirm its pending receipt, download and compare the bytes, then delete the private test submission. Do not import test material into the public collection.

## Operational limits

Invitations last up to 30 days and default to seven. They allow repeated submissions until expiry, with a maximum of 1 GiB per file; they are intended for trusted invitees. Monitor Blob usage and delete processed or abandoned staging copies. These invitations are not a public anonymous upload service or a per-invite total-storage quota.

Private submissions require working Vercel Blob credentials. Published archive originals remain in Git LFS independently. Public downloads consume GitHub LFS bandwidth, and private staging consumes Vercel Blob storage/transfer usage. The deployment does not rebuild release ZIPs or sync newly contributed originals into the historical R2 snapshot.
