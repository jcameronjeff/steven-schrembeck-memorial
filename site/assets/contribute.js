// Static mirrors send uploads to the Vercel-hosted intake service.
const form = document.querySelector('#contribution-form');
form.hidden = true;
const link = document.createElement('a');
link.href = 'https://steven-schrembeck-memorial.vercel.app/contribute.html' + location.hash;
link.textContent = 'Open the contribution form →';
link.rel = 'noreferrer';
document.querySelector('#upload-status').append(link);
