import {upload} from '@vercel/blob/client';

const form = document.querySelector('#contribution-form');
const status = document.querySelector('#upload-status');
const invite = new URLSearchParams(location.hash.slice(1)).get('invite');
history.replaceState(null, '', location.pathname);
if (!invite) {
  form.hidden = true;
  status.textContent = 'Please ask the archive caretaker for an invitation link to share a file or memory.';
}
form.addEventListener('submit', async event => {
  event.preventDefault();
  const button = form.querySelector('button[type=submit]');
  button.disabled = true;
  try {
    const fields = new FormData(form);
    let file = fields.get('file');
    if (!file?.size) {
      const memory = fields.get('memory').trim();
      if (!memory) throw new Error('Choose a file or write a memory.');
      file = new File([memory + '\n'], 'memory.txt', {type: 'text/plain'});
    } else if (fields.get('memory').trim()) throw new Error('Please submit your memory and file separately so each can be reviewed.');
    if (file.size > 1024 ** 3) throw new Error('Please contact the caretaker for files larger than 1 GiB.');
    const id = crypto.randomUUID();
    const filename = file.name.replace(/[^a-zA-Z0-9._-]/g, '-').replace(/^[^a-zA-Z0-9]+/, '').slice(-151);
    const payload = Object.fromEntries(['title', 'name', 'context', 'source', 'date'].map(key => [key, fields.get(key)]));
    status.textContent = 'Preparing your upload…';
    await upload(`incoming/${id}/${filename}`, file, {
      access: 'private', handleUploadUrl: '/api/upload', multipart: true,
      clientPayload: JSON.stringify({...payload, invite, consent: fields.has('consent')}),
      onUploadProgress: ({percentage}) => { status.textContent = `Uploading: ${Math.round(percentage)}%`; }
    });
    status.textContent = 'Upload complete. Confirming receipt…';
    let received = false;
    for (let attempt = 0; attempt < 15; attempt++) {
      await new Promise(resolve => setTimeout(resolve, 2000));
      const response = await fetch('/api/submission-status', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({id, invite})});
      if (response.ok && (await response.json()).status === 'pending') { received = true; break; }
    }
    status.textContent = received ? `Thank you. Your contribution is received and awaiting review. Receipt: ${id}. Nothing has been published yet.` : `Your file uploaded, but the receipt is still processing. Please save this reference and contact the caretaker before trying again: ${id}.`;
    form.reset();
  } catch (error) { status.textContent = error.message || 'Upload failed. Please try again.'; }
  finally { button.disabled = false; }
});
