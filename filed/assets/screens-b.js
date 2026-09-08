/* FILED — screens: document chase, return workspace, review queue,
   e-file centre, reject resolution. */

/* ── 5. Document intake and chase ──────────────────────────────────────── */

const DocumentsScreen = {
  crumb: 'Document chase',
  render(params) {
    const waiting = App.state.clients
      .filter((c) => outstandingDocs(c).length)
      .sort((a, b) => {
        const oldest = (c) => Math.min(...outstandingDocs(c).map((d) => fmt.days(d.requested || SEASON.today)));
        return oldest(b) - oldest(a);
      });

    if (!waiting.length) {
      return `
      <div class="view">
        <div class="view-head"><div><h1>Document chase</h1></div></div>
        <section class="panel"><div class="empty">
          <div class="empty-mark"></div>
          <h3>Every folder is complete</h3>
          <p>Nothing is outstanding across the roster. The next thing worth doing is clearing the review queue — four returns are waiting on a reviewer.</p>
          <button class="btn btn-primary" data-action="goto" data-arg="#/review">Open the review queue</button>
        </div></section>
      </div>`;
    }

    const current = App.client(params[0]) && outstandingDocs(App.client(params[0])).length
      ? App.client(params[0]) : waiting[0];

    const list = waiting.map((c) => {
      const out = outstandingDocs(c);
      const oldest = Math.max(...out.map((d) => fmt.days(d.requested || SEASON.today)));
      const chases = (CHASE_LOG[c.id] || []).length;
      return `
      <button class="stagerow" style="grid-template-columns:minmax(0,1fr) auto; align-items:start; padding:11px 14px"
              data-action="goto" data-arg="#/documents/${c.id}" aria-current="${c.id === current.id ? 'true' : 'false'}">
        <span>
          <span class="name" style="font-weight:600">${esc(c.name)}</span>
          <span class="sub" style="display:block; color:var(--text-muted); font-size:12.5px">
            ${out.length} outstanding · asked ${oldest} ${oldest === 1 ? 'day' : 'days'} ago · ${chases} ${chases === 1 ? 'chase' : 'chases'} sent
          </span>
        </span>
        <span>${pill(c.stage)}</span>
      </button>`;
    }).join('');

    const c = current;
    const tpl = CHASE_TEMPLATES[c.id];
    const draftKey = `chase::${c.id}`;
    const chases = CHASE_LOG[c.id] || [];
    const internal = chases.every((ch) => ch.via === 'Internal');

    return `
    <div class="view">
      <div class="view-head">
        <div>
          <h1>Document chase</h1>
          <p>${waiting.length} clients are holding up their own returns. Sorted by how long the oldest request has been sitting.</p>
        </div>
      </div>

      <div class="grid" style="grid-template-columns:minmax(280px, 360px) minmax(0,1fr)">
        <section class="panel" style="align-self:start">
          <div class="panel-head"><h2>Waiting on documents</h2><span class="spacer"></span><span class="panel-note">${waiting.length}</span></div>
          ${list}
        </section>

        <section class="panel">
          <div class="panel-head">
            <h2>${esc(c.name)}</h2>
            ${pill(c.stage)}
            <span class="spacer"></span>
            <button class="btn btn-sm" data-action="open-client" data-arg="${c.id}">Open client record</button>
          </div>

          <div class="panel-body">
            <div class="grid cols-2" style="gap:22px">
              <div>
                <h3 style="margin-bottom:8px">Checklist</h3>
                ${c.docs.map((d) => `
                  <div class="checkitem" data-done="${isDocIn(c, d)}">
                    <span class="box">${isDocIn(c, d) ? '✓' : ''}</span>
                    <div>
                      <div class="what">${esc(d.form)} <span class="panel-note">${esc(d.from)}</span></div>
                      ${d.note ? `<div class="why">${esc(d.note)}</div>` : ''}
                    </div>
                    <div style="white-space:nowrap">
                      ${isDocIn(c, d)
                        ? `<span class="panel-note">In ${fmt.date(d.on || SEASON.today)}</span>`
                        : `<button class="btn btn-sm" data-action="doc-received" data-arg="${c.id}::${d.form}">Mark received</button>`}
                    </div>
                  </div>`).join('')}

                <h3 style="margin:18px 0 8px">What has been chased</h3>
                ${chases.length ? chases.map((ch) => `
                  <div class="note" style="margin-bottom:10px">
                    <div class="note-meta">${fmt.stamp(ch.on)} · ${esc(staffName(ch.by))} · ${esc(ch.via)}</div>
                    <p class="note-text">${esc(ch.note)}</p>
                  </div>`).join('')
                : '<p class="panel-note">Nothing sent yet.</p>'}
                ${internal && chases.length ? `<p class="panel-note">This one is on us, not on the client. No reminder should go out.</p>` : ''}
              </div>

              <div>
                <h3 style="margin-bottom:8px">Reminder</h3>
                ${tpl ? `
                  <label class="field">
                    <span>Subject</span>
                    <input type="text" id="chasesubject" data-draft="${draftKey}::subject" value="${esc(App.draft(draftKey + '::subject') || tpl.subject)}">
                  </label>
                  <label class="field" style="margin-top:10px">
                    <span>Message · ${esc(tpl.channel)}</span>
                    <textarea id="chasebody" data-draft="${draftKey}" style="min-height:230px">${esc(App.draft(draftKey) || tpl.body)}</textarea>
                  </label>
                  <div class="row" style="margin-top:10px">
                    <button class="btn btn-primary" data-action="send-chase" data-arg="${c.id}">Send reminder</button>
                    <span class="panel-note">Logged against the client record</span>
                  </div>`
                : `<div class="banner" data-tone="info">
                    <span class="sev"></span>
                    <div><b>No reminder drafted</b><p>The outstanding item is produced in-house, so there is nothing to ask the client for.</p></div>
                    <button class="btn btn-sm" data-action="goto" data-arg="#/review">Open review queue</button>
                  </div>`}
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>`;
  },

  after() {
    $$('[data-draft]').forEach((el) => el.addEventListener('input', (e) => App.draft(e.target.dataset.draft, e.target.value)));
  }
};

