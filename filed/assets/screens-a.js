/* FILED — screens: case study cover, season command, roster, client record. */

/* ── 1. Case study cover ───────────────────────────────────────────────── */

const CoverScreen = {
  chrome: false,
  render() {
    const chain = ['Intake', 'Documents', 'Preparation', 'Review', 'Signature', 'Transmitted', 'Accepted', 'Invoiced']
      .map((s) => `<span class="step">${s}</span>`).join('<span class="arr">→</span>');

    return `
    <div class="cover">
      <div class="cover-inner">
        <div class="row" style="gap:10px; margin-bottom:34px">
          <span class="brand-mark" style="width:26px;height:30px"></span>
          <span class="brand-name" style="font-size:17px">FILED</span>
        </div>

        <h1>Never lose a return.<br>Never miss a deadline.</h1>
        <p class="lede">An operations console for a small US tax practice — eight preparers, about 600 returns a season, one deadline that does not move. Fourteen screens covering the return from intake to IRS acknowledgment, scoped from a one-line premise and built as working software rather than flat comps.</p>

        <div class="row" style="margin-top:30px; gap:10px">
          <a class="btn btn-primary" href="#/command" style="text-decoration:none; padding:10px 18px">Open the console</a>
          <a class="btn" href="#/reject/DUA-0409" style="text-decoration:none; padding:10px 18px">Start at a rejected return</a>
        </div>

        <div class="cover-rule"></div>

        <div class="cover-meta">
          <div><span class="mk">Product</span><span>FILED, tax practice operations</span></div>
          <div><span class="mk">Screens</span><span>14, all clickable and connected</span></div>
          <div><span class="mk">Season modelled</span><span>Tax year 2025, today is March 12</span></div>
          <div><span class="mk">Scope, design, build</span><span>Solo</span></div>
        </div>

        <div class="cover-rule"></div>

        <h2 style="margin-bottom:10px">The workflow is the product</h2>
        <p style="color:var(--text-muted); max-width:66ch; margin-bottom:14px">Every screen exists to serve one stage of a return’s life. Nothing was added because a dashboard usually has one.</p>
        <div class="stagemap">${chain}</div>

        <div class="cover-rule"></div>

        <div class="decisions">
          <div class="decision">
            <div class="dk">Decision one</div>
            <div>
              <h3>Colour means status, or it is removed</h3>
              <p><b>The problem.</b> A workflow tool invites decoration — a tinted card here, a coloured heading there — and by the fourth screen colour no longer tells you anything.</p>
              <p><b>The resolution.</b> Nine hues, one per stage, and no other colour in the product. Ink, paper and rule carry all the structure. The result is that a stage reads at a glance from any table, any board column, any row in the reject lane, without a legend.</p>
            </div>
          </div>

          <div class="decision">
            <div class="dk">Decision two</div>
            <div>
              <h3>Spend the boldness once, on the folder</h3>
              <p><b>The problem.</b> Dense professional tools flatten into undifferentiated grey, and the screen a practice manager lives in becomes the least memorable one.</p>
              <p><b>The resolution.</b> The client record is built as a physical folder — cut tabs, angled and overlapping, fused into the panel below. It is the only flourish in the product. Everything around it is deliberately quiet so that it lands.</p>
            </div>
          </div>

          <div class="decision">
            <div class="dk">Decision three</div>
            <div>
              <h3>Data that survives a preparer reading it</h3>
              <p><b>The problem.</b> Mock data breaks a demo in about four seconds. Round numbers, John Doe, a Schedule C client with no business name.</p>
              <p><b>The resolution.</b> Genuine IRS reject codes with their real meanings — <span class="mono">IND-031-04</span>, <span class="mono">R0000-500-01</span>, <span class="mono">F1040-164-01</span>. Real form designations, unrounded money, masked SSNs, and internal notes written the way colleagues actually write to each other. Partnership returns are dated Monday March 16 because March 15 falls on a Sunday in 2026. I hold an IRS AFSP credential with an active EFIN and PTIN, which is why this reads as a practice rather than as a theme.</p>
            </div>
          </div>
        </div>

        <div class="cover-rule"></div>

        <div class="row" style="justify-content:space-between; align-items:flex-end">
          <p style="color:var(--text-faint); font-size:13px; max-width:52ch">Scoped, designed and built solo. Sorting, filters, stage moves, transmission and the command palette all work — moving a return updates every count that reads from it.</p>
          <a class="btn btn-primary" href="#/command" style="text-decoration:none; padding:10px 18px">Open the console</a>
        </div>
      </div>
    </div>`;
  }
};

