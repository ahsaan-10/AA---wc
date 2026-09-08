# FILED — design plan

## Tokens

| Token | Light | Job |
|---|---|---|
| `--bg` | `#E7EAEC` | app ground — cool paper, deliberately not cream and not near-black |
| `--panel` | `#F8FAFA` | panels, tables, the folder body |
| `--accent` | `#16283C` | the one institutional ink: headings, primary buttons, the wordmark |
| `--rule` | `#D3DADC` | ledger hairlines — structure comes from rules, not from shadows |
| `--text-muted` | `#55636F` | secondary text and column headers |

Nine status hues carry the only other colour in the product, one per stage: intake `#4E5C68`,
documents `#8A5600`, preparation `#0A6960`, review `#493EA6`, signature `#A2450A`, transmitted
`#1B5AA8`, accepted `#146239`, rejected `#A61C15`, invoiced `#5C6770`. Diagnostic severity
reuses that set rather than inventing a second one — a blocker is the rejected red, a variance
is the documents ochre, a decision is the transmitted blue. Dark theme redefines every token,
including lifted status hues chosen against the dark ground rather than flipped.

**The rule the product is held to: if a colour on screen does not encode a state, it is removed.**

## Type

**Instrument Sans** across the whole product, 400–700. Chosen over Geist and Switzer because it
is slightly narrow with a tall x-height: at 13px in a forty-row table it stays legible where
Geist gets wide and Switzer gets soft, and it reads institutional rather than startup.
`font-variant-numeric: tabular-nums lining-nums` is set on the body, so every column of money
aligns — misaligned digits in a financial product read as amateur faster than anything else.

**IBM Plex Mono** appears only on identifiers: reject codes, return IDs, invoice numbers, EFIN,
PTIN, masked SSNs. Character-level precision is the actual function in each of those cases.

## Layout

A fixed 224px rail carrying the workflow stages themselves rather than generic navigation, with
live counts; a season bar with the countdown to 15 April pinned to the right; then a ruled
content plane. Density is a professional-tool density — 34px rows, hairline rules, whitespace
from rhythm rather than from padding everything into oblivion.

```
┌────────────┬──────────────────────────────────────────────┐
│ FILED      │ Season command  ·  12 March      ⌘K   34 days │
│ Okonjo &   ├──────────────────────────────────────────────┤
│ Vance      │ Good morning, Danielle                        │
│            │ ┌──────────────────────────────────────────┐  │
│ Console    │ │ open 20 │ risk 6 │ docs 12 │ signed 2 │…│  │
│ · Season   │ └──────────────────────────────────────────┘  │
│ · Deadline │ ┌───────────────────────┬──────────────────┐  │
│ · Team     │ │ Where the season sits │ Preparer capacity│  │
│ · Billing  │ │ ▪ Intake         3 ▬▬ │ Okonjo    ▬▬▬ 93%│  │
│            │ │ ▪ Documents      5 ▬▬▬│ Petrossian▬▬▬ 97%│  │
│ The return │ │ ▪ Preparation    4 ▬▬ │ …                │  │
│ · Roster   │ ├───────────────────────┼──────────────────┤  │
│ · Chase  8 │ │ At risk today         │ Since yesterday  │  │
│ · Review 2 │ │ ▌Ìtan Kitchen — the   │ 8:14 Transmitted…│  │
│ · E-file 4 │ │  capital accounts are │ 7:52 Transmitted…│  │
│ · Portal   │ │  $612 out and the     │ …                │  │
└────────────┴──────────────────────────────────────────────┘
```

## Three principles specific to this product

1. **Status is the only thing colour is allowed to say.** In a stage-based workflow the colour
   budget is spent the moment you tint a card for decoration.
2. **A number that cannot be traced is worse than no number.** Every figure on a screen ties to
   another figure somewhere else — the balance due ties to the line comparison, the stage counts
   tie to the roster, realisation ties to the invoice rows.
3. **The irreversible acts get the friction.** Transmitting to the IRS, writing off a fee and
   signing Form 8879 each take an explicit consent. Everything else is one click and a toast.

## What was revised, and why

- **Stat cards were cut from the dashboard.** The first plan had four large tiles in a shadowed
  grid. That is the default any brief produces. The dashboard now leads with a single ruled
  stage ledger — the counts sit in the workflow order a preparer thinks in, each row is a filter,
  and the bar weights show where the season is banked up. The metric strip that remains is one
  ruled band, not five floating objects.
- **A separate "primary action" accent was dropped.** It would have been a second colour system
  competing with status. The institutional ink does that job, which keeps colour meaning state
  and nothing else.
- **The folder tab became the one flourish rather than one of several.** Cut, skewed, overlapping
  tabs fused into the panel below, on the client record only. Everything around it is quiet so
  that it lands — the brief's boldness is spent once, on the screen the practice manager lives in.
- **The entrance moment is about the data, not the boxes.** Fade-and-slide on every section is
  the tell of a generated page. On entering the console the stage bars draw from zero in workflow
  order, and nothing else animates until a user does something.