/* ── 6. Return workspace ───────────────────────────────────────────────── */

function comparisonTable(c) {
  const lines = RETURN_LINES[c.id];
  const prior = c.years[0];

  const rows = lines ? lines.rows : [
    { label: 'Adjusted gross income', form: 'Form 1040, line 11', now: c.current.agi, prior: prior.agi }
  ];

  const body = rows.map((r) => {
    const chg = r.prior ? ((r.now - r.prior) / r.prior) * 100 : null;
    const big = chg !== null && Math.abs(chg) >= 20;
    return `
    <tr${r.rule ? ' class="total"' : ''}>
      <td>${esc(r.label)}<div class="panel-note">${esc(r.form)}</div></td>
      <td class="r num">${fmt.money(r.now)}</td>
      <td class="r num" style="color:var(--text-muted)">${fmt.money(r.prior)}</td>
      <td class="r"><span class="delta" data-dir="${chg > 0 ? 'up' : chg < 0 ? 'down' : 'flat'}">${chg === null ? '—' : `${chg > 0 ? '+' : '−'}${Math.abs(chg).toFixed(1)}%`}${big ? ' ⚑' : ''}</span></td>
    </tr>`;
  }).join('');

  const outcome = lines ? lines.outcome : { now: c.current.result, prior: prior.result };

  return `
  <table class="compare">
    <thead>
      <tr><th>Line</th><th class="r">${SEASON.taxYear}</th><th class="r">${SEASON.taxYear - 1}</th><th class="r">Change</th></tr>
    </thead>
    <tbody>
      ${body}
      <tr class="total">
        <td>${outcome.now > 0 ? 'Refund' : 'Balance due'}</td>
        <td class="r num">${fmt.outcome(outcome.now)}</td>
        <td class="r num" style="color:var(--text-muted)">${fmt.outcome(outcome.prior)}</td>
        <td class="r"><span class="delta" data-dir="${outcome.now < outcome.prior ? 'up' : 'down'}">${fmt.money(Math.abs(outcome.now - outcome.prior))}</span></td>
      </tr>
    </tbody>
  </table>
  ${lines ? `<p class="panel-note" style="margin-top:10px; max-width:70ch">${esc(lines.note)} A change of 20% or more is flagged.</p>`
    : `<p class="panel-note" style="margin-top:10px">Line-level comparison appears once the return is calculated. Prior year is shown as filed${prior.extended ? ' on extension' : ''}.</p>`}`;
}

