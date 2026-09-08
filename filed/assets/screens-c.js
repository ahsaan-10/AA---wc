/* FILED — screens: deadline board, client portal preview, team capacity,
   billing and realisation, plus the not-found and loading states. */

/* ── 10. Deadline board ────────────────────────────────────────────────── */

const BOARD_COLUMNS = [
  { key: SEASON.businessDue,   when: 'Monday 16 March',   what: 'Form 1065 and 1120-S', note: 'March 15 is a Sunday this year, so the partnership and S-corp deadline moves to the Monday.', urgent: true },
  { key: SEASON.individualDue, when: 'Wednesday 15 April', what: 'Form 1040',            note: 'Individual returns, and the last day to file Form 4868.' },
  { key: SEASON.extendedDue,   when: 'Thursday 15 October', what: 'Extended on Form 4868', note: 'Filing extended. Tax owed was still due on 15 April.' },
  { key: 'done',               when: 'Filed',              what: 'Accepted by the IRS',   note: 'Off the board. Nothing here needs a date.' }
];

const DeadlineScreen = {
  crumb: 'Deadline board',
  render() {
    const columns = BOARD_COLUMNS.map((col) => {
      const cards = App.state.clients.filter((c) =>
        col.key === 'done' ? ['accepted', 'invoiced'].includes(c.stage)
                           : c.due === col.key && !['accepted', 'invoiced'].includes(c.stage));
      return { ...col, cards };
    });

    return `
    <div class="view">
      <div class="view-head">
        <div>
          <h1>Deadline board</h1>
          <p>Every open return by the date it is actually due. Drag a card to a different column, or use the buttons on the card — either one files or withdraws the extension and updates the client record.</p>
        </div>
        <div class="spacer"></div>
        <div class="countdown" style="border:0; padding:0">
          <span class="countdown-n num">${daysToDeadline}</span>
          <span class="countdown-l">days to 15 April</span>
        </div>
      </div>

      <div class="board">
        ${columns.map((col) => `
          <div class="boardcol" data-col="${col.key}" data-urgent="${!!col.urgent}">
            <div class="boardcol-head">
              <div class="when">${esc(col.when)}</div>
              <div class="what">${esc(col.what)} <span class="panel-note num">· ${col.cards.length}</span></div>
              <p class="panel-note" style="margin-top:4px">${esc(col.note)}</p>
            </div>
            <div class="boardcards">
              ${col.cards.length ? col.cards.map((c) => `
                <div class="bcard" draggable="${col.key === 'done' ? 'false' : 'true'}" data-id="${c.id}" data-stage="${c.stage}" style="--sc:var(--st-${c.stage === 'docs' ? 'docs' : c.stage})">
                  <div class="bname" data-action="open-client" data-arg="${c.id}" style="cursor:pointer">${esc(c.name)}</div>
                  <div class="bmeta">${esc(c.entity)} · ${esc(staffById(c.preparer).initials)} ${pill(c.stage)}</div>
                  ${col.key === 'done' ? '' : `
                  <div class="move">
                    ${col.key !== SEASON.extendedDue
                      ? `<button class="btn btn-sm btn-quiet" data-action="extend" data-arg="${c.id}">File 4868</button>`
                      : `<button class="btn btn-sm btn-quiet" data-action="unextend" data-arg="${c.id}">Move to 15 April</button>`}
                  </div>`}
                </div>`).join('')
              : `<div class="empty" style="padding:22px 12px">
                   <p style="font-size:12.5px">${col.key === SEASON.extendedDue ? 'Nothing extended yet. Drag a return here to file Form 4868.' : 'Nothing due on this date.'}</p>
                 </div>`}
            </div>
          </div>`).join('')}
      </div>
    </div>`;
  },

  after() {
    let dragged = null;
    $$('.bcard[draggable="true"]').forEach((card) => {
      card.addEventListener('dragstart', (e) => {
        dragged = card.dataset.id;
        card.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', dragged);
      });
      card.addEventListener('dragend', () => card.classList.remove('dragging'));
    });
    $$('.boardcol').forEach((col) => {
      col.addEventListener('dragover', (e) => { e.preventDefault(); col.classList.add('drop'); });
      col.addEventListener('dragleave', () => col.classList.remove('drop'));
      col.addEventListener('drop', (e) => {
        e.preventDefault();
        col.classList.remove('drop');
        const id = e.dataTransfer.getData('text/plain') || dragged;
        const target = col.dataset.col;
        if (!id || target === 'done') return;
        moveDeadline(id, target);
      });
    });
  }
};