/* ── 2. Season command ─────────────────────────────────────────────────── */

const CommandScreen = {
  crumb: 'Season command',
  render() {
    const counts = stageCounts();
    const open = App.state.clients.filter((c) => !['accepted', 'invoiced'].includes(c.stage)).length;
    const max = Math.max(...Object.values(counts), 1);
    const ready = readyToTransmit().length;
    const rejected = counts.rejected;
    const outstandingCount = App.state.clients.reduce((n, c) => n + outstandingDocs(c).length, 0);

    const stageRows = STAGES.map((s) => `
      <button class="stagerow" data-stage="${s.key}" data-action="stage-filter" data-arg="${s.key}"
              title="${counts[s.key]} ${counts[s.key] === 1 ? 'return' : 'returns'} in ${s.label.toLowerCase()}">
        <span class="label">${pill(s.key)}</span>
        <span class="count num">${counts[s.key]}</span>
        <span class="bar"><span style="width:${(counts[s.key] / max) * 100}%; animation-delay:${STAGES.indexOf(s) * 45}ms"></span></span>
      </button>`).join('');

    const risk = AT_RISK.map((r) => {
      const c = App.client(r.client);
      return `
      <div class="risk" data-sev="${r.severity}" data-action="open-client" data-arg="${c.id}" tabindex="0" role="link">
        <div class="risk-strip">
          <div class="sev"></div>
          <div>
            <div class="risk-top">
              <span class="risk-name">${esc(c.name)}</span>
              ${pill(c.stage)}
              <span class="panel-note">${esc(staffById(r.owner).name)} · ${r.age} ${r.age === 1 ? 'day' : 'days'} in stage · due ${fmt.date(c.due)}</span>
            </div>
            <p class="risk-why">${esc(r.reason)}</p>
          </div>
        </div>
      </div>`;
    }).join('');

    const capacity = STAFF.map((s) => {
      const load = App.state.clients.filter((c) => c.preparer === s.id && !['accepted', 'invoiced'].includes(c.stage)).length;
      const util = (s.hoursUsed / s.hoursCap) * 100;
      return `
      <div class="caprow">
        <span>${esc(s.name.split(' ')[0])} ${esc(s.name.split(' ').slice(1).join(' '))}</span>
        <span class="capbar" data-over="${util > 90}" title="${s.hoursUsed} of ${s.hoursCap} hours committed this week">
          <span style="width:${Math.min(util, 100)}%"></span>
        </span>
        <span class="panel-note num" style="text-align:right">${fmt.pct(util)} · ${load}</span>
      </div>`;
    }).join('');

    const feed = ACTIVITY.map((a) => `
      <div class="feeditem">
        <time datetime="${a.at}">${a.at.slice(0, 10) === SEASON.today ? fmt.time(a.at) : fmt.date(a.at.slice(0, 10)) + ' ' + fmt.time(a.at)}</time>
        <div>${esc(a.text)}${a.by ? ` <span class="panel-note">${esc(staffById(a.by).initials)}</span>` : ''}</div>
      </div>`).join('');

    return `
    <div class="view">
      <div class="view-head">
        <div>
          <h1>Good morning, Danielle</h1>
          <p>Thursday 12 March. ${rejected} ${rejected === 1 ? 'return is' : 'returns are'} back from the IRS, ${ready} ${ready === 1 ? 'is' : 'are'} signed and waiting to transmit, and the partnership deadline is Monday.</p>
        </div>
        <div class="spacer"></div>
        <button class="btn btn-primary" data-action="goto" data-arg="#/efile">Transmit signed returns</button>
      </div>

      <div class="stack">
        <div class="panel">
          <dl class="metrics">
            <div class="metric"><dt>Open returns</dt><dd class="num">${open}</dd></div>
            <div class="metric"><dt>At risk today</dt><dd class="num">${AT_RISK.length}</dd></div>
            <div class="metric"><dt>Documents outstanding</dt><dd class="num">${outstandingCount}</dd></div>
            <div class="metric"><dt>Signed, ready to transmit</dt><dd class="num">${ready}</dd></div>
            <div class="metric"><dt>Accepted this season</dt><dd class="num">${SEASON.closedToDate.accepted + byStage('accepted').length + byStage('invoiced').length}<span class="foot"> of ${SEASON.seasonTotal}</span></dd></div>
          </dl>
        </div>

        <div class="grid cols-2">
          <div class="stack">
            <section class="panel">
              <div class="panel-head">
                <h2>Where the season sits</h2>
                <span class="spacer"></span>
                <span class="panel-note">Select a stage to filter the roster</span>
              </div>
              <div class="stageledger ${App.state.seen.includes('command') ? '' : 'animate'}">${stageRows}</div>
            </section>

            <section class="panel">
              <div class="panel-head">
                <h2>At risk today</h2>
                <span class="spacer"></span>
                <span class="panel-note">Six returns, each stuck for a different reason</span>
              </div>
              ${risk}
            </section>
          </div>

          <div class="stack">
            <section class="panel">
              <div class="panel-head">
                <h2>Preparer capacity</h2>
                <span class="spacer"></span>
                <button class="btn btn-quiet btn-sm" data-action="goto" data-arg="#/team">Reassign</button>
              </div>
              <div class="panel-body"><div class="capacity">${capacity}</div>
                <p class="panel-note" style="margin-top:12px">Hours committed against hours available this week. The marker sits at 90%; past it, work needs to move.</p>
              </div>
            </section>

            <section class="panel">
              <div class="panel-head"><h2>Since yesterday</h2></div>
              <div class="feed">${feed}</div>
            </section>
          </div>
        </div>
      </div>
    </div>`;
  }
};