const ReturnScreen = {
  crumb(params) { const c = App.client(params[0]); return c ? `${c.name} — return` : 'Return'; },

  render(params) {
    const c = App.client(params[0]);
    if (!c) return NotFoundScreen.render();

    const diags = (c.diagnostics || []).map((d) => ({ ...d, resolved: App.state.resolved.includes(c.id + '::' + d.code) }));
    const blockers = diags.filter((d) => d.sev === 'block' && !d.resolved);
    const forms = FORM_STATUS[c.id] || c.forms.map((f) => ({ form: f, state: 'done', note: '' }));
    const done = forms.filter((f) => f.state === 'done').length;

    const sevLabel = { block: 'Blocks transmission', variance: 'Year-over-year variance', attention: 'Needs a decision' };

    return `
    <div class="view">
      <div class="view-head">
        <div>
          <div class="row" style="gap:9px">
            <h1>${esc(c.name)}</h1>${pill(c.stage)}
          </div>
          <p>${esc(c.entity)} · ${esc(c.filing)} · return <span class="mono">${c.id}</span> · prepared by ${esc(staffName(c.preparer))} · due ${fmt.dateFull(c.due)}</p>
        </div>
        <div class="spacer"></div>
        <div class="row">
          <button class="btn" data-action="open-client" data-arg="${c.id}">Client record</button>
          <button class="btn btn-primary" data-action="ready-for-review" data-arg="${c.id}"
            ${blockers.length || c.stage !== 'prep' ? 'disabled' : ''}
            title="${blockers.length ? 'Clear the blocking diagnostic first' : c.stage !== 'prep' ? 'This return has already left preparation' : ''}">
            Send to review
          </button>
        </div>
      </div>

      ${blockers.length ? `
      <div class="banner" data-tone="error" style="margin-bottom:16px">
        <span class="sev"></span>
        <div>
          <b>${blockers.length === 1 ? 'One issue blocks transmission' : `${blockers.length} issues block transmission`}</b>
          <p>${esc(blockers[0].title)}. A return cannot be sent to review or to the IRS while a blocking diagnostic is open.</p>
        </div>
      </div>` : ''}

      <div class="grid" style="grid-template-columns:minmax(260px, 330px) minmax(0,1fr)">
        <section class="panel" style="align-self:start">
          <div class="panel-head"><h2>Forms</h2><span class="spacer"></span><span class="panel-note">${done} of ${forms.length} complete</span></div>
          <div class="panel-body">
            ${forms.map((f) => `
              <div class="checkitem" data-done="${f.state === 'done'}">
                <span class="box">${f.state === 'done' ? '✓' : f.state === 'open' ? '·' : ''}</span>
                <div>
                  <div class="what">${esc(f.form)}</div>
                  ${f.note ? `<div class="why">${esc(f.note)}</div>` : ''}
                  ${f.state === 'notstarted' ? '<div class="why">Not started</div>' : ''}
                </div>
                <span></span>
              </div>`).join('')}
          </div>
          <div class="panel-foot">
            <span class="panel-note">Signature: ${signatureOf(c.id) ? (signatureOf(c.id).signed ? `Form 8879 signed ${fmt.date(signatureOf(c.id).signed.slice(0,10))}` : 'Form 8879 sent, unsigned') : 'Form 8879 not sent'}</span>
          </div>
        </section>

        <div class="stack">
          <section class="panel">
            <div class="panel-head">
              <h2>Diagnostics</h2>
              <span class="spacer"></span>
              <span class="panel-note">${diags.filter((d) => !d.resolved).length} open</span>
            </div>
            ${diags.length ? diags.map((d) => `
              <div class="diag" data-sev="${d.sev}" data-resolved="${d.resolved}">
                <div class="sev"></div>
                <div>
                  <div class="diag-title">
                    <b>${esc(d.title)}</b>
                    <span class="diag-kind">${sevLabel[d.sev]}</span>
                    <span class="panel-note mono">${d.code}</span>
                  </div>
                  <p class="diag-body">${esc(d.body)}</p>
                  ${d.resolved ? '<p class="panel-note" style="margin-top:6px">Cleared by ' + esc(staffName(c.preparer)) + ' today.</p>' : `
                  <div class="diag-actions">
                    <button class="btn btn-sm" data-action="resolve-diag" data-arg="${c.id}::${d.code}">${d.sev === 'block' ? 'Mark resolved' : d.sev === 'variance' ? 'Add explanation note' : 'Record the decision'}</button>
                    ${d.link ? `<button class="btn btn-sm btn-quiet" data-action="goto" data-arg="${d.link}">${esc(d.action)}</button>` : ''}
                  </div>`}
                </div>
              </div>`).join('')
            : `<div class="empty" style="padding:30px">
                <h3>No diagnostics</h3>
                <p>Nothing in this return trips a check. It is ready for a reviewer to read rather than to fix.</p>
              </div>`}
          </section>

          <section class="panel">
            <div class="panel-head">
              <h2>Against last year</h2>
              <span class="spacer"></span>
              <span class="panel-note">${SEASON.taxYear} compared with ${SEASON.taxYear - 1} as filed</span>
            </div>
            <div class="panel-body">${comparisonTable(c)}</div>
          </section>
        </div>
      </div>
    </div>`;
  }
};

