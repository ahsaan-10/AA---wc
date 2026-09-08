/* FILED — state, formatting and the shared overlay pieces. */

const $  = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
));

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

const fmt = {
  money(n, opts = {}) {
    const v = Math.abs(Math.round(n));
    const s = '$' + v.toLocaleString('en-US');
    if (opts.signed && n < 0) return '−' + s;
    return s;
  },
  /* A return either produces a refund or a balance due. Never show a bare number. */
  outcome(n) {
    if (n === 0) return 'Pass-through';
    return n > 0 ? fmt.money(n) + ' refund' : fmt.money(n) + ' due';
  },
  date(iso) {
    if (!iso) return '—';
    const d = new Date(iso + (iso.length === 10 ? 'T12:00:00' : ''));
    return `${MONTHS[d.getMonth()]} ${d.getDate()}`;
  },
  dateFull(iso) {
    if (!iso) return '—';
    const d = new Date(iso + (iso.length === 10 ? 'T12:00:00' : ''));
    return `${MONTHS[d.getMonth()]} ${d.getDate()}, ${d.getFullYear()}`;
  },
  time(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    let h = d.getHours(); const m = String(d.getMinutes()).padStart(2, '0');
    const ap = h < 12 ? 'am' : 'pm'; h = h % 12 || 12;
    return `${h}:${m} ${ap}`;
  },
  stamp(iso) { return `${fmt.date(iso.slice(0, 10))}, ${fmt.time(iso)}`; },
  pct(n) { return `${Math.round(n)}%`; },
  days(iso) {
    const a = new Date(SEASON.today + 'T12:00:00');
    const b = new Date(iso + (iso.length === 10 ? 'T12:00:00' : ''));
    return Math.round((a - b) / 86400000);
  }
};

const stageMeta  = (key) => STAGES.find((s) => s.key === key) || { key, label: key, short: key };
const staffById  = (id) => STAFF.find((s) => s.id === id) || { name: '—', initials: '—', cred: '' };
const staffName  = (id) => staffById(id).name;
const daysToDeadline = fmt.days(SEASON.individualDue) * -1;

/* ── Store ─────────────────────────────────────────────────────────────── */

const App = {
  state: {
    clients: JSON.parse(JSON.stringify(CLIENTS)),
    route: { name: 'cover', params: [] },
    roster: { view: 'all', q: '', sort: { key: 'since', dir: 'asc' }, selected: [] },
    seen: [],
    drafts: {},
    resolved: [],
    docsIn: [],
    batches: JSON.parse(JSON.stringify(BATCHES)),
    signed: JSON.parse(JSON.stringify(SIGNATURES)),
    invoices: JSON.parse(JSON.stringify(INVOICES)),
    ackServiceDown: false,
    loading: false,
    toasts: []
  },

  client(id) { return this.state.clients.find((c) => c.id === id); },

  set(mutator) { mutator(this.state); render(); },

  /* Stage moves are the spine of the product: one write, and every count,
     board column and queue that reads from it updates on the next render. */
  moveStage(id, stage, { silent = false, note = '' } = {}) {
    const c = this.client(id);
    if (!c) return;
    const from = stageMeta(c.stage).label;
    c.stage = stage;
    c.since = SEASON.today;
    if (note) c.notes.unshift({ on: SEASON.today, by: 'do', text: note });
    if (!silent) this.toast(`Moved to ${stageMeta(stage).label.toLowerCase()}`, `${c.name} — from ${from.toLowerCase()}`);
    render();
  },

  toast(text, sub = '') {
    const id = Math.random().toString(36).slice(2);
    this.state.toasts.push({ id, text, sub });
    renderToasts();
    setTimeout(() => {
      this.state.toasts = this.state.toasts.filter((t) => t.id !== id);
      renderToasts();
    }, 5200);
  },

  draft(key, value) {
    if (value === undefined) return this.state.drafts[key] ?? '';
    this.state.drafts[key] = value;
    return value;
  },

  go(hash) {
    if (location.hash === hash) { route(); return; }
    location.hash = hash;
  }
};

/* ── Derived reads ─────────────────────────────────────────────────────── */

const byStage = (key) => App.state.clients.filter((c) => c.stage === key);
const stageCounts = () => Object.fromEntries(STAGES.map((s) => [s.key, byStage(s.key).length]));
const outstandingDocs = (c) => (c.docs || []).filter((d) => d.status === 'out' && !App.state.docsIn.includes(c.id + '::' + d.form));
const isDocIn = (c, d) => d.status === 'in' || App.state.docsIn.includes(c.id + '::' + d.form);
const stuckDays = (c) => fmt.days(c.since);
const signatureOf = (id) => App.state.signed[id];
const readyToTransmit = () => App.state.clients.filter((c) => c.stage === 'signature' && signatureOf(c.id) && signatureOf(c.id).signed);