/* ── 3. Client roster ──────────────────────────────────────────────────── */

const VIEWS = [
  { key: 'all',    label: 'All' },
  { key: 'mine',   label: 'My clients' },
  { key: 'stuck',  label: 'Stuck 5+ days' },
  { key: 'new',    label: 'New this season' }
];

function rosterRows() {
  const { view, q, sort } = App.state.roster;
  let rows = App.state.clients.slice();

  if (App.state.roster.stage) rows = rows.filter((c) => c.stage === App.state.roster.stage);
  if (view === 'mine')  rows = rows.filter((c) => c.preparer === 'do' || c.reviewer === 'do');
  if (view === 'stuck') rows = rows.filter((c) => stuckDays(c) >= 5);
  if (view === 'new')   rows = rows.filter((c) => c.since_year === 2026);

  const term = q.trim().toLowerCase();
  if (term) {
    rows = rows.filter((c) => [c.name, c.id, c.occupation, c.business, c.entity, stageMeta(c.stage).label]
      .join(' ').toLowerCase().includes(term));
  }

  const dir = sort.dir === 'asc' ? 1 : -1;
  const val = (c) => ({
    name: c.name.replace(/^(Mr|Ms) /, ''),
    id: c.id,
    entity: c.entity,
    stage: STAGES.findIndex((s) => s.key === c.stage),
    preparer: staffName(c.preparer),
    due: c.due,
    since: -stuckDays(c),
    fee: c.fee
  }[sort.key]);

  rows.sort((a, b) => {
    const x = val(a), y = val(b);
    if (x === y) return a.name.localeCompare(b.name);
    return (x > y ? 1 : -1) * dir;
  });
  return rows;
}

