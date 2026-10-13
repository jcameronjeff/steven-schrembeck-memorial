import {get} from '@vercel/blob';
import {verifyInvite} from '../lib/invitations.mjs';

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') return res.status(405).json({error: 'Use POST.'});
  try {
    const {id, invite: token} = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
    const invite = verifyInvite(token);
    if (!/^[a-f0-9-]{36}$/.test(id)) throw new Error('Invalid receipt.');
    const object = await get(`submissions/${id}.json`, {access: 'private'});
    if (!object) return res.status(202).json({status: 'processing'});
    const metadata = await new Response(object.stream).json();
    if (metadata.inviteId !== invite.id) throw new Error('Invalid receipt.');
    return res.status(200).json({status: metadata.status});
  } catch { return res.status(400).json({error: 'Unable to check this receipt.'}); }
}