function moveDeadline(id, due) {
  const c = App.client(id);
  if (!c || c.due === due) return;
  const wasExtended = due === SEASON.extendedDue;
  c.due = due;
  render();
  if (wasExtended) {
    App.toast('Filed Form 4868', `${c.name} — filing extended to 15 October. Any tax owed was still due 15 April.`);
  } else {
    App.toast('Moved to ' + fmt.dateFull(due), `${c.name} — extension withdrawn from the board.`);
  }
}

/* ── 11. Client portal preview ─────────────────────────────────────────── */

const PortalScreen = {
  crumb: 'Client portal preview',
  render() {
    const c = App.client(PORTAL.client);
    const sig = signatureOf(c.id);
    const uploads = PORTAL.uploads.concat(App.state.drafts['portal::uploads'] ? JSON.parse(App.state.drafts['portal::uploads']) : []);
    const typed = App.draft('portal::name');

    return `
    <div class="view">
      <div class="view-head">
        <div>
          <h1>Client portal preview</h1>
          <p>The same product from the taxpayer’s side, at the width they actually use it. Three jobs only: send documents, read the result, sign Form 8879. Signing here puts the return in the transmit queue on the e-file centre.</p>
        </div>
      </div>

      <div class="grid" style="grid-template-columns:auto minmax(0,1fr); gap:28px; align-items:start">
        <div class="phone">
          <div class="phone-status"><span>9:41</span><span>Okonjo &amp; Vance</span></div>
          <div class="phone-body">
            <div class="phone-head">
              <span class="brand-mark" style="width:17px;height:20px"></span>
              <div>
                <div style="font-weight:600; font-size:14px">Your 2025 return</div>
                <div class="panel-note">${esc(c.name)}</div>
              </div>
            </div>

            <div>
              <div class="row" style="justify-content:space-between">
                <h3 style="font-size:13.5px">Documents</h3>
                <span class="panel-note">${uploads.length} sent</span>
              </div>
              ${uploads.map((u) => `
                <div class="filerow">
                  <span class="tick">✓</span>
                  <span style="flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap">${esc(u.name)}</span>
                  <span class="panel-note">${esc(u.size)}</span>
                </div>`).join('')}
              <div class="upload" style="margin-top:10px">
                Photograph or upload a document
                <div style="margin-top:8px"><button class="btn btn-sm" data-action="portal-upload">Add a document</button></div>
              </div>
            </div>

            <div>
              <h3 style="font-size:13.5px; margin-bottom:6px">Your return</h3>
              ${PORTAL.summary.map((s) => `
                <div class="kv">
                  <span class="k">${esc(s.label)}</span>
                  <span class="v num" ${s.emphasis ? 'style="font-size:15px"' : ''}>${fmt.money(s.value)}</span>
                </div>`).join('')}
              <p class="panel-note" style="margin-top:8px">Payable to the United States Treasury by 15 April. We can schedule the debit for that date.</p>
            </div>

            <div>
              <h3 style="font-size:13.5px; margin-bottom:6px">Form 8879</h3>
              ${sig && sig.signed ? `
                <div class="banner" data-tone="info">
                  <span class="sev"></span>
                  <div><b>Signed</b><p>${fmt.stamp(sig.signed)}. Your preparer can now file the return.</p></div>
                </div>`
              : `
                <div class="signature-pad">
                  <p class="panel-note">By signing you authorise Okonjo &amp; Vance Tax Group to transmit your 2025 federal return to the IRS. Type your full name as it appears on the return.</p>
                  <div class="signature-line">${esc(typed) || '&nbsp;'}</div>
                  <input type="text" id="signname" data-draft="portal::name" value="${esc(typed)}" placeholder="Full name" aria-label="Type your full name to sign">
                  <button class="btn btn-primary" data-action="portal-sign" ${typed.trim().length > 3 ? '' : 'disabled'}>Sign Form 8879</button>
                </div>`}
            </div>
          </div>
        </div>

        <div class="stack">
          <section class="panel">
            <div class="panel-head"><h2>Why the portal only does three things</h2></div>
            <div class="panel-body stack" style="gap:12px">
              <div class="note"><p class="note-text">A taxpayer opens this two or three times a year, usually on a phone, usually to answer a request. Anything beyond sending documents, reading the result and signing is our work leaking onto them.</p></div>
              <div class="note"><p class="note-text">The balance due is stated with the date and the payment method, because that is the only number in this screen anyone actually reads.</p></div>
              <div class="note"><p class="note-text">Signature is the one irreversible act on the client’s side, so it is a typed name against explicit authorisation text rather than a checkbox.</p></div>
            </div>
          </section>

          <section class="panel">
            <div class="panel-head"><h2>What signing does on our side</h2></div>
            <div class="panel-body">
              <div class="kv"><span class="k">Stage</span><span class="v">${stageMeta(c.stage).label}</span></div>
              <div class="kv"><span class="k">Form 8879 sent</span><span class="v">${sig ? fmt.stamp(sig.sent) : '—'}</span></div>
              <div class="kv"><span class="k">Signed</span><span class="v">${sig && sig.signed ? fmt.stamp(sig.signed) : 'Not yet'}</span></div>
              <div class="kv"><span class="k">Ready to transmit</span><span class="v">${readyToTransmit().length} ${readyToTransmit().length === 1 ? 'return' : 'returns'}</span></div>
              <div class="row" style="margin-top:12px">
                <button class="btn" data-action="goto" data-arg="#/efile">Open the e-file centre</button>
                <button class="btn btn-quiet" data-action="open-client" data-arg="${c.id}">Client record</button>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>`;
  },

  after() {
    const n = $('#signname');
    if (n) n.addEventListener('input', (e) => {
      App.draft('portal::name', e.target.value);
      const pos = e.target.selectionStart;
      render();
      const next = $('#signname');
      if (next) { next.focus(); next.setSelectionRange(pos, pos); }
    });
  }
};