/* ── 7. Review queue ───────────────────────────────────────────────────── */

const ReviewScreen = {
  crumb: 'Review queue',
  render(params) {
    const queue = byStage('review');

    if (!queue.length) {
      return `
      <div class="view">
        <div class="view-head"><div><h1>Review queue</h1></div></div>
        <section class="panel"><div class="empty">
          <div class="empty-mark"></div>
          <h3>The queue is clear</h3>
          <p>Nothing is waiting on a reviewer. ${readyToTransmit().length} signed ${readyToTransmit().length === 1 ? 'return is' : 'returns are'} ready to go to the IRS.</p>
          <button class="btn btn-primary" data-action="goto" data-arg="#/efile">Open the e-file centre</button>
        </div></section>
      </div>`;
    }

    const current = queue.find((c) => c.id === params[0]) || queue[0];
    const diff = REVIEW_DIFFS[current.id];
    const noteKey = `review::${current.id}`;
    const noteErr = App.state.drafts[`err::${noteKey}`];

    const list = queue.map((c) => `
      <button class="stagerow" style="grid-template-columns:minmax(0,1fr) auto; padding:11px 14px; align-items:start"
              data-action="goto" data-arg="#/review/${c.id}" aria-current="${c.id === current.id ? 'true' : 'false'}">
        <span>
          <span style="font-weight:600">${esc(c.name)}</span>
          <span style="display:block; color:var(--text-muted); font-size:12.5px">
            ${esc(c.entity)} · from ${esc(staffName(c.preparer))} · ${stuckDays(c)} ${stuckDays(c) === 1 ? 'day' : 'days'} in review
          </span>
        </span>
        <span class="panel-note" style="white-space:nowrap">due ${fmt.date(c.due)}</span>
      </button>`).join('');

    return `
    <div class="view">
      <div class="view-head">
        <div>
          <h1>Review queue</h1>
          <p>${queue.length} ${queue.length === 1 ? 'return is' : 'returns are'} with a reviewer. A return leaves review in one direction or the other, and either way it carries a note.</p>
        </div>
      </div>

      <div class="grid" style="grid-template-columns:minmax(280px, 340px) minmax(0,1fr)">
        <section class="panel" style="align-self:start">
          <div class="panel-head"><h2>Waiting</h2><span class="spacer"></span><span class="panel-note">${queue.length}</span></div>
          ${list}
        </section>

        <section class="panel">
          <div class="panel-head">
            <h2>${esc(current.name)}</h2>
            <span class="panel-note">${esc(current.entity)} · <span class="mono">${current.id}</span></span>
            <span class="spacer"></span>
            <button class="btn btn-sm" data-action="goto" data-arg="#/return/${current.id}">Open return workspace</button>
          </div>

          <div class="panel-body">
            ${diff ? `
              <div class="row" style="justify-content:space-between; margin-bottom:12px">
                <span class="panel-note">Reviewed by ${esc(staffName(diff.reviewer))}, ${diff.minutes} minutes, ${diff.changes.length} changes</span>
                <span class="panel-note">Received ${fmt.stamp(diff.received)} from ${esc(staffName(diff.preparer))}</span>
              </div>
              ${diff.changes.map((ch) => `
                <div class="diffrow">
                  <div class="row" style="gap:8px">
                    <b style="font-size:13.5px">${esc(ch.field)}</b>
                    <span class="panel-note">${esc(ch.form)}</span>
                  </div>
                  <div class="diffline">
                    <div class="diffbox before">${esc(ch.before)}</div>
                    <div class="diffarrow">→</div>
                    <div class="diffbox after">${esc(ch.after)}</div>
                  </div>
                  <p class="panel-note" style="max-width:80ch">${esc(ch.why)}</p>
                </div>`).join('')}
              ${diff.delta.refundBefore !== diff.delta.refundAfter ? `
                <div class="banner" data-tone="warn" style="margin:14px 0">
                  <span class="sev"></span>
                  <div>
                    <b>The result changed in review</b>
                    <p>Refund moved from ${fmt.money(diff.delta.refundBefore)} to ${fmt.money(diff.delta.refundAfter)}. The client was told the earlier figure on the phone, so someone has to make that call before the 8879 goes out.</p>
                  </div>
                </div>` : ''}
            ` : `<p class="panel-note">No reviewer edits recorded yet.</p>`}

            <div style="max-width:640px; margin-top:6px">
              <label class="field ${noteErr ? 'field-error' : ''}">
                <span>Reviewer note — required either way</span>
                <textarea id="reviewnote" data-draft="${noteKey}" placeholder="What you changed, or what the preparer needs to fix.">${esc(App.draft(noteKey))}</textarea>
              </label>
              ${noteErr ? `<p class="errortext" style="margin-top:6px">⚑ ${esc(noteErr)}</p>` : ''}
              <div class="row" style="margin-top:12px">
                <button class="btn btn-primary" data-action="review-approve" data-arg="${current.id}">Approve and send for signature</button>
                <button class="btn" data-action="review-return" data-arg="${current.id}">Return to preparer</button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>`;
  },

  after() {
    const t = $('#reviewnote');
    if (t) t.addEventListener('input', (e) => App.draft(e.target.dataset.draft, e.target.value));
  }
};