/* ── Fragments ─────────────────────────────────────────────────────────── */

function pill(stage) {
  const m = stageMeta(stage);
  return `<span class="pill" data-stage="${stage}"><span class="dot"></span>${esc(m.label)}</span>`;
}

function personChip(id) {
  const s = staffById(id);
  return `<span title="${esc(s.name)}${s.cred ? ', ' + s.cred : ''}">${esc(s.name)}</span>`;
}

function idTag(id) { return `<span class="mono">${esc(id)}</span>`; }

/* ── Toasts ────────────────────────────────────────────────────────────── */

function renderToasts() {
  $('#toasts').innerHTML = App.state.toasts.slice(-3).map((t) => `
    <div class="toast" role="status">
      <div>
        <div>${esc(t.text)}</div>
        ${t.sub ? `<div class="toast-sub">${esc(t.sub)}</div>` : ''}
      </div>
    </div>`).join('');
}

/* ── Confirmation dialog ───────────────────────────────────────────────── */

let lastFocused = null;

function confirmAction({ title, body, consent, confirmLabel, tone = 'danger', detail = '' }) {
  return new Promise((resolve) => {
    lastFocused = document.activeElement;
    const wrap = document.createElement('div');
    wrap.className = 'scrim center';
    wrap.innerHTML = `
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="mtitle">
        <div class="modal-head"><h2 id="mtitle">${esc(title)}</h2></div>
        <div class="modal-body">
          <p>${body}</p>
          ${detail ? `<div class="panel" style="background:var(--panel-sunk)"><div class="panel-body" style="padding:10px 12px">${detail}</div></div>` : ''}
          ${consent ? `<label class="consent"><input type="checkbox" id="consent"><span>${esc(consent)}</span></label>` : ''}
        </div>
        <div class="modal-foot">
          <button class="btn" data-x="cancel">Cancel</button>
          <button class="btn btn-${tone}" data-x="ok" ${consent ? 'disabled' : ''}>${esc(confirmLabel)}</button>
        </div>
      </div>`;
    document.body.appendChild(wrap);

    const ok = $('[data-x="ok"]', wrap);
    const consentBox = $('#consent', wrap);
    if (consentBox) consentBox.addEventListener('change', () => { ok.disabled = !consentBox.checked; });

    const close = (val) => {
      wrap.remove();
      if (lastFocused && lastFocused.focus) lastFocused.focus();
      resolve(val);
    };
    $('[data-x="cancel"]', wrap).addEventListener('click', () => close(false));
    ok.addEventListener('click', () => close(true));
    wrap.addEventListener('click', (e) => { if (e.target === wrap) close(false); });
    wrap.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') close(false);
      if (e.key === 'Tab') {
        const f = $$('button, input', wrap);
        const i = f.indexOf(document.activeElement);
        if (e.shiftKey && i <= 0) { e.preventDefault(); f[f.length - 1].focus(); }
        else if (!e.shiftKey && i === f.length - 1) { e.preventDefault(); f[0].focus(); }
      }
    });
    (consentBox || ok).focus();
  });
}

/* ── Command palette ───────────────────────────────────────────────────── */

const PALETTE_SCREENS = [
  { title: 'Season command', hash: '#/command', sub: 'Today at a glance' },
  { title: 'Client roster', hash: '#/clients', sub: 'All open returns' },
  { title: 'Document intake and chase', hash: '#/documents', sub: 'What is outstanding' },
  { title: 'Review queue', hash: '#/review', sub: 'Waiting on a reviewer' },
  { title: 'E-file centre', hash: '#/efile', sub: 'Batches and acknowledgments' },
  { title: 'Deadline board', hash: '#/deadlines', sub: 'By due date' },
  { title: 'Team capacity', hash: '#/team', sub: 'Load and reassignment' },
  { title: 'Billing and realisation', hash: '#/billing', sub: 'Invoices and write-offs' },
  { title: 'Client portal preview', hash: '#/portal', sub: 'The taxpayer’s view' },
  { title: 'Case study cover', hash: '#/cover', sub: 'How this was scoped' }
];

const PALETTE_ACTIONS = [
  { title: 'Transmit signed returns to the IRS', hash: '#/efile', sub: 'E-file centre' },
  { title: 'Open the reject lane', hash: '#/efile', sub: 'Returns the IRS sent back' },
  { title: 'Draft a document reminder', hash: '#/documents', sub: 'Document chase' },
  { title: 'File Form 4868 extension', hash: '#/deadlines', sub: 'Deadline board' }
];

let paletteState = { open: false, q: '', active: 0, results: [] };

