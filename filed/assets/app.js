/* FILED — routing, chrome and the actions that move work through the practice. */

const ROUTES = {
  cover: CoverScreen,
  command: CommandScreen,
  clients: RosterScreen,
  client: ClientScreen,
  documents: DocumentsScreen,
  return: ReturnScreen,
  review: ReviewScreen,
  efile: EfileScreen,
  reject: RejectScreen,
  deadlines: DeadlineScreen,
  portal: PortalScreen,
  team: TeamScreen,
  billing: BillingScreen
};

const NAV = [
  { group: 'Console', items: [
    { hash: '#/command',   label: 'Season command' },
    { hash: '#/deadlines', label: 'Deadline board' },
    { hash: '#/team',      label: 'Team capacity' },
    { hash: '#/billing',   label: 'Billing' }
  ]},
  { group: 'The return', items: [
    { hash: '#/clients',   label: 'Client roster',  count: () => App.state.clients.length },
    { hash: '#/documents', label: 'Document chase', count: () => App.state.clients.filter((c) => outstandingDocs(c).length).length, stage: 'docs' },
    { hash: '#/review',    label: 'Review queue',   count: () => byStage('review').length, stage: 'review' },
    { hash: '#/efile',     label: 'E-file centre',  count: () => readyToTransmit().length + byStage('transmitted').length, stage: 'transmitted' },
    { hash: '#/portal',    label: 'Client portal' }
  ]}
];

/* ── Routing ───────────────────────────────────────────────────────────── */