/* ── 12. Team capacity ─────────────────────────────────────────────────── */

const TeamScreen = {
  crumb: 'Team capacity',
  render() {
    const openOf = (id) => App.state.clients.filter((c) => c.preparer === id && !['accepted', 'invoiced'].includes(c.stage));

    const rows = STAFF.map((s) => {
      const load = openOf(s.id);
      const util = (s.hoursUsed / s.hoursCap) * 100;
      const blocked = load.filter((c) => outstandingDocs(c).length || c.stage === 'rejected').length;
      return `
      <tr>
        <td><div class="name">${esc(s.name)}, ${esc(s.cred)}</div><div class="sub">${esc(s.role)}</div></td>
        <td class="r num">${load.length}</td>
        <td class="r num">${blocked}</td>
        <td class="r num">${s.hoursUsed}</td>
        <td class="r num">${s.hoursCap}</td>
        <td style="min-width:180px">
          <span class="capbar" data-over="${util > 90}" title="${fmt.pct(util)} committed"><span style="width:${Math.min(util, 100)}%"></span></span>
        </td>
        <td class="r num">${fmt.pct(util)}</td>
      </tr>`;
    }).join('');

    const work = App.state.clients
      .filter((c) => !['accepted', 'invoiced'].includes(c.stage))
      .sort((a, b) => a.due.localeCompare(b.due) || b.fee - a.fee)
      .map((c) => `
      <tr>
        <td class="clickable" data-action="open-client" data-arg="${c.id}">
          <div class="name">${esc(c.name)}</div>
          <div class="sub">${esc(c.entity)} · due ${fmt.date(c.due)}</div>
        </td>
        <td>${pill(c.stage)}</td>
        <td class="r num">${stuckDays(c)}</td>
        <td style="min-width:210px">
          <select data-action="reassign" data-arg="${c.id}" aria-label="Preparer for ${esc(c.name)}">
            ${STAFF.map((s) => `<option value="${s.id}" ${c.preparer === s.id ? 'selected' : ''}>${esc(s.name)}</option>`).join('')}
          </select>
        </td>
        <td>${esc(staffName(c.reviewer))}</td>
      </tr>`).join('');

    const over = STAFF.filter((s) => (s.hoursUsed / s.hoursCap) > 0.9);

    return `
    <div class="view">
      <div class="view-head">
        <div>
          <h1>Team capacity</h1>
          <p>Hours committed against hours available this week, and what each preparer is actually holding. Blocked means the return cannot move without something arriving.</p>
        </div>
      </div>

      <div class="stack">
        ${over.length ? `
        <div class="banner" data-tone="warn">
          <span class="sev"></span>
          <div>
            <b>${over.length === 1 ? `${over[0].name} is past 90% committed` : `${over.length} preparers are past 90% committed`}</b>
            <p>${esc(over.map((s) => s.name.split(' ')[0]).join(', '))} ${over.length === 1 ? 'has' : 'have'} more hours booked than the week holds. Grace Sung and Renato Almeida have room — reassigning below moves the work everywhere it appears.</p>
          </div>
        </div>` : ''}

        <section class="panel">
          <div class="panel-head"><h2>This week</h2><span class="spacer"></span><span class="panel-note">Marker at 90%</span></div>
          <div class="tablewrap"><table class="ledger">
            <thead><tr><th>Preparer</th><th class="r">Open</th><th class="r">Blocked</th><th class="r">Hours used</th><th class="r">Available</th><th>Utilisation</th><th class="r">%</th></tr></thead>
            <tbody>${rows}</tbody>
          </table></div>
        </section>

        <section class="panel">
          <div class="panel-head"><h2>Work in hand</h2><span class="spacer"></span><span class="panel-note">Change a preparer to reassign</span></div>
          <div class="tablewrap"><table class="ledger">
            <thead><tr><th>Return</th><th>Stage</th><th class="r">Days in stage</th><th>Preparer</th><th>Reviewer</th></tr></thead>
            <tbody>${work}</tbody>
          </table></div>
        </section>
      </div>
    </div>`;
  }
};