function paletteResults(q) {
  const term = q.trim().toLowerCase();
  const clients = App.state.clients
    .filter((c) => !term || c.name.toLowerCase().includes(term) || c.id.toLowerCase().includes(term)
      || (c.occupation || '').toLowerCase().includes(term) || (c.business || '').toLowerCase().includes(term)
      || c.entity.toLowerCase().includes(term))
    .slice(0, term ? 7 : 5)
    .map((c) => ({ kind: 'Client', title: c.name, sub: `${c.id} · ${c.entity} · ${stageMeta(c.stage).label}`, hash: `#/client/${c.id}/overview` }));

  const screens = PALETTE_SCREENS
    .filter((s) => !term || s.title.toLowerCase().includes(term) || s.sub.toLowerCase().includes(term))
    .map((s) => ({ kind: 'Screen', ...s }));

  const actions = PALETTE_ACTIONS
    .filter((a) => !term || a.title.toLowerCase().includes(term))
    .map((a) => ({ kind: 'Action', ...a }));

  const rejects = App.state.clients.filter((c) => c.stage === 'rejected')
    .filter((c) => !term || c.reject.code.toLowerCase().includes(term) || c.name.toLowerCase().includes(term))
    .map((c) => ({ kind: 'Reject', title: `${c.reject.code} — ${c.name}`, sub: 'Open reject resolution', hash: `#/reject/${c.id}` }));

  return [...clients, ...(term ? rejects : []), ...screens, ...actions].slice(0, 12);
}

function openPalette() {
  paletteState = { open: true, q: '', active: 0, results: paletteResults('') };
  lastFocused = document.activeElement;
  const wrap = document.createElement('div');
  wrap.className = 'scrim top';
  wrap.id = 'palette';
  wrap.innerHTML = `
    <div class="palette" role="dialog" aria-modal="true" aria-label="Command palette">
      <div class="palette-input">
        <svg width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden="true"><circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.4"/><path d="M11 11l4 4" stroke="currentColor" stroke-width="1.4"/></svg>
        <input id="pq" type="text" placeholder="Jump to a client, return, reject code or screen" aria-label="Search" autocomplete="off">
      </div>
      <div class="palette-results" id="presults"></div>
      <div class="palette-foot"><span><kbd>↑</kbd><kbd>↓</kbd> move</span><span><kbd>↵</kbd> open</span><span><kbd>esc</kbd> close</span></div>
    </div>`;
  document.body.appendChild(wrap);
  drawPalette();

  const input = $('#pq', wrap);
  input.addEventListener('input', () => {
    paletteState.q = input.value;
    paletteState.results = paletteResults(input.value);
    paletteState.active = 0;
    drawPalette();
  });
  wrap.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { closePalette(); }
    if (e.key === 'ArrowDown') { e.preventDefault(); paletteState.active = Math.min(paletteState.active + 1, paletteState.results.length - 1); drawPalette(); }
    if (e.key === 'ArrowUp') { e.preventDefault(); paletteState.active = Math.max(paletteState.active - 1, 0); drawPalette(); }
    if (e.key === 'Enter') {
      const r = paletteState.results[paletteState.active];
      if (r) { closePalette(); App.go(r.hash); }
    }
  });
  wrap.addEventListener('click', (e) => {
    if (e.target === wrap) return closePalette();
    const btn = e.target.closest('.presult');
    if (btn) { const r = paletteState.results[Number(btn.dataset.i)]; closePalette(); App.go(r.hash); }
  });
  input.focus();
}

function drawPalette() {
  const box = $('#presults');
  if (!box) return;
  if (!paletteState.results.length) {
    box.innerHTML = `<div class="empty" style="padding:30px 20px">
      <h3>Nothing matches “${esc(paletteState.q)}”</h3>
      <p>Try a surname, a client ID such as ${idTag('RAG-0118')}, a reject code, or the name of a screen.</p>
    </div>`;
    return;
  }
  let lastKind = null;
  box.innerHTML = paletteState.results.map((r, i) => {
    const head = r.kind !== lastKind ? `<div class="palette-group">${esc(r.kind === 'Client' ? 'Clients' : r.kind === 'Screen' ? 'Screens' : r.kind === 'Reject' ? 'Rejected returns' : 'Actions')}</div>` : '';
    lastKind = r.kind;
    return head + `
      <button class="presult" data-i="${i}" data-active="${i === paletteState.active}">
        <span class="pkind">${r.kind === 'Client' ? '◧' : r.kind === 'Reject' ? '⚑' : r.kind === 'Action' ? '›' : '▤'}</span>
        <span><span class="ptitle">${esc(r.title)}</span><br><span class="psub">${esc(r.sub)}</span></span>
        <span class="pkind">${esc(r.kind)}</span>
      </button>`;
  }).join('');
}

function closePalette() {
  paletteState.open = false;
  const el = $('#palette');
  if (el) el.remove();
  if (lastFocused && lastFocused.focus) lastFocused.focus();
}