/* ── 8. E-file centre ──────────────────────────────────────────────────── */

const EfileScreen = {
  crumb: 'E-file centre',
  render() {
    const ready = readyToTransmit();
    const inFlight = byStage('transmitted');
    const rejects = byStage('rejected');

    const readyRows = ready.map((c) => {
      const sig = signatureOf(c.id);
      return `
      <tr>
        <td><div class="name">${esc(c.name)}</div><div class="sub">${esc(c.entity)} · ${esc(staffName(c.preparer))}</div></td>
        <td class="tight mono">${c.id}</td>
        <td class="tight">Signed ${fmt.stamp(sig.signed)}</td>
        <td class="tight">${esc(sig.method)}</td>
        <td class="tight r">${fmt.date(c.due)}</td>
        <td class="tight r">${fmt.outcome(c.current.result)}</td>
      </tr>`;
    }).join('');

    return `
    <div class="view">
      <div class="view-head">
        <div>
          <h1>E-file centre</h1>
          <p>Transmitting with EFIN <span class="mono">${SEASON.efin}</span>. Transmission is final — a filed return can only be changed by amending it on Form 1040-X.</p>
        </div>
        <div class="spacer"></div>
        <button class="btn btn-primary" data-action="transmit-ready" ${ready.length ? '' : 'disabled'}>
          Transmit ${ready.length} to IRS
        </button>
      </div>

      ${App.state.ackServiceDown ? `
      <div class="banner" data-tone="error" style="margin-bottom:16px">
        <span class="sev"></span>
        <div>
          <b>The IRS acknowledgment service did not respond</b>
          <p>The last request to the Modernized e-File system timed out after 30 seconds. Returns already transmitted are still filed — this affects only our ability to read acknowledgments back. Nothing needs retransmitting.</p>
        </div>
        <button class="btn btn-sm" data-action="check-acks">Try again</button>
      </div>` : ''}

      <div class="stack">
        <section class="panel">
          <div class="panel-head">
            <h2>Signed and ready to transmit</h2>
            <span class="spacer"></span>
            <span class="panel-note">Form 8879 on file for each</span>
          </div>
          ${ready.length ? `
          <div class="tablewrap"><table class="ledger">
            <thead><tr><th>Client</th><th>Return</th><th>Signature</th><th>Method</th><th class="r">Due</th><th class="r">Result</th></tr></thead>
            <tbody>${readyRows}</tbody>
          </table></div>` : `
          <div class="empty" style="padding:34px">
            <div class="empty-mark"></div>
            <h3>Nothing is waiting to transmit</h3>
            <p>Returns appear here the moment a client signs Form 8879. ${byStage('signature').length} ${byStage('signature').length === 1 ? 'client has' : 'clients have'} been sent one and not signed yet.</p>
            <button class="btn" data-action="goto" data-arg="#/clients">See who has not signed</button>
          </div>`}
        </section>

        <div class="grid cols-2">
          <section class="panel">
            <div class="panel-head">
              <h2>In flight</h2>
              <span class="spacer"></span>
              <button class="btn btn-sm" data-action="check-acks" ${inFlight.length ? '' : 'disabled'}>Check for acknowledgments</button>
            </div>
            ${inFlight.length ? `
            <div class="tablewrap"><table class="ledger">
              <thead><tr><th>Client</th><th>Batch</th><th>Transmitted</th><th class="r">Waiting</th></tr></thead>
              <tbody>${inFlight.map((c) => {
                const sent = (c.ack && c.ack.transmitted) || SEASON.today + 'T09:00:00';
                return `<tr>
                  <td><div class="name">${esc(c.name)}</div><div class="sub">${esc(c.entity)}</div></td>
                  <td class="mono">${esc((c.ack && c.ack.batch) || '—')}</td>
                  <td>${fmt.time(sent)}</td>
                  <td class="r">${Math.max(0, Math.round((new Date(SEASON.today + 'T09:20:00') - new Date(sent)) / 60000))} min</td>
                </tr>`;
              }).join('')}</tbody>
            </table></div>` : `<div class="empty" style="padding:28px"><h3>Nothing in flight</h3><p>Every transmitted return has been acknowledged.</p></div>`}
          </section>

          <section class="panel">
            <div class="panel-head">
              <h2>Rejected — triage</h2>
              <span class="spacer"></span>
              <span class="panel-note">${rejects.length} to resolve</span>
            </div>
            ${rejects.length ? rejects.map((c) => `
              <div class="risk" data-sev="critical" data-action="goto" data-arg="#/reject/${c.id}" tabindex="0" role="link">
                <div class="risk-strip">
                  <div class="sev"></div>
                  <div>
                    <div class="risk-top">
                      <span class="risk-name">${esc(c.name)}</span>
                      <span class="mono" style="font-size:12.5px">${c.reject.code}</span>
                      <span class="panel-note">attempt ${c.reject.attempt} · ${fmt.stamp(c.reject.rejected)}</span>
                    </div>
                    <p class="risk-why">${esc(REJECT_LIBRARY[c.reject.code].plain)}</p>
                  </div>
                </div>
              </div>`).join('')
            : `<div class="empty" style="padding:28px"><h3>Nothing rejected</h3><p>Every return the IRS has looked at came back accepted.</p></div>`}
          </section>
        </div>

        <section class="panel">
          <div class="panel-head"><h2>Batch history</h2><span class="spacer"></span><span class="panel-note">Season to date: ${SEASON.closedToDate.accepted} accepted</span></div>
          <div class="tablewrap"><table class="ledger">
            <thead><tr><th>Batch</th><th>Transmitted</th><th class="r">Returns</th><th>Outcome</th><th>Notes</th></tr></thead>
            <tbody>${App.state.batches.map((b) => `
              <tr>
                <td class="mono">${b.id}</td>
                <td>${fmt.stamp(b.sent)}</td>
                <td class="r num">${b.count}</td>
                <td>${b.state === 'accepted' ? pill('accepted') : b.state === 'pending' ? pill('transmitted') : `<span class="pill" data-stage="rejected"><span class="dot"></span>Mixed</span>`}</td>
                <td class="panel-note">${esc(b.note)}</td>
              </tr>`).join('')}
            </tbody>
          </table></div>
        </section>
      </div>
    </div>`;
  }
};