/* ── 13. Billing and realisation ───────────────────────────────────────── */

const BillingScreen = {
  crumb: 'Billing',
  render() {
    const inv = App.state.invoices;
    const billed = inv.reduce((n, i) => n + i.billed, 0);
    const standard = inv.reduce((n, i) => n + i.standard, 0);
    const collected = inv.reduce((n, i) => n + i.paid, 0);
    const written = inv.reduce((n, i) => n + i.writeOff, 0);
    const realisation = (billed / standard) * 100;

    const byType = ['1040', '1120-S', '1065'].map((t) => {
      const set = App.state.clients.filter((c) => c.entity === t);
      const avg = set.reduce((n, c) => n + c.fee, 0) / set.length;
      return { t, avg, n: set.length };
    });
    const maxAvg = Math.max(...byType.map((b) => b.avg));

    const rows = inv.map((i) => {
      const c = App.client(i.client);
      const age = fmt.days(i.issued);
      return `
      <tr>
        <td class="mono">${i.no}</td>
        <td class="clickable" data-action="open-client" data-arg="${i.client}">
          <div class="name">${esc(c.name)}</div>
          <div class="sub">${esc(c.entity)} · ${esc(i.terms)}</div>
        </td>
        <td class="r">${fmt.date(i.issued)}<div class="sub">${age} ${age === 1 ? 'day' : 'days'}</div></td>
        <td class="r num">${fmt.money(i.standard)}</td>
        <td class="r num">${fmt.money(i.billed)}</td>
        <td class="r num">${i.writeOff ? fmt.money(i.writeOff) : '—'}</td>
        <td class="r num">${fmt.money(i.paid)}</td>
        <td>${invoiceStatusPill(i.status)}</td>
        <td class="tight r">
          ${i.status === 'paid' ? '<span class="panel-note">Settled</span>' : `
            <button class="btn btn-sm" data-action="invoice-paid" data-arg="${i.no}">Record payment</button>
            <button class="btn btn-sm btn-quiet" data-action="invoice-writeoff" data-arg="${i.no}">Write off</button>`}
        </td>
      </tr>`;
    }).join('');

    return `
    <div class="view">
      <div class="view-head">
        <div>
          <h1>Billing and realisation</h1>
          <p>What the schedule says a return is worth, what we actually billed, and what came back. Realisation is the gap between the first two.</p>
        </div>
      </div>

      <div class="stack">
        <div class="panel">
          <dl class="metrics">
            <div class="metric"><dt>Billed, open invoices</dt><dd class="num">${fmt.money(billed)}</dd></div>
            <div class="metric"><dt>Collected</dt><dd class="num">${fmt.money(collected)}<span class="foot"> of ${fmt.money(billed)}</span></dd></div>
            <div class="metric"><dt>Written off</dt><dd class="num">${fmt.money(written)}</dd></div>
            <div class="metric"><dt>Realisation</dt><dd class="num">${realisation.toFixed(1)}%</dd></div>
            <div class="metric"><dt>Overdue</dt><dd class="num">${fmt.money(inv.filter((i) => i.status === 'overdue').reduce((n, i) => n + (i.billed - i.paid), 0))}</dd></div>
          </dl>
        </div>

        <div class="grid cols-2">
          <section class="panel">
            <div class="panel-head"><h2>Invoices</h2><span class="spacer"></span><span class="panel-note">${inv.length} open this fortnight</span></div>
            <div class="tablewrap"><table class="ledger">
              <thead><tr><th>Invoice</th><th>Client</th><th class="r">Issued</th><th class="r">Standard</th><th class="r">Billed</th><th class="r">Off</th><th class="r">Paid</th><th>Status</th><th></th></tr></thead>
              <tbody>${rows}</tbody>
            </table></div>
          </section>

          <div class="stack">
            <section class="panel">
              <div class="panel-head"><h2>Average fee by return type</h2></div>
              <div class="panel-body">
                <table class="compare">
                  <thead><tr><th>Return</th><th class="r">Average fee</th><th style="width:44%"></th><th class="r">Returns</th></tr></thead>
                  <tbody>
                    ${byType.map((b) => `
                      <tr>
                        <td>${esc(b.t)}</td>
                        <td class="r num">${fmt.money(b.avg)}</td>
                        <td><span class="bar" style="--sc:var(--st-invoiced)"><span style="width:${(b.avg / maxAvg) * 100}%"></span></span></td>
                        <td class="r num">${b.n}</td>
                      </tr>`).join('')}
                  </tbody>
                </table>
                <p class="panel-note" style="margin-top:10px">Business returns carry the practice. A 1065 at ${fmt.money(byType[2].avg)} is roughly three 1040s, and it lands in the two weeks before 16 March.</p>
              </div>
            </section>

            <section class="panel">
              <div class="panel-head"><h2>Write-offs</h2></div>
              <div class="panel-body stack" style="gap:12px">
                ${inv.filter((i) => i.writeOff).map((i) => `
                  <div class="note">
                    <div class="note-meta">${i.no} · ${esc(App.client(i.client).name)} · ${fmt.money(i.writeOff)}</div>
                    <p class="note-text">${esc(i.note)}</p>
                  </div>`).join('') || '<p class="panel-note">Nothing written off this fortnight.</p>'}
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>`;
  }
};

