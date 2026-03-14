async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

const PAGE_SIZE = 10;
let notesPage = 1;
let actionsPage = 1;

async function loadNotes() {
  const list = document.getElementById('notes');
  const info = document.getElementById('notes-page-info');
  list.innerHTML = '';
  const data = await fetchJSON(`/notes/?page=${notesPage}&page_size=${PAGE_SIZE}`);
  for (const n of data.items) {
    const li = document.createElement('li');
    li.textContent = `${n.title}: ${n.content}`;
    list.appendChild(li);
  }
  const totalPages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));
  info.textContent = `Page ${notesPage} of ${totalPages} (${data.total} total)`;
  document.getElementById('notes-prev').disabled = notesPage <= 1;
  document.getElementById('notes-next').disabled = notesPage >= totalPages;
}

async function loadActions() {
  const list = document.getElementById('actions');
  const info = document.getElementById('actions-page-info');
  list.innerHTML = '';
  const data = await fetchJSON(`/action-items/?page=${actionsPage}&page_size=${PAGE_SIZE}`);
  for (const a of data.items) {
    const li = document.createElement('li');
    li.textContent = `${a.description} [${a.completed ? 'done' : 'open'}]`;
    if (!a.completed) {
      const btn = document.createElement('button');
      btn.textContent = 'Complete';
      btn.onclick = async () => {
        await fetchJSON(`/action-items/${a.id}/complete`, { method: 'PUT' });
        loadActions();
      };
      li.appendChild(btn);
    }
    list.appendChild(li);
  }
  const totalPages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));
  info.textContent = `Page ${actionsPage} of ${totalPages} (${data.total} total)`;
  document.getElementById('actions-prev').disabled = actionsPage <= 1;
  document.getElementById('actions-next').disabled = actionsPage >= totalPages;
}

window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('note-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('note-title').value;
    const content = document.getElementById('note-content').value;
    await fetchJSON('/notes/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content }),
    });
    e.target.reset();
    notesPage = 1;
    loadNotes();
  });

  document.getElementById('action-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const description = document.getElementById('action-desc').value;
    await fetchJSON('/action-items/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description }),
    });
    e.target.reset();
    actionsPage = 1;
    loadActions();
  });

  document.getElementById('notes-prev').addEventListener('click', () => { notesPage--; loadNotes(); });
  document.getElementById('notes-next').addEventListener('click', () => { notesPage++; loadNotes(); });
  document.getElementById('actions-prev').addEventListener('click', () => { actionsPage--; loadActions(); });
  document.getElementById('actions-next').addEventListener('click', () => { actionsPage++; loadActions(); });

  loadNotes();
  loadActions();
});
