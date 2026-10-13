import {handleUpload} from '@vercel/blob/client';
import {put} from '@vercel/blob';
import {uploadMetadata} from '../lib/invitations.mjs';

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') return res.status(405).json({error: 'Use POST.'});
  if (!process.env.BLOB_READ_WRITE_TOKEN || !process.env.CONTRIBUTION_INVITE_SECRET) return res.status(503).json({error: 'Uploads are not available yet. Please contact the archive caretaker.'});
  try {
    const result = await handleUpload({
      request: req, body: typeof req.body === 'string' ? JSON.parse(req.body) : req.body,
      onBeforeGenerateToken: async (pathname, payload) => {
        const {invite, metadata} = uploadMetadata(pathname, payload);
        return {maximumSizeInBytes: invite.maxBytes, validUntil: Math.min(invite.expires, Date.now() + 3600000), addRandomSuffix: false, allowOverwrite: false, tokenPayload: JSON.stringify(metadata)};
      },
      onUploadCompleted: async ({blob, tokenPayload}) => {
        // handleUpload verifies the provider's callback signature before this runs.
        const metadata = JSON.parse(tokenPayload);
        if (blob.pathname !== `incoming/${metadata.id}/${metadata.filename}`) throw new Error('Upload path mismatch.');
        await put(`submissions/${metadata.id}.json`, JSON.stringify({...metadata, blobPath: blob.pathname, receivedAt: new Date().toISOString(), status: 'pending'}), {access: 'private', contentType: 'application/json', addRandomSuffix: false, allowOverwrite: true});
      }
    });
    return res.status(200).json(result);
  } catch (error) {
    return res.status(400).json({error: error.message.startsWith('Vercel Blob') ? 'Upload could not be completed. Please try again.' : error.message});
  }
}