/* ── Not found ─────────────────────────────────────────────────────────── */

const NotFoundScreen = {
  crumb: 'Not found',
  render() {
    return `
    <div class="view">
      <section class="panel">
        <div class="empty">
          <div class="empty-mark"></div>
          <h3>That record is not in this season</h3>
          <p>The link may point at a return from a prior year, or at a client who has been archived. Nothing has been lost — prior seasons are read-only and open from the client record.</p>
          <div class="row" style="justify-content:center">
            <button class="btn btn-primary" data-action="goto" data-arg="#/command">Back to season command</button>
            <button class="btn" data-action="palette">Search for a client</button>
          </div>
        </div>
      </section>
    </div>`;
  }
};

/* ── Loading ───────────────────────────────────────────────────────────── */

function loadingView(label) {
  const row = `<div class="skelrow">
    <div class="skel" style="width:80%"></div><div class="skel" style="width:52%"></div>
    <div class="skel" style="width:64%"></div><div class="skel" style="width:40%"></div><div class="skel" style="width:46%"></div>
  </div>`;
  return `
  <div class="view" aria-busy="true">
    <div class="view-head">
      <div>
        <h1>${esc(label)}</h1>
        <p>Reading the season file…</p>
      </div>
    </div>
    <section class="panel">
      <div class="toolbar"><div class="skel" style="width:210px; height:26px"></div><div class="skel" style="width:170px; height:26px"></div></div>
      ${row.repeat(8)}
    </section>
    <p class="sr" role="status">Loading ${esc(label)}</p>
  </div>`;
}
