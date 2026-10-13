import {createHmac, timingSafeEqual, randomUUID} from 'node:crypto';

export const MAX_BYTES = 1024 * 1024 * 1024;
export const EXTENSIONS = new Set(['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.txt', '.md', '.mp3', '.m4a', '.wav', '.mp4', '.mov', '.mkv', '.webm', '.docx']);
function secret() {
  const value = process.env.CONTRIBUTION_INVITE_SECRET;
  if (!value || value.length < 32) throw new Error('Upload invitations are not configured.');
  return value;
}
const signature = data => createHmac('sha256', secret()).update(data).digest('base64url');
export function createInvite(days = 7, maxBytes = MAX_BYTES) {
  if (!Number.isFinite(days) || days <= 0 || days > 30 || !Number.isSafeInteger(maxBytes) || maxBytes < 1 || maxBytes > MAX_BYTES) throw new Error('Invites last 1–30 days and allow at most 1 GiB per file.');
  const data = Buffer.from(JSON.stringify({id: randomUUID(), expires: Date.now() + days * 86400000, maxBytes})).toString('base64url');
  return `${data}.${signature(data)}`;
}
export function verifyInvite(token) {
  if (typeof token !== 'string' || token.length > 2048) throw new Error('Invalid invitation.');
  const [data, sig, extra] = token.split('.');
  const expected = signature(data || '');
  if (extra || !sig || sig.length !== expected.length || !timingSafeEqual(Buffer.from(sig), Buffer.from(expected))) throw new Error('Invalid invitation.');
  const invite = JSON.parse(Buffer.from(data, 'base64url').toString());
  if (!/^[a-f0-9-]{36}$/.test(invite.id) || !Number.isFinite(invite.expires) || invite.expires <= Date.now() || !Number.isSafeInteger(invite.maxBytes) || invite.maxBytes < 1 || invite.maxBytes > MAX_BYTES) throw new Error('This invitation has expired or is invalid.');
  return invite;
}
export function uploadMetadata(pathname, payload) {
  const data = JSON.parse(payload || '{}');
  const invite = verifyInvite(data.invite);
  const match = /^incoming\/([a-f0-9-]{36})\/([a-zA-Z0-9][a-zA-Z0-9._-]{0,150})$/.exec(pathname);
  if (!match || !EXTENSIONS.has(match[2].slice(match[2].lastIndexOf('.')).toLowerCase())) throw new Error('Unsupported file name or type.');
  const metadata = {id: match[1], inviteId: invite.id, filename: match[2]};
  for (const [field, limit] of Object.entries({title: 200, name: 120, context: 4000, source: 2000, date: 10})) {
    const value = data[field] ?? '';
    if (typeof value !== 'string' || value.length > limit) throw new Error(`Invalid ${field}.`);
    metadata[field] = value.trim();
  }
  if (!metadata.title || !metadata.name || data.consent !== true) throw new Error('A title, public credit, and permission to publish are required.');
  if (metadata.source && !/^https?:\/\//.test(metadata.source)) throw new Error('Source must be an HTTP or HTTPS URL.');
  if (metadata.date && !/^\d{4}-\d{2}-\d{2}$/.test(metadata.date)) throw new Error('Date must be YYYY-MM-DD.');
  return {invite, metadata: {...metadata, consent: true}};
}