const RosterScreen = {
  crumb: 'Client roster',
  render() {
    const rows = rosterRows();
    const sel = App.state.roster.selected;
    const { sort } = App.state.roster;
    const arrow = (k) => sort.key === k ? `<span class="arrow">${sort.dir === 'asc' ? '▲' : '▼'}</span>` : '';
    const th = (k, label, cls = '') => `<th class="sortable ${cls}" data-action="sort" data-arg="${k}" aria-sort="${sort.key === k ? (sort.dir === 'asc' ? 'ascending' : 'descending') : 'none'}">${label}${arrow(k)}</th>`;

    const body = rows.map((c) => {
      const stuck = stuckDays(c);
      return `
      <tr data-id="${c.id}" aria-selected="${sel.includes(c.id)}">
        <td class="checkcell"><input type="checkbox" data-action="select" data-arg="${c.id}" ${sel.includes(c.id) ? 'checked' : ''} aria-label="Select ${esc(c.name)}"></td>
        <td class="clickable" data-action="open-client" data-arg="${c.id}">
          <div class="name">${esc(c.name)}</div>
          <div class="sub">${esc(c.occupation)}${c.business ? ' · ' + esc(c.business) : ''}</div>
        </td>
        <td class="tight"><span class="mono">${c.id}</span></td>
        <td class="tight">${esc(c.entity)}</td>
        <td class="tight">${pill(c.stage)}</td>
        <td class="tight">${esc(staffName(c.preparer))}</td>
        <td class="tight r num">${stuck}</td>
        <td class="tight r">${fmt.date(c.due)}</td>
        <td class="tight r num">${fmt.money(c.fee)}</td>
      </tr>`;
    }).join('');

    const empty = `
      <div class="empty">
        <div class="empty-mark"></div>
        <h3>No returns match this view</h3>
        <p>${App.state.roster.q
          ? `Nothing in the roster matches “${esc(App.state.roster.q)}”. Search by surname, client ID, occupation or form type.`
          : 'The filter is doing its job — there is genuinely nothing here.'}</p>
        <button class="btn" data-action="clear-filters">Clear filters</button>
      </div>`;

    return `
    <div class="view">
      <div class="view-head">
        <div>
          <h1>Client roster</h1>
          <p>${rows.length} of ${App.state.clients.length} returns on the working roster. ${SEASON.closedToDate.invoiced} more were accepted and invoiced earlier this season and have left the working roster.</p>
        </div>
      </div>

      <section class="panel">
        <div class="toolbar">
          <div class="seg" role="group" aria-label="Saved views">
            ${VIEWS.map((v) => `<button data-action="view" data-arg="${v.key}" aria-pressed="${App.state.roster.view === v.key}">${v.label}</button>`).join('')}
          </div>
          <div class="search">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true"><circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.4"/><path d="M11 11l4 4" stroke="currentColor" stroke-width="1.4"/></svg>
            <input id="rosterq" type="text" value="${esc(App.state.roster.q)}" placeholder="Search name, ID, occupation" aria-label="Search the roster">
          </div>
          ${App.state.roster.stage ? `<button class="btn btn-sm" data-action="clear-stage" title="Remove this filter">Stage: ${esc(stageMeta(App.state.roster.stage).label)} ✕</button>` : ''}
          <span class="spacer" style="margin-left:auto"></span>
          <button class="btn btn-sm" data-action="goto" data-arg="#/deadlines">Deadline board</button>
        </div>

        ${sel.length ? `
        <div class="bulkbar">
          <strong>${sel.length} selected</strong>
          <button class="btn btn-sm" data-action="bulk-remind">Send document reminder</button>
          <button class="btn btn-sm" data-action="bulk-review">Move to review</button>
          <button class="btn btn-sm" data-action="bulk-clear">Clear selection</button>
        </div>` : ''}

        ${rows.length ? `
        <div class="tablewrap">
          <table class="ledger">
            <thead>
              <tr>
                <th class="checkcell"><input type="checkbox" data-action="select-all" ${sel.length && sel.length === rows.length ? 'checked' : ''} aria-label="Select all shown"></th>
                ${th('name', 'Client')}
                ${th('id', 'ID')}
                ${th('entity', 'Return')}
                ${th('stage', 'Stage')}
                ${th('preparer', 'Preparer')}
                ${th('since', 'Days in stage', 'r')}
                ${th('due', 'Due', 'r')}
                ${th('fee', 'Fee', 'r')}
              </tr>
            </thead>
            <tbody>${body}</tbody>
          </table>
        </div>` : empty}
      </section>
    </div>`;
  },

  after() {
    const input = $('#rosterq');
    if (!input) return;
    input.addEventListener('input', (e) => {
      App.state.roster.q = e.target.value;
      const pos = e.target.selectionStart;
      render();
      const next = $('#rosterq');
      if (next) { next.focus(); next.setSelectionRange(pos, pos); }
    });
  }
};

