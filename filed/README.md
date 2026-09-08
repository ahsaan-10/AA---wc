# FILED

An operations console for a small US tax practice — eight preparers, roughly 600 individual
and small-business returns a season. Its single job is that no return gets lost and no
deadline gets missed.

**Live prototype:** https://claude.ai/code/artifact/6973056b-8bf3-4850-941e-4c6c436f2a7d

The season modelled is tax year 2025, filed in 2026. Today, in the prototype, is Thursday
12 March 2026 — 34 days from the 15 April individual deadline and four days from the
partnership and S-corp deadline, which falls on Monday 16 March because 15 March is a Sunday.

## Running it

Nothing to install and no build step for the source.

```
open filed/index.html            # or: npx http-server filed
node filed/build.mjs             # bundles everything into filed/dist/filed.html
```

`index.html` loads the source files directly. `build.mjs` inlines them into a single
self-contained page — that bundle is what is published at the link above.

## The workflow it models

Every screen exists to serve one stage. Nothing was added because dashboards usually have one.

```
Intake → Documents outstanding → In preparation → In review → Awaiting signature (Form 8879)
       → Transmitted → IRS accepted / IRS rejected → Invoiced
```

## The fourteen screens

| # | Screen | Route |
|---|---|---|
| 1 | Case study cover | `#/cover` |
| 2 | Season command | `#/command` |
| 3 | Client roster | `#/clients` |
| 4 | Client record (folder tabs) | `#/client/RAG-0118/overview` |
| 5 | Document intake and chase | `#/documents` |
| 6 | Return workspace | `#/return/RAG-0118` |
| 7 | Review queue | `#/review` |
| 8 | E-file centre | `#/efile` |
| 9 | Reject resolution | `#/reject/DUA-0409` |
| 10 | Deadline board | `#/deadlines` |
| 11 | Client portal preview | `#/portal` |
| 12 | Team capacity | `#/team` |
| 13 | Billing and realisation | `#/billing` |
| 14 | Command palette | `⌘K` / `Ctrl-K` from anywhere |

Plus the four states that expose junior work, each designed rather than defaulted: the empty
state (roster with no matches, cleared chase queue, cleared review queue), the loading state
(first visit to any screen), the destructive confirmation (transmitting to the IRS, writing
off a fee, signing Form 8879), and the error state (the IRS acknowledgment service not
responding, and a record that is not in this season).

## What actually works

- Sorting, saved views, search, multi-select and bulk actions on the roster all filter real data.
- Moving a return between stages updates every count that reads from it — rail badges, the
  stage ledger, the at-risk list, the review queue, the transmit queue and the deadline board.
- Marking the last outstanding document received moves the client from documents to preparation.
- Review cannot be completed without a note; approving sends Form 8879 and the return leaves
  the queue for the signature stage.
- Transmission takes a confirmation with an explicit Form 8879 consent, creates a batch, and
  the acknowledgment check fails once before it succeeds — because Modernized e-File does that.
- Retransmission of a rejected return stays disabled until the fix path has been worked.
- Signing in the portal preview puts the return in the transmit queue on the e-file centre.
- Drag a card on the deadline board to file or withdraw a Form 4868 extension.
- The command palette opens on ⌘K and jumps to clients, reject codes, screens and actions.
- Typed text survives the session; confirmations use the same verb as the button that caused them.
- Responsive to 390px, visible keyboard focus, reduced motion respected, both themes designed.

## The data

Every value is meant to survive being read by someone who prepares returns for a living.

- Real IRS Modernized e-File business rules with their real meanings: `IND-031-04` (prior-year
  AGI mismatch), `R0000-500-01` (name and SSN do not match SSA records), `F1040-164-01`
  (Form 8862 required after a prior EIC disallowance).
- Real form designations: 1040, Schedule C, Schedule E, Form 4562, Form 8879, Form 4868,
  Form 1065, Schedule K-1, Form 8995, Form 8829, Form 8606, Form 8962, 1099-NEC, 1099-B, 1098-T.
- Priya Raghunathan's Schedule C ties out: gross receipts $214,180 less $80,688 of expenses
  gives net profit of $133,492; self-employment tax of $18,862 and a QBI deduction of $21,662
  produce total tax of $32,839 against $26,621 of estimates — the $6,218 balance due on screen.
- Money is never rounded. SSNs are always masked. Identifiers are set in mono because
  character-level precision is their function.
- Internal notes are written the way colleagues actually write to each other, including the
  client whose K-1 is late every year, the one whose fee has risen three years running, and
  the one who pays sixty days late and always has.

Written by an IRS AFSP-credentialed preparer with an active EFIN and PTIN, which is why the
reject codes, form numbers, deadlines and fee structures are real rather than approximated.

## Files

```
filed/
├── index.html            source entry point
├── build.mjs             bundles to dist/filed.html
├── DESIGN.md             the design plan and what was revised
└── assets/
    ├── tokens.css        colour, type and spacing tokens, both themes
    ├── app.css           component layer
    ├── data.js           the season: clients, staff, batches, invoices, reject library
    ├── ui.js             store, formatting, toasts, confirmations, command palette
    ├── screens-a.js      cover, season command, roster, client record
    ├── screens-b.js      document chase, return workspace, review, e-file, reject
    ├── screens-c.js      deadline board, portal, team, billing, empty and loading states
    └── app.js            router, chrome, and every action that moves work
```
