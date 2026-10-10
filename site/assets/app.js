document.documentElement.classList.add('js');
const menu = document.querySelector('.menu-button');
const nav = document.querySelector('.site-nav');
menu?.addEventListener('click', () => {
  const open = menu.getAttribute('aria-expanded') !== 'true';
  menu.setAttribute('aria-expanded', String(open));
  nav.classList.toggle('is-open', open);
  menu.textContent = open ? 'Close' : 'Menu';
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && menu?.getAttribute('aria-expanded') === 'true') {
    menu.click(); menu.focus();
  }
});
const search = document.querySelector('[data-search]');
const filters = [...document.querySelectorAll('[data-filter]')];
const entries = [...document.querySelectorAll('[data-entry]')];
const kindSelect = document.querySelector('[data-kind-select]');
let category = new URLSearchParams(location.search).get('type') || kindSelect?.value || 'all';
if (kindSelect) { if ([...kindSelect.options].some(o => o.value === category)) kindSelect.value = category; else category = 'all'; kindSelect.addEventListener('change', () => { category = kindSelect.value; applyFilters(); }); }
function applyFilters() {
  const query = (search?.value || '').trim().toLocaleLowerCase();
  let count = 0;
  for (const entry of entries) {
    const show = (category === 'all' || (category === 'featured' && entry.dataset.main === 'true') || entry.dataset.kind === category) && entry.textContent.toLocaleLowerCase().includes(query);
    entry.hidden = !show;
    count += Number(show);
  }
  const status = document.querySelector('[data-results]');
  if (status) { const noun = status.dataset.noun ? (count === 1 ? status.dataset.noun.replace(/s$/, '') : status.dataset.noun) : (count === 1 ? 'memory' : 'memories'); status.textContent = `${count} ${noun}${query ? ` matching “${search.value.trim()}”` : ''}`; }
  const empty = document.querySelector('[data-empty]');
  if (empty) empty.hidden = count > 0;
}
search?.addEventListener('input', applyFilters);
filters.forEach(button => button.addEventListener('click', () => {
  category = button.dataset.filter;
  filters.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  applyFilters();
}));
document.querySelector('[data-reset]')?.addEventListener('click', () => {
  search.value = ''; category = 'all'; if (kindSelect) kindSelect.value = 'all';
  filters.forEach(item => item.setAttribute('aria-pressed', String(item.dataset.filter === 'all')));
  applyFilters(); search.focus();
});
document.querySelectorAll('audio').forEach(player => player.addEventListener('play', () => {
  document.querySelectorAll('audio').forEach(other => { if (other !== player) other.pause(); });
}));
document.querySelectorAll('[data-open-dialog]').forEach(button => button.addEventListener('click', () => {
  document.getElementById(button.dataset.openDialog).showModal();
}));
document.querySelectorAll('[data-close-dialog]').forEach(button => button.addEventListener('click', () => button.closest('dialog').close()));
document.querySelectorAll('dialog').forEach(dialog => dialog.addEventListener('click', event => {
  const box = dialog.getBoundingClientRect();
  if (event.target === dialog && (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom)) dialog.close();
}));
document.querySelectorAll('[data-photo]').forEach(link => link.addEventListener('click', event => {
  event.preventDefault();
  const dialog = document.getElementById('photo-dialog');
  const image = dialog.querySelector('img');
  image.src = link.href; image.alt = link.querySelector('img').alt;
  dialog.querySelector('[data-photo-caption]').textContent = image.alt;
  dialog.showModal();
}));
document.querySelector('[data-memory-form]')?.addEventListener('submit', event => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  if (!String(data.get('name')).trim() || !String(data.get('memory')).trim()) {
    form.querySelector('[data-form-status]').textContent = 'Please add your name and a memory before downloading.';
    return;
  }
  const text = `A memory of Steven Schrembeck\n\nShared by: ${String(data.get('name')).trim()}\nConnection: ${String(data.get('connection')).trim() || 'Not specified'}\nSaved: ${new Date().toISOString().slice(0,10)}\n\n${String(data.get('memory')).trim()}\n\nThis file was saved on the writer’s device. It has not been sent or published.\n`;
  const url = URL.createObjectURL(new Blob([text], {type:'text/plain;charset=utf-8'}));
  const link = document.createElement('a');
  link.href = url; link.download = 'a-memory-of-steven.txt';
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  form.querySelector('[data-form-status]').textContent = 'Your download is ready. Keep the text file or share it with the person caring for the collection. Nothing was sent.';
});

if (entries.length) applyFilters();