/* ── 4. Client record ──────────────────────────────────────────────────── */

const CLIENT_TABS = ['overview', 'documents', 'returns', 'messages', 'billing'];

function feeLedger(c) {
  const rows = [...c.years].reverse().concat([{ y: SEASON.taxYear, fee: c.fee, current: true }]);
  const max = Math.max(...rows.map((r) => r.fee));
  return `
    <table class="compare">
      <thead><tr><th>Tax year</th><th>Fee</th><th style="width:46%">&nbsp;</th><th class="r">Change</th></tr></thead>
      <tbody>
        ${rows.map((r, i) => {
          const prev = i > 0 ? rows[i - 1].fee : null;
          const chg = prev ? ((r.fee - prev) / prev) * 100 : null;
          return `<tr>
            <td class="tight">${r.y}${r.current ? ' <span class="panel-note">current</span>' : ''}</td>
            <td class="num">${fmt.money(r.fee)}</td>
            <td><span class="bar" style="--sc:var(--st-invoiced)"><span style="width:${(r.fee / max) * 100}%"></span></span></td>
            <td class="r">${chg === null ? '<span class="delta" data-dir="flat">—</span>'
              : `<span class="delta" data-dir="${chg > 0 ? 'up' : chg < 0 ? 'down' : 'flat'}">${chg > 0 ? '+' : ''}${chg.toFixed(1)}%</span>`}</td>
          </tr>`;
        }).join('')}
      </tbody>
    </table>`;
}