/* ── 9. Reject resolution ──────────────────────────────────────────────── */

const RejectScreen = {
  crumb(params) { const c = App.client(params[0]); return c ? `Reject — ${c.name}` : 'Reject'; },

  render(params) {
    const c = App.client(params[0]);
    if (!c || !c.reject) return NotFoundScreen.render();
    const lib = REJECT_LIBRARY[c.reject.code];
    const steps = lib.fix.map((s, i) => ({ text: s, done: App.state.drafts[`fix::${c.id}::${i}`] === 'done' }));
    const allDone = steps.every((s) => s.done);
    const resolved = c.stage !== 'rejected';

    return `
    <div class="view">
      <div class="view-head">
        <div>
          <div class="row" style="gap:9px"><h1>${esc(c.name)}</h1>${pill(c.stage)}</div>
          <p>${esc(c.entity)} · <span class="mono">${c.id}</span> · transmitted ${fmt.stamp(c.reject.transmitted)} in batch <span class="mono">${c.reject.batch}</span> · attempt ${c.reject.attempt}</p>
        </div>
        <div class="spacer"></div>
        <div class="row">
          <button class="btn" data-action="open-client" data-arg="${c.id}">Client record</button>
          <button class="btn btn-primary" data-action="retransmit" data-arg="${c.id}" ${allDone && !resolved ? '' : 'disabled'}
            title="${resolved ? 'Already retransmitted' : allDone ? '' : 'Work the fix path first'}">Retransmit to IRS</button>
        </div>
      </div>

      <div class="grid" style="grid-template-columns:minmax(0,1.5fr) minmax(280px,1fr)">
        <div class="stack">
          <section class="panel">
            <div class="panel-body" style="padding:18px">
              <h2 style="font-size:17px; max-width:62ch">${esc(lib.plain)}</h2>
              <p style="color:var(--text-muted); margin-top:10px; max-width:74ch">${esc(lib.cause)}</p>
              <div class="row" style="gap:20px; margin-top:16px; padding-top:14px; border-top:1px solid var(--rule-hair)">
                <div>
                  <div class="panel-note">IRS business rule</div>
                  <div class="mono" style="font-size:15px; margin-top:2px">${c.reject.code}</div>
                </div>
                <div style="max-width:62ch">
                  <div class="panel-note">What the rule says</div>
                  <div style="font-size:13px; margin-top:2px">${esc(lib.official)}</div>
                </div>
              </div>
            </div>
          </section>

          <section class="panel">
            <div class="panel-head">
              <h2>Fix path</h2>
              <span class="spacer"></span>
              <span class="panel-note">${steps.filter((s) => s.done).length} of ${steps.length} done</span>
            </div>
            <div class="panel-body">
              ${steps.map((s, i) => `
                <div class="checkitem" data-done="${s.done}">
                  <span class="box">${s.done ? '✓' : ''}</span>
                  <div><div class="what">${esc(s.text)}</div></div>
                  <div>${resolved ? '' : `<button class="btn btn-sm" data-action="fix-step" data-arg="${c.id}::${i}">${s.done ? 'Undo' : 'Done'}</button>`}</div>
                </div>`).join('')}

              ${resolved ? `
                <div class="banner" data-tone="info" style="margin-top:14px">
                  <span class="sev"></span>
                  <div><b>Retransmitted</b><p>Sent back to the IRS today. Acknowledgments for a corrected return usually come back within the hour.</p></div>
                  <button class="btn btn-sm" data-action="goto" data-arg="#/efile">E-file centre</button>
                </div>`
              : !allDone ? `<p class="panel-note" style="margin-top:12px">Retransmission stays disabled until the fix path is worked. A second reject on the same rule is what turns a two-day delay into a two-week one.</p>` : `
                <div class="banner" data-tone="info" style="margin-top:14px">
                  <span class="sev"></span>
                  <div><b>Ready to retransmit</b><p>${lib.retransmit ? 'The return itself has not changed in a way that requires a new Form 8879.' : 'A new Form 8879 is required before this can go back.'}</p></div>
                </div>`}
            </div>
          </section>
        </div>

        <div class="stack">
          <section class="panel">
            <div class="panel-head"><h2>What it costs the client</h2></div>
            <div class="panel-body">
              <div class="kv"><span class="k">Expected result</span><span class="v">${fmt.outcome(c.current.result)}</span></div>
              <div class="kv"><span class="k">Filing deadline</span><span class="v">${fmt.dateFull(c.due)}, ${daysToDeadline} days away</span></div>
              <div class="kv"><span class="k">Rejected</span><span class="v">${fmt.stamp(c.reject.rejected)}</span></div>
              <div class="kv"><span class="k">Time to acknowledge</span><span class="v">${Math.round((new Date(c.reject.rejected) - new Date(c.reject.transmitted)) / 60000)} minutes</span></div>
              <p class="panel-note" style="margin-top:10px">A rejected return is not a late return. The IRS gives a five-day perfection period from the rejection to resubmit, and the original transmission date holds.</p>
            </div>
          </section>

          <section class="panel">
            <div class="panel-head"><h2>Notes on file</h2></div>
            <div class="panel-body stack" style="gap:12px">
              ${c.notes.map((n) => `
                <div class="note">
                  <div class="note-meta">${fmt.dateFull(n.on)} · ${esc(staffName(n.by))}</div>
                  <p class="note-text">${esc(n.text)}</p>
                </div>`).join('')}
            </div>
          </section>
        </div>
      </div>
    </div>`;
  }
};
