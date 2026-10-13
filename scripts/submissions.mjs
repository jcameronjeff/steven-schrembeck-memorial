// Private caretaker tools. Credentials never become part of the public archive.
import {get, list, del} from '@vercel/blob';
import {createInvite} from '../lib/invitations.mjs';
import {mkdir, writeFile, readFile} from 'node:fs/promises';
import {createWriteStream} from 'node:fs';
import {pipeline} from 'node:stream/promises';
import {Readable} from 'node:stream';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const [command, id, ...args] = process.argv.slice(2);
async function metadataFor(id) {
  if (!/^[a-f0-9-]{36}$/.test(id || '')) throw new Error('Use a submission receipt ID.');
  const blob = await get(`submissions/${id}.json`, {access: 'private'});
  if (!blob) throw new Error('Receipt not found. Check pending uploads in the Blob dashboard.');
  const data = await new Response(blob.stream).json();
  if (data.id !== id || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,150}$/.test(data.filename) || data.blobPath !== `incoming/${id}/${data.filename}`) throw new Error('Invalid submission record.');
  return data;
}
try {
  if (command === 'invite') {
    const base = new URL(id || process.env.ARCHIVE_SITE_URL || 'https://steven-schrembeck-memorial.vercel.app');
    if (base.protocol !== 'https:' && base.hostname !== 'localhost') throw new Error('Use an HTTPS site URL.');
    base.pathname = '/contribute.html'; base.search = ''; base.hash = 'invite=' + createInvite(Number(args[0] || 7));
    console.log(base.href);
  } else if (command === 'list') {
    let cursor;
    do {
      const result = await list({prefix: 'submissions/', cursor});
      for (const blob of result.blobs) {
        const data = await metadataFor(path.basename(blob.pathname, '.json'));
        console.log(JSON.stringify({id: data.id, status: data.status, title: data.title, name: data.name, receivedAt: data.receivedAt}));
      }
      cursor = result.hasMore ? result.cursor : undefined;
    } while (cursor);
  } else if (command === 'review' || command === 'import') {
    const data = await metadataFor(id);
    const directory = path.join(root, '.private/submissions', id);
    await mkdir(directory, {recursive: true, mode: 0o700});
    await writeFile(path.join(directory, 'metadata.json'), JSON.stringify(data, null, 2), {mode: 0o600});
    if (command === 'review') {
      console.log(JSON.stringify(data, null, 2));
      console.log('To download for inspection: npm run submissions -- download', id);
    } else {
      const slug = args[args.indexOf('--slug') + 1];
      if (!args.includes('--slug') || !slug) throw new Error('Use import ID --slug descriptive-name after reviewing the downloaded file.');
      const local = path.join(directory, data.filename);
      // Require explicit download/review before importing. Import strips private receipt fields.
      await readFile(path.join(directory, 'downloaded.json'));
      const result = spawnSync('python3', ['scripts/contribute.py', 'add', local, '--metadata', path.join(directory, 'metadata.json'), '--slug', slug], {cwd: root, stdio: 'inherit'});
      if (result.status !== 0) throw new Error('Import failed.');
    }
  } else if (command === 'download') {
    const data = await metadataFor(id);
    const directory = path.join(root, '.private/submissions', id);
    await mkdir(directory, {recursive: true, mode: 0o700});
    const blob = await get(data.blobPath, {access: 'private'});
    if (!blob) throw new Error('File not found.');
    await pipeline(Readable.fromWeb(blob.stream), createWriteStream(path.join(directory, data.filename), {mode: 0o600}));
    await writeFile(path.join(directory, 'downloaded.json'), JSON.stringify({at: new Date().toISOString()}));
    console.log('Saved for review:', path.join(directory, data.filename));
  } else if (command === 'delete') {
    if (!args.includes('--confirm')) throw new Error('Use delete ID --confirm after rejection or confirmed publication.');
    const data = await metadataFor(id);
    await del(data.blobPath);
    await del(`submissions/${id}.json`);
    console.log('Deleted private submission', id);
  } else {
    console.log('Commands: invite [SITE_URL] [DAYS], list, review ID, download ID, import ID --slug NAME, delete ID --confirm');
  }
} catch (error) { console.error(error.message); process.exitCode = 1; }