const ClientScreen = {
  crumb(params) { const c = App.client(params[0]); return c ? c.name : 'Client'; },

  render(params) {
    const c = App.client(params[0]);
    if (!c) return NotFoundScreen.render();
    const tab = CLIENT_TABS.includes(params[1]) ? params[1] : 'overview';
    const out = outstandingDocs(c).length;
    const sig = signatureOf(c.id);

    const tabs = [
      ['overview', 'Overview', ''],
      ['documents', 'Documents', out ? String(out) : ''],
      ['returns', 'Returns', String(c.years.length + 1)],
      ['messages', 'Messages', String((CHASE_LOG[c.id] || []).length + c.notes.length)],
      ['billing', 'Billing', '']
    ].map(([key, label, count]) => `
      <button class="ftab" role="tab" aria-selected="${tab === key}" data-action="client-tab" data-arg="${c.id}/${key}">
        <span>${label}${count ? `<span class="tabcount">${count}</span>` : ''}</span>
      </button>`).join('');

    return `
    <div class="view">
      <div class="view-head">
        <div>
          <div class="row" style="gap:9px">
            <h1>${esc(c.name)}</h1>
            ${pill(c.stage)}
          </div>
          <p>${esc(c.occupation)}${c.business ? ` · ${esc(c.business)}` : ''} · client since ${c.since_year} · ${c.kind === 'business' ? 'EIN' : 'SSN'} <span class="mono">${esc(c.ssn || c.ein)}</span></p>
        </div>
        <div class="spacer"></div>
        <div class="row">
          <button class="btn" data-action="goto" data-arg="#/documents">Chase documents</button>
          <button class="btn btn-primary" data-action="goto" data-arg="#/return/${c.id}">Open return workspace</button>
        </div>
      </div>

      <div class="folder">
        <div class="folder-tabs" role="tablist">${tabs}</div>
        <div class="folder-body" role="tabpanel">${this.tab(c, tab, sig)}</div>
      </div>
    </div>`;
  },

  tab(c, tab, sig) {
    if (tab === 'overview') {
      const last = c.years[0];
      return `
      <div class="grid cols-2" style="padding:16px; gap:20px">
        <div class="stack">
          <div>
            <h3 style="margin-bottom:10px">This year’s return</h3>
            <div class="kv"><span class="k">Return type</span><span class="v">${esc(c.entity)} · ${esc(c.filing)}</span></div>
            <div class="kv"><span class="k">Forms in scope</span><span class="v">${c.forms.map((f) => esc(f)).join(', ')}</span></div>
            <div class="kv"><span class="k">Stage</span><span class="v">${stageMeta(c.stage).label}, ${stuckDays(c)} ${stuckDays(c) === 1 ? 'day' : 'days'}</span></div>
            <div class="kv"><span class="k">Due</span><span class="v">${fmt.dateFull(c.due)}${c.due === SEASON.businessDue ? ' — March 15 is a Sunday' : ''}</span></div>
            <div class="kv"><span class="k">Preparer</span><span class="v">${esc(staffName(c.preparer))}, ${staffById(c.preparer).cred}</span></div>
            <div class="kv"><span class="k">Reviewer</span><span class="v">${esc(staffName(c.reviewer))}, ${staffById(c.reviewer).cred}</span></div>
            <div class="kv"><span class="k">Result</span><span class="v">${c.current.refundOrDue === 'unknown' ? 'Not yet calculated' : fmt.outcome(c.current.result)}</span></div>
            ${sig ? `<div class="kv"><span class="k">Form 8879</span><span class="v">${sig.signed ? `Signed ${fmt.stamp(sig.signed)}` : `Sent ${fmt.stamp(sig.sent)}, unsigned`}</span></div>` : ''}
          </div>

          <div>
            <h3 style="margin-bottom:8px">Internal notes</h3>
            <div class="stack" style="gap:12px">
              ${c.notes.map((n) => `
                <div class="note">
                  <div class="note-meta">${fmt.dateFull(n.on)} · ${esc(staffName(n.by))}</div>
                  <p class="note-text">${esc(n.text)}</p>
                </div>`).join('')}
            </div>
          </div>
        </div>

        <div class="stack">
          <div>
            <h3 style="margin-bottom:10px">Prior years</h3>
            <table class="compare">
              <thead><tr><th>Year</th><th class="r">AGI</th><th class="r">Result</th><th class="r">Filed</th></tr></thead>
              <tbody>
                ${c.years.map((y) => `<tr>
                  <td>${y.y}${y.extended ? ' <span class="panel-note">extended</span>' : ''}</td>
                  <td class="r num">${y.agi ? fmt.money(y.agi) : '—'}</td>
                  <td class="r num">${y.result === 0 ? 'Pass-through' : fmt.outcome(y.result)}</td>
                  <td class="r">${fmt.date(y.filed)}</td>
                </tr>`).join('')}
              </tbody>
            </table>
            <p class="panel-note" style="margin-top:8px">Last filed ${fmt.dateFull(last.filed)}${last.extended ? ' on extension' : ''}.</p>
          </div>

          <div>
            <h3 style="margin-bottom:10px">Fee history</h3>
            ${feeLedger(c)}
          </div>

          <div>
            <h3 style="margin-bottom:8px">Contact</h3>
            <div class="kv"><span class="k">Email</span><span class="v">${esc(c.email)}</span></div>
            <div class="kv"><span class="k">Phone</span><span class="v">${esc(c.phone)}</span></div>
          </div>
        </div>
      </div>`;
    }

    if (tab === 'documents') {
      const chases = CHASE_LOG[c.id] || [];
      return `
      <div class="grid cols-2" style="padding:16px; gap:20px">
        <div>
          <h3 style="margin-bottom:4px">Document checklist</h3>
          <p class="panel-note" style="margin-bottom:8px">${outstandingDocs(c).length ? `${outstandingDocs(c).length} outstanding` : 'Everything is in'}</p>
          ${c.docs.map((d) => `
            <div class="checkitem" data-done="${isDocIn(c, d)}">
              <span class="box">${isDocIn(c, d) ? '✓' : ''}</span>
              <div>
                <div class="what">${esc(d.form)} <span class="panel-note">${esc(d.from)}</span></div>
                ${d.note ? `<div class="why">${esc(d.note)}</div>` : ''}
                ${d.amount ? `<div class="why num">${fmt.money(d.amount)}</div>` : ''}
              </div>
              <div class="panel-note" style="white-space:nowrap">${isDocIn(c, d) ? `In ${fmt.date(d.on || SEASON.today)}` : `Asked ${fmt.date(d.requested)}`}</div>
            </div>`).join('')}
        </div>
        <div>
          <h3 style="margin-bottom:8px">Chase history</h3>
          ${chases.length ? chases.map((ch) => `
            <div class="checkitem" data-done="true" style="grid-template-columns:minmax(0,1fr) auto">
              <div>
                <div class="what">${esc(ch.via)} · ${esc(staffName(ch.by))}</div>
                <div class="why">${esc(ch.note)}</div>
              </div>
              <div class="panel-note">${fmt.stamp(ch.on)}</div>
            </div>`).join('')
          : `<p class="panel-note">Nothing has been chased. Every document arrived without being asked for twice.</p>`}
          <div class="row" style="margin-top:14px">
            <button class="btn" data-action="goto" data-arg="#/documents">Open the chase queue</button>
          </div>
        </div>
      </div>`;
    }

    if (tab === 'returns') {
      return `
      <div style="padding:16px">
        <h3 style="margin-bottom:10px">Return history</h3>
        <div class="tablewrap">
          <table class="ledger">
            <thead><tr><th>Tax year</th><th>Forms</th><th class="r">AGI</th><th class="r">Result</th><th class="r">Fee</th><th class="r">Filed</th><th>Outcome</th></tr></thead>
            <tbody>
              <tr>
                <td>${SEASON.taxYear} <span class="panel-note">current</span></td>
                <td>${c.forms.slice(0, 3).map(esc).join(', ')}${c.forms.length > 3 ? ` +${c.forms.length - 3}` : ''}</td>
                <td class="r num">${c.current.agi ? fmt.money(c.current.agi) : '—'}</td>
                <td class="r num">${c.current.refundOrDue === 'unknown' ? '—' : fmt.outcome(c.current.result)}</td>
                <td class="r num">${fmt.money(c.fee)}</td>
                <td class="r">—</td>
                <td>${pill(c.stage)}</td>
              </tr>
              ${c.years.map((y) => `<tr>
                <td>${y.y}</td>
                <td class="panel-note">As filed</td>
                <td class="r num">${y.agi ? fmt.money(y.agi) : '—'}</td>
                <td class="r num">${y.result === 0 ? 'Pass-through' : fmt.outcome(y.result)}</td>
                <td class="r num">${fmt.money(y.fee)}</td>
                <td class="r">${fmt.date(y.filed)}</td>
                <td>${y.extended ? '<span class="pill" data-stage="docs"><span class="dot"></span>Extended on 4868</span>' : '<span class="pill" data-stage="accepted"><span class="dot"></span>Accepted</span>'}</td>
              </tr>`).join('')}
            </tbody>
          </table>
        </div>
        <div style="max-width:520px; margin-top:20px">
          <h3 style="margin-bottom:10px">Fee history</h3>
          ${feeLedger(c)}
        </div>
      </div>`;
    }

    if (tab === 'messages') {
      const chases = CHASE_LOG[c.id] || [];
      const draftKey = `msg::${c.id}`;
      const template = CHASE_TEMPLATES[c.id];
      return `
      <div class="grid cols-2" style="padding:16px; gap:20px">
        <div>
          <h3 style="margin-bottom:10px">Thread</h3>
          <div class="stack" style="gap:12px">
            ${chases.map((ch) => `
              <div class="note">
                <div class="note-meta">${fmt.stamp(ch.on)} · ${esc(staffName(ch.by))} · ${esc(ch.via)}</div>
                <p class="note-text">${esc(ch.note)}</p>
              </div>`).join('')}
            ${c.notes.map((n) => `
              <div class="note" style="border-left-color:var(--st-review)">
                <div class="note-meta">${fmt.dateFull(n.on)} · ${esc(staffName(n.by))} · internal note</div>
                <p class="note-text">${esc(n.text)}</p>
              </div>`).join('')}
          </div>
        </div>
        <div>
          <h3 style="margin-bottom:10px">Write to ${esc(c.name.split(' ')[0])}</h3>
          <label class="field">
            <span>Message</span>
            <textarea id="clientmsg" data-draft="${draftKey}" placeholder="${template ? 'A draft is loaded below — edit it before sending.' : 'Write to the client…'}">${esc(App.draft(draftKey) || (template ? template.body : ''))}</textarea>
          </label>
          <div class="row" style="margin-top:10px">
            <button class="btn btn-primary" data-action="send-message" data-arg="${c.id}">Send message</button>
            <span class="panel-note">${template ? esc(template.channel) : 'Portal message'}</span>
          </div>
        </div>
      </div>`;
    }

    /* billing */
    const inv = App.state.invoices.filter((i) => i.client === c.id);
    return `
    <div style="padding:16px">
      <h3 style="margin-bottom:10px">Invoices</h3>
      ${inv.length ? `
      <div class="tablewrap">
        <table class="ledger">
          <thead><tr><th>Invoice</th><th>Issued</th><th class="r">Standard</th><th class="r">Billed</th><th class="r">Written off</th><th class="r">Paid</th><th>Status</th></tr></thead>
          <tbody>${inv.map((i) => `
            <tr>
              <td class="mono">${i.no}</td>
              <td>${fmt.date(i.issued)}</td>
              <td class="r num">${fmt.money(i.standard)}</td>
              <td class="r num">${fmt.money(i.billed)}</td>
              <td class="r num">${i.writeOff ? fmt.money(i.writeOff) : '—'}</td>
              <td class="r num">${fmt.money(i.paid)}</td>
              <td>${invoiceStatusPill(i.status)}</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${inv.filter((i) => i.note).map((i) => `<p class="panel-note" style="margin-top:10px">${i.no}: ${esc(i.note)}</p>`).join('')}`
      : `<div class="empty">
          <div class="empty-mark"></div>
          <h3>Nothing invoiced yet</h3>
          <p>The fee of ${fmt.money(c.fee)} is billed once the IRS accepts the return. Nothing to do here today.</p>
          <button class="btn" data-action="goto" data-arg="#/billing">Open billing</button>
        </div>`}
      <div style="max-width:520px; margin-top:20px">${feeLedger(c)}</div>
    </div>`;
  },

  after() {
    const t = $('#clientmsg');
    if (t) t.addEventListener('input', (e) => App.draft(e.target.dataset.draft, e.target.value));
  }
};

function invoiceStatusPill(status) {
  const map = { paid: 'accepted', sent: 'transmitted', overdue: 'rejected', partial: 'signature', draft: 'intake' };
  const label = { paid: 'Paid', sent: 'Sent', overdue: 'Overdue', partial: 'Part paid', draft: 'Draft' }[status];
  return `<span class="pill" data-stage="${map[status]}"><span class="dot"></span>${label}</span>`;
}