function parseHash() {
  const raw = location.hash.replace(/^#\/?/, '');
  if (!raw) return { name: 'cover', params: [] };
  const parts = raw.split('/').filter(Boolean);
  return { name: parts[0], params: parts.slice(1) };
}

function route() {
  App.state.route = parseHash();
  App.state.loading = false;
  window.scrollTo({ top: 0 });
  render();
}

function render() {
  const r = App.state.route;
  const screen = ROUTES[r.name] || NotFoundScreen;
  const root = $('#root');

  if (screen.chrome === false) {
    App.firstPaint = false;
    root.innerHTML = screen.render(r.params);
    bindScreen(screen);
    return;
  }

  const crumb = typeof screen.crumb === 'function' ? screen.crumb(r.params) : (screen.crumb || 'Not found');
  const needsLoad = !App.state.seen.includes(r.name) && ROUTES[r.name];

  let content;
  if (needsLoad || App.state.loading) {
    if (!App.state.loading) {
      App.state.loading = true;
      setTimeout(() => {
        if (!App.state.seen.includes(r.name)) App.state.seen.push(r.name);
        App.state.loading = false;
        render();
      }, 420);
    }
    content = loadingView(crumb);
  } else {
    App.firstPaint = !App.state.painted.includes(r.name);
    content = screen.render(r.params);
    if (App.firstPaint) App.state.painted.push(r.name);
  }

  root.innerHTML = shell(crumb, content);
  bindScreen(App.state.loading ? {} : screen);
}

function bindScreen(screen) {
  if (screen && typeof screen.after === 'function') screen.after();
  $$('[data-draft]').forEach((el) => {
    if (el.dataset.bound) return;
    el.dataset.bound = '1';
    el.addEventListener('input', (e) => App.draft(e.target.dataset.draft, e.target.value));
  });
}

/* ── Chrome ────────────────────────────────────────────────────────────── */

function shell(crumb, content) {
  const here = location.hash || '#/command';
  const nav = NAV.map((g) => `
    <div class="nav-group">
      <div class="nav-group-label">${g.group}</div>
      ${g.items.map((it) => {
        const active = here.startsWith(it.hash);
        const n = it.count ? it.count() : null;
        return `<a class="nav-item" href="${it.hash}" ${active ? 'aria-current="page"' : ''}>
          ${it.stage ? `<span class="nav-dot" style="background:var(--st-${it.stage})"></span>` : '<span class="nav-dot" style="background:var(--rule-strong)"></span>'}
          <span>${it.label}</span>
          ${n !== null ? `<span class="nav-count num">${n}</span>` : ''}
        </a>`;
      }).join('')}
    </div>`).join('');

  return `
  <div class="app">
    <nav class="rail" aria-label="Main">
      <div class="brand">
        <span class="brand-mark" aria-hidden="true"></span>
        <span>
          <span class="brand-name">FILED</span>
          <span class="brand-sub">${esc(SEASON.firm)}</span>
        </span>
      </div>
      ${nav}
      <div class="nav-group" style="padding-top:2px">
        <a class="nav-item" href="#/cover"><span class="nav-dot" style="background:transparent"></span><span>Case study</span></a>
      </div>
      <div class="rail-foot">
        <span class="who">Danielle Okonjo, EA</span>
        <span>Practice manager</span>
        <span>EFIN <span class="mono">${SEASON.efin}</span> · PTIN <span class="mono">${SEASON.ptin}</span></span>
        <span>Tax year ${SEASON.taxYear}</span>
      </div>
    </nav>

    <div class="main">
      <header class="seasonbar">
        <button class="btn btn-quiet btn-sm railtoggle" data-action="rail" aria-label="Show navigation">☰</button>
        <div class="crumb">
          <b>${esc(crumb)}</b>
          <span class="sep crumb-tail">·</span>
          <span class="crumb-tail">Thursday 12 March 2026, 7:40am</span>
        </div>
        <button class="kbutton" data-action="palette" aria-label="Open command palette">
          <span class="klabel">Jump to…</span><kbd>⌘</kbd><kbd>K</kbd>
        </button>
        <div class="countdown">
          <span class="countdown-n num">${daysToDeadline}</span>
          <span class="countdown-l">days to 15 April</span>
        </div>
      </header>
      <main id="main">${content}</main>
    </div>
  </div>`;
}

/* ── Actions ───────────────────────────────────────────────────────────── */

const handlers = {
  goto: (arg) => App.go(arg),
  palette: () => openPalette(),
  rail: () => document.body.dataset.rail = document.body.dataset.rail === 'open' ? '' : 'open',
  'open-client': (id) => App.go(`#/client/${id}/overview`),
  'client-tab': (arg) => App.go(`#/client/${arg}`),

  sort(key) {
    const s = App.state.roster.sort;
    s.dir = s.key === key && s.dir === 'asc' ? 'desc' : 'asc';
    s.key = key;
    render();
  },
  view(key) {
    App.state.roster.view = key;
    App.state.roster.selected = [];
    App.state.roster.stage = null;
    render();
  },
  'clear-stage'() { App.state.roster.stage = null; render(); },
  'clear-filters'() {
    App.state.roster = { view: 'all', q: '', sort: { key: 'since', dir: 'asc' }, selected: [], stage: null };
    render();
  },
  'stage-filter'(key) {
    App.state.roster.stage = key;
    App.state.roster.view = 'all';
    App.state.roster.q = '';
    App.go('#/clients');
  },
  select(id) {
    const sel = App.state.roster.selected;
    const i = sel.indexOf(id);
    if (i >= 0) sel.splice(i, 1); else sel.push(id);
    render();
  },
  'select-all'() {
    const shown = rosterRows().map((c) => c.id);
    App.state.roster.selected = App.state.roster.selected.length === shown.length ? [] : shown;
    render();
  },
  'bulk-clear'() { App.state.roster.selected = []; render(); },
  'bulk-remind'() {
    const n = App.state.roster.selected.length;
    const names = App.state.roster.selected.map((id) => App.client(id).name);
    App.state.roster.selected.forEach((id) => logChase(id, 'Portal message', 'Bulk reminder sent from the roster.'));
    App.state.roster.selected = [];
    render();
    App.toast(`Reminder sent to ${n} ${n === 1 ? 'client' : 'clients'}`, names.slice(0, 3).join(', ') + (n > 3 ? ` and ${n - 3} more` : ''));
  },
  'bulk-review'() {
    const ids = App.state.roster.selected.slice();
    const moved = ids.filter((id) => App.client(id).stage === 'prep');
    moved.forEach((id) => App.moveStage(id, 'review', { silent: true }));
    App.state.roster.selected = [];
    render();
    if (!moved.length) App.toast('Nothing moved', 'Only returns in preparation can go to review.');
    else App.toast(`Moved ${moved.length} to review`, ids.length > moved.length ? `${ids.length - moved.length} were not in preparation and stayed put.` : 'Counts updated across the console.');
  },

  'send-message'(id) {
    const c = App.client(id);
    App.draft(`msg::${id}`, '');
    render();
    App.toast('Message sent', `${c.name} — logged against the client record.`);
  },

  'send-chase'(id) {
    const c = App.client(id);
    logChase(id, (CHASE_TEMPLATES[id] || {}).channel || 'Portal message', 'Reminder sent from the chase queue.');
    App.draft(`chase::${id}`, '');
    App.draft(`chase::${id}::subject`, '');
    render();
    App.toast('Reminder sent', `${c.name} — chase logged today.`);
  },

  'doc-received'(arg) {
    const [id, form] = arg.split('::');
    const c = App.client(id);
    App.state.docsIn.push(arg);
    const left = outstandingDocs(c).length;
    if (!left && c.stage === 'docs') {
      App.moveStage(id, 'prep', { silent: true });
      App.toast('Marked received', `${form} was the last item. ${c.name} moved to preparation.`);
    } else {
      App.toast('Marked received', `${form} for ${c.name}. ${left} still outstanding.`);
    }
    render();
  },

  'resolve-diag'(arg) {
    const [id, code] = arg.split('::');
    App.state.resolved.push(arg);
    render();
    const c = App.client(id);
    const d = (c.diagnostics || []).find((x) => x.code === code);
    App.toast(d && d.sev === 'variance' ? 'Explanation added' : 'Diagnostic resolved', `${code} — ${c.name}`);
  },

  'ready-for-review'(id) {
    App.moveStage(id, 'review', { silent: true });
    App.toast('Sent to review', `${App.client(id).name} — now with ${staffName(App.client(id).reviewer)}.`);
  },

  'review-approve'(id) {
    const key = `review::${id}`;
    if (!App.draft(key).trim()) {
      App.state.drafts[`err::${key}`] = 'A reviewer note is required. Write what you changed, or that nothing needed changing.';
      render();
      return;
    }
    const c = App.client(id);
    c.notes.unshift({ on: SEASON.today, by: c.reviewer, text: App.draft(key).trim() });
    App.state.signed[id] = { sent: SEASON.today + 'T09:20:00', signed: null, method: 'Portal e-signature', ip: null };
    delete App.state.drafts[`err::${key}`];
    App.draft(key, '');
    App.moveStage(id, 'signature', { silent: true });
    App.toast('Approved', `Form 8879 sent to ${c.name}. Nothing transmits until they sign it.`);
  },

  'review-return'(id) {
    const key = `review::${id}`;
    if (!App.draft(key).trim()) {
      App.state.drafts[`err::${key}`] = 'A note is required to return a review. The preparer needs to know what to fix.';
      render();
      return;
    }
    const c = App.client(id);
    c.notes.unshift({ on: SEASON.today, by: c.reviewer, text: App.draft(key).trim() });
    delete App.state.drafts[`err::${key}`];
    App.draft(key, '');
    App.moveStage(id, 'prep', { silent: true });
    App.toast('Returned to preparer', `${c.name} — back with ${staffName(c.preparer)} with your note attached.`);
  },

  async 'transmit-ready'() {
    const ready = readyToTransmit();
    if (!ready.length) return;
    const detail = ready.map((c) => `
      <div class="kv"><span class="k">${esc(c.name)}</span><span class="v">${esc(c.entity)} · ${fmt.outcome(c.current.result)}</span></div>`).join('');

    const ok = await confirmAction({
      title: `Transmit ${ready.length} ${ready.length === 1 ? 'return' : 'returns'} to the IRS`,
      body: 'Transmission is final. Once the IRS accepts a return it can only be changed by filing an amended return on Form 1040-X, which takes months to process and costs the client the difference.',
      detail,
      consent: 'I have a signed Form 8879 on file for every return in this batch.',
      confirmLabel: `Transmit ${ready.length} to IRS`,
      tone: 'primary'
    });
    if (!ok) return;

    const batchId = `B-0312-${String.fromCharCode(66 + App.state.batches.filter((b) => b.id.startsWith('B-0312')).length)}`;
    ready.forEach((c) => {
      c.ack = { batch: batchId, transmitted: SEASON.today + 'T09:20:00', accepted: null };
      App.moveStage(c.id, 'transmitted', { silent: true });
    });
    App.state.batches.unshift({
      id: batchId, sent: SEASON.today + 'T09:20:00', count: ready.length,
      returns: ready.map((c) => c.id), state: 'pending',
      note: 'Awaiting acknowledgment.'
    });
    App.state.ackTried = false;
    render();
    App.toast(`Transmitted ${ready.length} to IRS`, `Batch ${batchId} · EFIN ${SEASON.efin}. Acknowledgments usually arrive within 45 minutes.`);
  },

  'check-acks'() {
    /* The Modernized e-File system goes down often enough that a preparer needs to
       be able to tell "not acknowledged yet" from "we could not ask". */
    if (!App.state.ackTried) {
      App.state.ackTried = true;
      App.state.ackServiceDown = true;
      render();
      App.toast('Could not reach the IRS', 'The acknowledgment request timed out. Transmitted returns are unaffected.');
      return;
    }
    App.state.ackServiceDown = false;
    const inFlight = byStage('transmitted');
    inFlight.forEach((c) => {
      c.ack = { ...(c.ack || {}), accepted: SEASON.today + 'T09:34:00' };
      App.moveStage(c.id, 'accepted', { silent: true });
    });
    App.state.batches.forEach((b) => { if (b.state === 'pending') { b.state = 'accepted'; b.note = 'All accepted.'; } });
    render();
    App.toast(`${inFlight.length} ${inFlight.length === 1 ? 'acknowledgment' : 'acknowledgments'} received`, inFlight.map((c) => c.name).join(', ') + ' — accepted.');
  },

  'fix-step'(arg) {
    const key = `fix::${arg}`;
    App.state.drafts[key] = App.state.drafts[key] === 'done' ? '' : 'done';
    render();
  },

  async retransmit(id) {
    const c = App.client(id);
    const ok = await confirmAction({
      title: 'Retransmit to the IRS',
      body: `This sends ${esc(c.name)}’s corrected return back through the same EFIN. The IRS allows five days from a rejection to resubmit, and the original transmission date holds, so this return will not be treated as late.`,
      detail: `<div class="kv"><span class="k">Reject</span><span class="v mono">${c.reject.code}</span></div>
               <div class="kv"><span class="k">Attempt</span><span class="v">${c.reject.attempt + 1}</span></div>
               <div class="kv"><span class="k">Form 8879</span><span class="v">${REJECT_LIBRARY[c.reject.code].retransmit ? 'Existing signature stands' : 'New signature required'}</span></div>`,
      consent: 'The fix path is complete and the return has been re-checked.',
      confirmLabel: 'Retransmit to IRS',
      tone: 'primary'
    });
    if (!ok) return;
    c.ack = { batch: 'B-0312-R', transmitted: SEASON.today + 'T09:26:00', accepted: null };
    c.reject.attempt += 1;
    App.moveStage(id, 'transmitted', { silent: true });
    render();
    App.toast('Retransmitted', `${c.name} — attempt ${c.reject.attempt}, batch B-0312-R.`);
  },

  extend(id)   { moveDeadline(id, SEASON.extendedDue); },
  unextend(id) { moveDeadline(id, SEASON.individualDue); },

  'portal-upload'() {
    const list = App.state.drafts['portal::uploads'] ? JSON.parse(App.state.drafts['portal::uploads']) : [];
    const next = [
      { name: 'Property tax statement 2025.pdf', size: '221 KB' },
      { name: 'Charitable receipts bundle.pdf', size: '612 KB' },
      { name: 'IRA year-end statement.pdf', size: '188 KB' }
    ][list.length % 3];
    list.push({ ...next, on: SEASON.today + 'T09:22:00', state: 'accepted' });
    App.state.drafts['portal::uploads'] = JSON.stringify(list);
    render();
    App.toast('Document added', `${next.name} is with your preparer.`);
  },

  async 'portal-sign'() {
    const c = App.client(PORTAL.client);
    const name = App.draft('portal::name').trim();
    const ok = await confirmAction({
      title: 'Sign Form 8879',
      body: `Signing authorises Okonjo &amp; Vance Tax Group to file your 2025 federal return as shown. A filed return can only be changed by amending it.`,
      detail: `<div class="kv"><span class="k">Signing as</span><span class="v">${esc(name)}</span></div>
               <div class="kv"><span class="k">Balance due</span><span class="v num">${fmt.money(4106)} by 15 April</span></div>`,
      consent: 'I have reviewed the return and the figures are correct to the best of my knowledge.',
      confirmLabel: 'Sign Form 8879',
      tone: 'primary'
    });
    if (!ok) return;
    App.state.signed[c.id] = { sent: App.state.signed[c.id].sent, signed: SEASON.today + 'T09:24:00', method: 'Portal e-signature', ip: '73.71.204.19' };
    render();
    App.toast('Signed', `Form 8879 for ${c.name} is on file. The return is now in the transmit queue.`);
  },

  'invoice-paid'(no) {
    const i = App.state.invoices.find((x) => x.no === no);
    i.paid = i.billed;
    i.status = 'paid';
    render();
    App.toast('Payment recorded', `${no} — ${fmt.money(i.billed)} settled in full.`);
  },

  async 'invoice-writeoff'(no) {
    const i = App.state.invoices.find((x) => x.no === no);
    const amount = i.billed - i.paid;
    const c = App.client(i.client);
    const ok = await confirmAction({
      title: `Write off ${fmt.money(amount)}`,
      body: `This closes ${no} at the ${fmt.money(i.paid)} already collected and gives up the remaining ${fmt.money(amount)} from ${esc(c.name)}. It reduces this season’s realisation and cannot be reversed once posted.`,
      detail: `<div class="kv"><span class="k">Standard fee</span><span class="v num">${fmt.money(i.standard)}</span></div>
               <div class="kv"><span class="k">Collected</span><span class="v num">${fmt.money(i.paid)}</span></div>
               <div class="kv"><span class="k">Writing off</span><span class="v num">${fmt.money(amount)}</span></div>`,
      consent: 'I have the partner approval this write-off needs.',
      confirmLabel: `Write off ${fmt.money(amount)}`,
      tone: 'danger'
    });
    if (!ok) return;
    i.writeOff += amount;
    i.billed = i.paid;
    i.status = 'paid';
    i.note = i.note || `Written off ${fmt.dateFull(SEASON.today)} by Danielle Okonjo.`;
    render();
    App.toast(`Written off ${fmt.money(amount)}`, `${no} — realisation updated.`);
  }
};

function logChase(id, via, note) {
  if (!CHASE_LOG[id]) CHASE_LOG[id] = [];
  CHASE_LOG[id].push({ on: SEASON.today + 'T09:18:00', by: 'do', via, note });
}

/* ── Wiring ────────────────────────────────────────────────────────────── */

document.addEventListener('click', (e) => {
  const link = e.target.closest('a[href^="#/"]');
  if (link) { document.body.dataset.rail = ''; }

  const el = e.target.closest('[data-action]');
  if (!el) return;
  const action = el.dataset.action;
  if (!handlers[action]) return;
  if (el.tagName !== 'SELECT') {
    e.preventDefault();
    handlers[action](el.dataset.arg);
  }
});

document.addEventListener('change', (e) => {
  const el = e.target.closest('[data-action="reassign"]');
  if (!el) return;
  const c = App.client(el.dataset.arg);
  const to = el.value;
  c.preparer = to;
  render();
  App.toast('Reassigned', `${c.name} is now with ${staffName(to)}.`);
});

document.addEventListener('keydown', (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault();
    if (paletteState.open) closePalette(); else openPalette();
    return;
  }
  if (e.key === 'Enter' || e.key === ' ') {
    const el = document.activeElement;
    if (el && el.hasAttribute('data-action') && el.getAttribute('role') === 'link') {
      e.preventDefault();
      handlers[el.dataset.action](el.dataset.arg);
    }
  }
});

window.addEventListener('hashchange', route);

App.state.painted = [];
App.state.roster.stage = null;
App.state.ackTried = false;
route();
