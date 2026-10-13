import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createInvite, verifyInvite, uploadMetadata} from '../lib/invitations.mjs';
process.env.CONTRIBUTION_INVITE_SECRET = 'test-only-secret-'.repeat(4);
const pathname = 'incoming/12345678-1234-1234-1234-123456789abc/photo.jpg';
const metadata = {title: 'A memory', name: 'A friend', consent: true};
test('valid invitation, metadata, and per-file limit', () => {
  const token = createInvite(1, 1000);
  assert.equal(verifyInvite(token).maxBytes, 1000);
  assert.equal(uploadMetadata(pathname, JSON.stringify({...metadata, invite: token})).metadata.title, 'A memory');
});
test('tampering, expiry, secret rotation, and missing configuration fail closed', () => {
  const token = createInvite();
  assert.throws(() => verifyInvite(token + 'x'));
  const now = Date.now;
  Date.now = () => now() + 31 * 86400000;
  assert.throws(() => verifyInvite(token));
  Date.now = now;
  const secret = process.env.CONTRIBUTION_INVITE_SECRET;
  process.env.CONTRIBUTION_INVITE_SECRET = 'rotated'.repeat(10);
  assert.throws(() => verifyInvite(token));
  delete process.env.CONTRIBUTION_INVITE_SECRET;
  assert.throws(() => verifyInvite(token));
  process.env.CONTRIBUTION_INVITE_SECRET = secret;
});
test('reject unsafe names, active documents, missing consent and executable source links', () => {
  const payload = {...metadata, invite: createInvite()};
  for (const path of ['incoming/../photo.jpg', pathname.replace('.jpg', '.html'), pathname.replace('photo.jpg', '../../photo.jpg')]) {
    assert.throws(() => uploadMetadata(path, JSON.stringify(payload)));
  }
  for (const change of [{consent: false}, {source: 'javascript:alert(1)'}, {title: ''}, {context: 'x'.repeat(4001)}]) {
    assert.throws(() => uploadMetadata(pathname, JSON.stringify({...payload, ...change})));
  }
});
