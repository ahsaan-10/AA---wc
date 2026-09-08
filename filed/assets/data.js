/* FILED — season data. Tax year 2025, filed in 2026. Today is Thursday March 12, 2026.
   April 15, 2026 falls on a Wednesday. March 15, 2026 falls on a Sunday, so partnership
   and S-corp returns are due Monday March 16. That date shift is real and the board uses it. */

const SEASON = {
  today: '2026-03-12',
  individualDue: '2026-04-15',
  businessDue: '2026-03-16',
  extendedDue: '2026-10-15',
  taxYear: 2025,
  firm: 'Okonjo & Vance Tax Group',
  efin: '••••93',
  ptin: 'P0••••417',
  /* Season-to-date totals for returns already closed out and off the working roster. */
  closedToDate: { accepted: 386, invoiced: 341, extensions: 52 },
  seasonTotal: 612
};

const STAGES = [
  { key: 'intake',      label: 'Intake',              short: 'Intake' },
  { key: 'docs',        label: 'Documents outstanding', short: 'Documents' },
  { key: 'prep',        label: 'In preparation',      short: 'Preparation' },
  { key: 'review',      label: 'In review',           short: 'Review' },
  { key: 'signature',   label: 'Awaiting signature',  short: 'Signature' },
  { key: 'transmitted', label: 'Transmitted',         short: 'Transmitted' },
  { key: 'accepted',    label: 'IRS accepted',        short: 'Accepted' },
  { key: 'rejected',    label: 'IRS rejected',        short: 'Rejected' },
  { key: 'invoiced',    label: 'Invoiced',            short: 'Invoiced' }
];

const STAFF = [
  { id: 'do', name: 'Danielle Okonjo',        cred: 'EA',   role: 'Practice manager', hoursCap: 34, hoursUsed: 31.5, initials: 'DO' },
  { id: 'mv', name: 'Marcus Vasquez-Reilly',  cred: 'CPA',  role: 'Senior reviewer',  hoursCap: 44, hoursUsed: 41.0, initials: 'MV' },
  { id: 'ap', name: 'Ani Petrossian',         cred: 'EA',   role: 'Preparer',         hoursCap: 45, hoursUsed: 43.5, initials: 'AP' },
  { id: 'yn', name: 'Yuki Nakamura',          cred: 'CPA',  role: 'Preparer, business', hoursCap: 45, hoursUsed: 38.0, initials: 'YN' },
  { id: 'ab', name: 'Adwoa Boateng',          cred: 'AFSP', role: 'Preparer',         hoursCap: 40, hoursUsed: 27.5, initials: 'AB' },
  { id: 'sd', name: 'Simone Delacroix-Hall',  cred: 'EA',   role: 'Preparer, business', hoursCap: 42, hoursUsed: 40.0, initials: 'SD' },
  { id: 'gs', name: 'Grace Sung',             cred: 'CPA',  role: 'Reviewer',         hoursCap: 40, hoursUsed: 22.0, initials: 'GS' },
  { id: 'ra', name: 'Renato Almeida',         cred: 'AFSP', role: 'Preparer, seasonal', hoursCap: 28, hoursUsed: 12.5, initials: 'RA' }
];

/* Genuine IRS Modernized e-File business rules, with the plain-language reading a
   preparer would actually give a client. */
const REJECT_LIBRARY = {
  'IND-031-04': {
    plain: 'The prior-year AGI we sent to authenticate the e-signature does not match what the IRS has on file.',
    official: 'The primary taxpayer’s prior year AGI or Self-Select PIN in the Return Header must match the e-File database.',
    cause: 'Most often the 2024 return was amended, filed late, or still unprocessed when the IRS built its database — so the AGI they hold is not the AGI on the client’s copy.',
    fix: [
      'Pull the 2024 return as originally filed, not the amended copy, and read line 11.',
      'If 2024 was filed after mid-November, enter 0 as the prior-year AGI instead.',
      'Re-enter the AGI in the signature section and retransmit. No new Form 8879 is required — the return itself has not changed.'
    ],
    retransmit: true
  },
  'R0000-500-01': {
    plain: 'The primary taxpayer’s name and SSN do not match Social Security Administration records.',
    official: 'Taxpayer identification number in the Return Header must match e-File database; primary SSN and Primary Name Control mismatch.',
    cause: 'Usually a name change after marriage or divorce that was never filed with the SSA, or a hyphenated surname entered in the wrong order.',
    fix: [
      'Confirm the exact name printed on the client’s Social Security card — not the driver’s licence.',
      'Correct the name control to match the card and retransmit.',
      'If the card itself is out of date, the client files Form SS-5 with the SSA. That takes about two weeks, so file Form 4868 to protect the deadline.'
    ],
    retransmit: true
  },
  'F1040-164-01': {
    plain: 'Earned Income Credit was disallowed in an earlier year, so Form 8862 has to be attached before the IRS will allow it again.',
    official: 'Form 8862 must be present in the return when Earned Income Credit was previously reduced or disallowed.',
    cause: 'The IRS disallowed EIC for this household in a prior year. Until Form 8862 is filed, every subsequent EIC claim rejects automatically.',
    fix: [
      'Confirm with the client which year the credit was disallowed and whether it was disallowed for reckless disregard — that carries a two-year ban.',
      'Add Form 8862, Information to Claim Certain Credits After Disallowance, and complete Part II for each qualifying child.',
      'Retransmit. Expect the refund to take longer than usual; EIC returns with an 8862 attached are routinely held for review.'
    ],
    retransmit: true
  }
};

/* Clients. Occupation is given because it explains the shape of the return. */
const CLIENTS = [
  {
    id: 'RAG-0118', name: 'Priya Raghunathan', kind: 'individual', entity: '1040',
    occupation: 'Freelance cinematographer', business: 'Sixteen Feet Films (sole prop)',
    ssn: '•••-••-4192', filing: 'Single', preparer: 'ap', reviewer: 'mv',
    stage: 'prep', since: '2026-03-05', due: '2026-04-15', fee: 985,
    forms: ['1040', 'Schedule C', 'Schedule SE', 'Form 4562', 'Form 8995'],
    email: 'priya@sixteenfeet.co', phone: '(415) 555-0173', since_year: 2019,
    current: { agi: 124061, result: -6218, refundOrDue: 'due' },
    years: [
      { y: 2024, agi: 121451, result: 3186, fee: 910, filed: '2025-04-02', extended: false },
      { y: 2023, agi: 98274, result: -1842, fee: 845, filed: '2024-03-19', extended: false },
      { y: 2022, agi: 112906, result: 2417, fee: 795, filed: '2023-10-09', extended: true }
    ],
    docs: [
      { form: '1099-NEC', from: 'Cardinal Post LLC', amount: 42500, status: 'in', on: '2026-02-04' },
      { form: '1099-NEC', from: 'Halyard Creative', amount: 61300, status: 'in', on: '2026-02-11' },
      { form: '1099-NEC', from: 'Two Rivers Media', amount: 18750, status: 'in', on: '2026-02-27' },
      { form: 'Equipment purchase invoices', from: 'Client', status: 'in', on: '2026-03-02', note: 'RED Komodo body + two Sigma primes, $31,480 total' },
      { form: '1098', from: 'Bay Federal Credit Union', status: 'in', on: '2026-02-06' },
      { form: 'Mileage log', from: 'Client', status: 'out', requested: '2026-02-18', note: 'Needs the location-shoot log, not the calendar export' }
    ],
    notes: [
      { on: '2026-03-09', by: 'ap', text: 'Bought the Komodo package in November. Asked whether she wants §179 in full or 5-year MACRS — 2026 income looks higher than 2025, so spreading it may be worth more. Waiting on her call.' },
      { on: '2026-02-18', by: 'ab', text: 'Mileage log requested. She keeps it in a notebook in the truck and photographs it, so give her a few days.' }
    ],
    diagnostics: [
      { sev: 'block', code: 'DOC-01', title: 'Mileage log not received', body: 'Schedule C claims 11,240 business miles at $0.70 per mile, $7,868 of deduction, with no substantiating log on file. The return cannot be transmitted with an unsupported vehicle deduction.', action: 'Chase mileage log', link: '#/documents' },
      { sev: 'variance', code: 'VAR-04', title: 'Gross receipts up 34.7% year over year', body: 'Gross receipts of $214,180 against $159,010 in 2024, while estimated payments fell by $8,889. That combination is why a client whose tax barely moved now owes $6,218. Verify the Two Rivers 1099-NEC is 2025 work and not a December 2024 invoice paid in January.', action: 'Add explanation note' },
      { sev: 'attention', code: 'QBI-02', title: 'Section 179 election interacts with QBI', body: 'Electing the full $31,480 under §179 reduces the Form 8995 deduction by $6,296, worth about $1,511 at her marginal rate. Spreading the equipment over five years defers $25,246 of deduction into 2026, when she expects to earn more. Compare both before filing.', action: 'Open comparison' }
    ]
  },
  {
    id: 'HAL-0233', name: 'Bettina & Marc Halverson', kind: 'individual', entity: '1040',
    occupation: 'Hospital administrator / high-school teacher', business: 'Rental duplex, Fremont',
    ssn: '•••-••-7735', filing: 'Married filing jointly', preparer: 'ab', reviewer: 'gs',
    stage: 'review', since: '2026-03-10', due: '2026-04-15', fee: 745,
    forms: ['1040', 'Schedule E', 'Form 4562', 'Schedule A'],
    email: 'bhalverson@outlook.com', phone: '(510) 555-0148', since_year: 2016,
    current: { agi: 218904, result: 3417, refundOrDue: 'refund' },
    years: [
      { y: 2024, agi: 206338, result: 2894, fee: 720, filed: '2025-03-27', extended: false },
      { y: 2023, agi: 194117, result: 4102, fee: 690, filed: '2024-04-01', extended: false },
      { y: 2022, agi: 181662, result: 1523, fee: 655, filed: '2023-03-30', extended: false }
    ],
    docs: [
      { form: 'W-2', from: 'Alta Bates Summit Medical Center', amount: 164200, status: 'in', on: '2026-01-29' },
      { form: 'W-2', from: 'Fremont Unified School District', amount: 79340, status: 'in', on: '2026-01-31' },
      { form: '1098', from: 'Chase Home Lending', status: 'in', on: '2026-02-02' },
      { form: 'Rental income and expense summary', from: 'Client', status: 'in', on: '2026-02-20' }
    ],
    notes: [
      { on: '2026-03-10', by: 'ab', text: 'Passed to Grace. Depreciation schedule for the duplex carried forward clean; the new roof in August is a capital improvement, 27.5-year, not a repair. Flagged it in the review note so nobody re-argues it next year.' }
    ],
    diagnostics: [
      { sev: 'attention', code: 'SCHE-11', title: 'Roof replacement capitalised, not expensed', body: '$18,600 roof replacement placed in service 2025-08-14, depreciated over 27.5 years rather than deducted. Client asked twice about expensing it; the note explains why it cannot be.', action: 'View note' }
    ]
  },
  {
    id: 'ITK-0071', name: 'Ìtan Kitchen LLC', kind: 'business', entity: '1065',
    occupation: 'Restaurant, three partners', business: 'Two locations, Oakland and Emeryville',
    ein: '••-••••8046', filing: 'Partnership', preparer: 'sd', reviewer: 'mv',
    stage: 'review', since: '2026-03-09', due: '2026-03-16', fee: 2940,
    forms: ['Form 1065', 'Schedule K-1 (3)', 'Form 4562', 'Form 8825'],
    email: 'tunde@itankitchen.com', phone: '(510) 555-0192', since_year: 2021,
    current: { agi: 412870, result: 0, refundOrDue: 'passthrough' },
    years: [
      { y: 2024, agi: 358214, result: 0, fee: 2750, filed: '2025-03-14', extended: false },
      { y: 2023, agi: 291455, result: 0, fee: 2400, filed: '2024-09-11', extended: true },
      { y: 2022, agi: 168903, result: 0, fee: 1850, filed: '2023-03-15', extended: false }
    ],
    docs: [
      { form: 'Trial balance', from: 'Client bookkeeper', status: 'in', on: '2026-02-13' },
      { form: 'Partner capital rollforward', from: 'Client', status: 'in', on: '2026-02-24' },
      { form: 'Fixed asset additions', from: 'Client', status: 'in', on: '2026-02-24', note: 'Emeryville build-out, $84,200' }
    ],
    notes: [
      { on: '2026-03-09', by: 'sd', text: 'Four days to the 16th. K-1s reviewed against the capital rollforward; Oyelaran took a $40,000 guaranteed payment mid-year that was booked to draws. Reclassified. All three partners need their K-1 before they can file personally, and Adaeze always files the first week of April.' },
      { on: '2026-02-13', by: 'yn', text: 'Bookkeeper sends the trial balance in a spreadsheet with the prior year in a second tab. Ask for both every year, it saves an hour of tie-out.' }
    ],
    partners: [
      { name: 'Tunde Oyelaran', pct: 45, k1: 185791 },
      { name: 'Adaeze Oyelaran', pct: 35, k1: 144504 },
      { name: 'Femi Adeyemi', pct: 20, k1: 82575 }
    ],
    diagnostics: [
      { sev: 'block', code: 'K1-03', title: 'Partner capital accounts must tie before K-1s issue', body: 'Beginning capital plus contributions and income, less distributions, is $612 off the trial balance for Femi Adeyemi. The 1065 cannot be filed with capital accounts out of balance.', action: 'Open capital rollforward' },
      { sev: 'variance', code: 'VAR-09', title: 'Guaranteed payment reclassified from draws', body: '$40,000 moved from partner draws to guaranteed payments for Tunde Oyelaran. This raises his self-employment income and changes his personal estimate for 2026.', action: 'Add explanation note' }
    ]
  },
  {
    id: 'DUA-0409', name: 'Ismael & Consuelo Duarte', kind: 'individual', entity: '1040',
    occupation: 'Warehouse supervisor / part-time home health aide', business: '',
    ssn: '•••-••-3081', filing: 'Married filing jointly', preparer: 'ab', reviewer: 'do',
    stage: 'rejected', since: '2026-03-11', due: '2026-04-15', fee: 425,
    forms: ['1040', 'Schedule EIC', 'Form 8862', 'Form 2441'],
    email: 'c.duarte91@gmail.com', phone: '(209) 555-0117', since_year: 2022,
    current: { agi: 51740, result: 6842, refundOrDue: 'refund' },
    years: [
      { y: 2024, agi: 48219, result: 5917, fee: 400, filed: '2025-02-14', extended: false },
      { y: 2023, agi: 44860, result: 2103, fee: 375, filed: '2024-02-20', extended: false }
    ],
    docs: [
      { form: 'W-2', from: 'Ridgeline Logistics', amount: 43880, status: 'in', on: '2026-01-24' },
      { form: 'W-2', from: 'Comfort Keepers Home Care', amount: 7860, status: 'in', on: '2026-01-24' },
      { form: 'Childcare provider statement', from: 'Little Acorns Preschool', status: 'in', on: '2026-02-01' }
    ],
    notes: [
      { on: '2026-03-11', by: 'ab', text: 'Rejected on the 8862. Their 2022 EIC was disallowed by an IRS notice they never mentioned to us — Consuelo found the CP75 in a drawer tonight. Not reckless disregard, just a dependent SSN mismatch, so they are not banned. Adding 8862 and retransmitting.' },
      { on: '2026-02-14', by: 'do', text: 'They plan around this refund. Tell them the 8862 adds three to four weeks and tell them today, not the week they expect the deposit.' }
    ],
    reject: {
      code: 'F1040-164-01', batch: 'B-0311-B', transmitted: '2026-03-11T16:22:00',
      rejected: '2026-03-11T16:51:00', attempt: 1
    }
  },
  {
    id: 'STE-0155', name: 'Georg & Lena Steinhauser', kind: 'individual', entity: '1040',
    occupation: 'Staff engineer / pharmacist', business: '',
    ssn: '•••-••-6624', filing: 'Married filing jointly', preparer: 'ap', reviewer: 'mv',
    stage: 'rejected', since: '2026-03-10', due: '2026-04-15', fee: 1240,
    forms: ['1040', 'Form 6251', 'Form 3921', 'Schedule D', 'Schedule B'],
    email: 'g.steinhauser@fastmail.com', phone: '(650) 555-0164', since_year: 2018,
    current: { agi: 486215, result: -14208, refundOrDue: 'due' },
    years: [
      { y: 2024, agi: 402770, result: -8317, fee: 1180, filed: '2025-04-11', extended: false },
      { y: 2023, agi: 388194, result: 2265, fee: 1095, filed: '2024-10-04', extended: true },
      { y: 2022, agi: 351028, result: -3940, fee: 985, filed: '2023-04-06', extended: false }
    ],
    docs: [
      { form: 'W-2', from: 'Vantiq Systems Inc', amount: 341600, status: 'in', on: '2026-02-03' },
      { form: 'W-2', from: 'Sutter Health Pharmacy', amount: 138900, status: 'in', on: '2026-01-30' },
      { form: 'Form 3921', from: 'Vantiq Systems Inc', status: 'in', on: '2026-02-09', note: 'ISO exercise, 14,000 shares' },
      { form: '1099-B', from: 'Fidelity', status: 'in', on: '2026-02-16' }
    ],
    notes: [
      { on: '2026-03-10', by: 'ap', text: 'Name control reject. Lena took Steinhauser at the wedding in October but never filed the SS-5, so the SSA still has Kaczmarek. Filing under her card name this year and she does the SS-5 afterwards. Explained she cannot fix it before April 15.' },
      { on: '2026-02-09', by: 'mv', text: 'ISO exercise held past year end, so AMT applies. The $14,208 balance due is the AMT, not withholding. Warn them in the cover letter, this is the third year running they call about it.' }
    ],
    reject: {
      code: 'R0000-500-01', batch: 'B-0310-A', transmitted: '2026-03-10T09:14:00',
      rejected: '2026-03-10T09:38:00', attempt: 1
    }
  },
  {
    id: 'BAP-0288', name: 'Marcelin Baptiste', kind: 'individual', entity: '1040',
    occupation: 'Rideshare and delivery driver', business: 'Sole prop, no DBA',
    ssn: '•••-••-2907', filing: 'Head of household', preparer: 'ra', reviewer: 'gs',
    stage: 'rejected', since: '2026-03-09', due: '2026-04-15', fee: 510,
    forms: ['1040', 'Schedule C', 'Schedule SE', 'Schedule EIC'],
    email: 'mbaptiste88@yahoo.com', phone: '(510) 555-0129', since_year: 2023,
    current: { agi: 39184, result: 3106, refundOrDue: 'refund' },
    years: [
      { y: 2024, agi: 36402, result: 2871, fee: 485, filed: '2025-03-08', extended: false },
      { y: 2023, agi: 28950, result: 1994, fee: 450, filed: '2024-04-09', extended: false }
    ],
    docs: [
      { form: '1099-NEC', from: 'Uber Technologies', amount: 31480, status: 'in', on: '2026-02-02' },
      { form: '1099-K', from: 'DoorDash', amount: 14260, status: 'in', on: '2026-02-05' },
      { form: 'Mileage log', from: 'Client', status: 'in', on: '2026-02-19', note: '29,415 miles, app export' }
    ],
    notes: [
      { on: '2026-03-09', by: 'ra', text: 'AGI reject. He filed 2024 with a storefront preparer in March last year and does not have the copy. Requested a transcript through e-Services; if the AGI does not come back today we transmit with 0.' }
    ],
    reject: {
      code: 'IND-031-04', batch: 'B-0309-C', transmitted: '2026-03-09T14:05:00',
      rejected: '2026-03-09T14:29:00', attempt: 2
    }
  },
  {
    id: 'TRA-0301', name: 'Minh Trần', kind: 'individual', entity: '1040',
    occupation: 'Software engineer, public company RSUs', business: '',
    ssn: '•••-••-5518', filing: 'Single', preparer: 'ap', reviewer: 'mv',
    stage: 'signature', since: '2026-03-08', due: '2026-04-15', fee: 820,
    forms: ['1040', 'Schedule D', 'Form 8949', 'Schedule B'],
    email: 'minh.tran@hey.com', phone: '(408) 555-0139', since_year: 2020,
    current: { agi: 294517, result: 5904, refundOrDue: 'refund' },
    years: [
      { y: 2024, agi: 271306, result: 4128, fee: 790, filed: '2025-03-21', extended: false },
      { y: 2023, agi: 248872, result: -2016, fee: 745, filed: '2024-03-25', extended: false },
      { y: 2022, agi: 233490, result: 3877, fee: 700, filed: '2023-04-04', extended: false }
    ],
    docs: [
      { form: 'W-2', from: 'Cadence Design Systems', amount: 268400, status: 'in', on: '2026-02-01' },
      { form: '1099-B', from: 'E*TRADE', status: 'in', on: '2026-02-14', note: '41 lots, RSU sell-to-cover' },
      { form: '1099-INT', from: 'Ally Bank', amount: 3417, status: 'in', on: '2026-02-01' }
    ],
    notes: [
      { on: '2026-03-08', by: 'ap', text: '8879 sent 3/8. Basis on the E*TRADE 1099-B was reported without the compensation element on 14 of the 41 lots, adjusted on Form 8949 with code B. Worth $4,880 to him.' }
    ]
  },
  {
    id: 'FER-0177', name: 'Gianna Ferraro DDS', kind: 'business', entity: '1120-S',
    occupation: 'Dentist, single-shareholder practice', business: 'Ferraro Family Dentistry PC',
    ein: '••-••••3315', filing: 'S corporation', preparer: 'yn', reviewer: 'mv',
    stage: 'signature', since: '2026-03-07', due: '2026-03-16', fee: 2185,
    forms: ['Form 1120-S', 'Schedule K-1', 'Form 4562', 'Form 1125-A'],
    email: 'gianna@ferrarodental.com', phone: '(925) 555-0155', since_year: 2017,
    current: { agi: 486300, result: 0, refundOrDue: 'passthrough' },
    years: [
      { y: 2024, agi: 441880, result: 0, fee: 2050, filed: '2025-03-12', extended: false },
      { y: 2023, agi: 398215, result: 0, fee: 1925, filed: '2024-03-13', extended: false },
      { y: 2022, agi: 372640, result: 0, fee: 1800, filed: '2023-03-14', extended: false }
    ],
    docs: [
      { form: 'Trial balance', from: 'Client bookkeeper', status: 'in', on: '2026-02-10' },
      { form: 'Payroll reports Q1–Q4', from: 'Gusto', status: 'in', on: '2026-02-10' },
      { form: 'Equipment financing schedule', from: 'Client', status: 'in', on: '2026-02-21', note: 'CEREC mill, $128,400' }
    ],
    notes: [
      { on: '2026-03-07', by: 'yn', text: 'Reasonable compensation set at $186,000 against $486,300 of net income. Documented against the ADA salary survey for the East Bay so the file supports it if anyone asks.' }
    ]
  },
  {
    id: 'WHI-0142', name: 'Priscilla Whitcombe', kind: 'individual', entity: '1040',
    occupation: 'Retired, beneficiary of a family trust', business: '',
    ssn: '•••-••-8840', filing: 'Single', preparer: 'do', reviewer: 'mv',
    stage: 'docs', since: '2026-02-26', due: '2026-04-15', fee: 690,
    forms: ['1040', 'Schedule B', 'Schedule E', 'Schedule D'],
    email: 'pwhitcombe@comcast.net', phone: '(415) 555-0182', since_year: 2014,
    current: { agi: 0, result: 0, refundOrDue: 'unknown' },
    years: [
      { y: 2024, agi: 168742, result: -4915, fee: 665, filed: '2025-04-08', extended: false },
      { y: 2023, agi: 155380, result: -3702, fee: 640, filed: '2024-10-11', extended: true },
      { y: 2022, agi: 149217, result: 1108, fee: 615, filed: '2023-10-06', extended: true }
    ],
    docs: [
      { form: '1099-DIV', from: 'Schwab', amount: 22418, status: 'in', on: '2026-02-11' },
      { form: '1099-B', from: 'Schwab', status: 'in', on: '2026-02-11' },
      { form: 'SSA-1099', from: 'Social Security Administration', amount: 41436, status: 'in', on: '2026-01-27' },
      { form: 'Schedule K-1 (1041)', from: 'Whitcombe Family Trust', status: 'out', requested: '2026-02-26', note: 'Trustee is Bickford & Lyle; they issue in the last week of March every year' }
    ],
    notes: [
      { on: '2026-02-26', by: 'do', text: 'K-1 comes late every year from Bickford & Lyle. Do not chase before 3/20, it annoys her and they will not move faster. If it is not here by 4/1 we extend on 4868 and she pays the estimate.' }
    ]
  },
  {
    id: 'AMA-0356', name: 'Nana Amankwah', kind: 'individual', entity: '1040',
    occupation: 'Travel nurse, four states', business: '',
    ssn: '•••-••-1263', filing: 'Single', preparer: 'ab', reviewer: 'gs',
    stage: 'docs', since: '2026-03-02', due: '2026-04-15', fee: 875,
    forms: ['1040', 'CA 540NR', 'AZ 140NR', 'OR 40-N', 'WA (no filing)'],
    email: 'n.amankwah@protonmail.com', phone: '(503) 555-0198', since_year: 2022,
    current: { agi: 0, result: 0, refundOrDue: 'unknown' },
    years: [
      { y: 2024, agi: 138905, result: 2274, fee: 840, filed: '2025-04-10', extended: false },
      { y: 2023, agi: 129440, result: 1856, fee: 795, filed: '2024-04-12', extended: false }
    ],
    docs: [
      { form: 'W-2', from: 'Aya Healthcare', amount: 96300, status: 'in', on: '2026-02-05' },
      { form: 'W-2', from: 'Cross Country Nurses', amount: 44180, status: 'in', on: '2026-02-05' },
      { form: 'Assignment itinerary with dates', from: 'Client', status: 'out', requested: '2026-03-02', note: 'Needed to allocate wages by state; the W-2s do not split Oregon correctly' },
      { form: 'Housing stipend documentation', from: 'Client', status: 'out', requested: '2026-03-02', note: 'Confirm she maintained the Portland apartment all year, otherwise the stipends are taxable' }
    ],
    notes: [
      { on: '2026-03-02', by: 'ab', text: 'Cross Country reported everything to Arizona including the six weeks in Bend. Cannot start the state returns until the itinerary arrives.' }
    ]
  },
  {
    id: 'SEP-0264', name: 'Camila Sepúlveda-Ortiz', kind: 'individual', entity: '1040',
    occupation: 'Residential realtor', business: 'Sepúlveda-Ortiz Properties (sole prop)',
    ssn: '•••-••-9074', filing: 'Married filing jointly', preparer: 'ra', reviewer: 'gs',
    stage: 'docs', since: '2026-02-24', due: '2026-04-15', fee: 795,
    forms: ['1040', 'Schedule C', 'Schedule SE', 'Form 8995'],
    email: 'camila@sopropertiesbay.com', phone: '(925) 555-0121', since_year: 2019,
    current: { agi: 0, result: 0, refundOrDue: 'unknown' },
    years: [
      { y: 2024, agi: 174288, result: -5211, fee: 760, filed: '2025-04-14', extended: false },
      { y: 2023, agi: 208650, result: -7043, fee: 735, filed: '2024-04-15', extended: false },
      { y: 2022, agi: 241905, result: -9188, fee: 690, filed: '2023-04-13', extended: false }
    ],
    docs: [
      { form: '1099-NEC', from: 'Compass California', amount: 148700, status: 'in', on: '2026-02-08' },
      { form: 'Mileage log', from: 'Client', status: 'out', requested: '2026-02-24' },
      { form: 'Home office square footage', from: 'Client', status: 'out', requested: '2026-02-24', note: 'She moved in June; needs both addresses and the months at each' },
      { form: 'Estimated tax payment record', from: 'Client', status: 'out', requested: '2026-03-03', note: 'She pays by card and never keeps confirmations. Pull the IRS account transcript if she cannot find them.' }
    ],
    notes: [
      { on: '2026-03-03', by: 'ra', text: 'Third year of declining commission income. She has not adjusted her estimates down and overpaid Q1 and Q2 by roughly $4,400 between them. Worth a conversation about 2026 rather than just filing this.' },
      { on: '2026-02-24', by: 'ra', text: 'Always files on the deadline. Not disorganised, she just does not open the portal until the first week of April.' }
    ]
  },
  {
    id: 'MAR-0339', name: 'Dario Marchetti', kind: 'individual', entity: '1040',
    occupation: 'Concrete contractor', business: 'Marchetti Flatwork',
    ssn: '•••-••-4406', filing: 'Married filing jointly', preparer: 'sd', reviewer: 'mv',
    stage: 'docs', since: '2026-02-20', due: '2026-04-15', fee: 1150,
    forms: ['1040', 'Schedule C', 'Form 4562', 'Schedule SE', 'Form 8995'],
    email: 'dario@marchettiflatwork.com', phone: '(707) 555-0166', since_year: 2015,
    current: { agi: 0, result: 0, refundOrDue: 'unknown' },
    years: [
      { y: 2024, agi: 196470, result: -12905, fee: 1085, filed: '2025-09-29', extended: true },
      { y: 2023, agi: 182335, result: -10442, fee: 1020, filed: '2024-10-08', extended: true },
      { y: 2022, agi: 158720, result: -6817, fee: 940, filed: '2023-10-12', extended: true }
    ],
    docs: [
      { form: 'Bank statements Jan–Dec', from: 'Client', status: 'in', on: '2026-02-19' },
      { form: '1099-NEC (subcontractors issued)', from: 'Client', status: 'in', on: '2026-02-19' },
      { form: 'Equipment purchase — skid steer', from: 'Client', status: 'out', requested: '2026-02-20', note: 'Financed through Bobcat; needs the contract, not the invoice' },
      { form: 'Vehicle log for the F-350', from: 'Client', status: 'out', requested: '2026-02-27' }
    ],
    notes: [
      { on: '2026-02-27', by: 'sd', text: 'Extends every year and always has. Do not spend March hours on this one; he will not have the skid steer paperwork until his lender sends the year-end statement.' }
    ]
  },
  {
    id: 'OSE-0207', name: 'Kwabena Osei-Tutu', kind: 'individual', entity: '1040',
    occupation: 'Franchise owner, two quick-service locations', business: 'K-Squared Restaurants',
    ssn: '•••-••-6152', filing: 'Married filing jointly', preparer: 'yn', reviewer: 'mv',
    stage: 'docs', since: '2026-03-01', due: '2026-04-15', fee: 1385,
    forms: ['1040', 'Schedule E', 'Schedule K-1 (2)', 'Form 8995'],
    email: 'kosei@ksquaredrest.com', phone: '(916) 555-0187', since_year: 2018,
    current: { agi: 0, result: 0, refundOrDue: 'unknown' },
    years: [
      { y: 2024, agi: 264180, result: -8422, fee: 1310, filed: '2025-09-15', extended: true },
      { y: 2023, agi: 238904, result: -6015, fee: 1245, filed: '2024-09-20', extended: true }
    ],
    docs: [
      { form: 'Schedule K-1 (1065) — Elmhurst', from: 'K-Squared Elmhurst LLC', status: 'in', on: '2026-03-04' },
      { form: 'Schedule K-1 (1065) — Del Paso', from: 'K-Squared Del Paso LLC', status: 'out', requested: '2026-03-01', note: 'Prepared in-house by Simone; blocked on the same trial balance as Ìtan' },
      { form: 'W-2', from: 'K-Squared Management', amount: 92000, status: 'in', on: '2026-02-06' }
    ],
    notes: [
      { on: '2026-03-04', by: 'yn', text: 'His personal return cannot go anywhere until Del Paso issues. That is our own K-1, so it is on us, not on him. Do not send him a document chase for it.' }
    ]
  },
  {
    id: 'KOW-0125', name: 'Irena Kowalczyk', kind: 'individual', entity: '1040',
    occupation: 'Retired machinist', business: '',
    ssn: '•••-••-3390', filing: 'Qualifying surviving spouse', preparer: 'ab', reviewer: 'gs',
    stage: 'accepted', since: '2026-03-06', due: '2026-04-15', fee: 385,
    forms: ['1040', 'Schedule B'],
    email: 'ikowalczyk@aol.com', phone: '(510) 555-0104', since_year: 2011,
    current: { agi: 62148, result: 1204, refundOrDue: 'refund' },
    years: [
      { y: 2024, agi: 60377, result: 1096, fee: 370, filed: '2025-02-28', extended: false },
      { y: 2023, agi: 58940, result: 942, fee: 355, filed: '2024-03-04', extended: false },
      { y: 2022, agi: 57216, result: 1387, fee: 340, filed: '2023-03-02', extended: false }
    ],
    docs: [
      { form: '1099-R', from: 'Boilermakers National Pension', amount: 38400, status: 'in', on: '2026-01-22' },
      { form: 'SSA-1099', from: 'Social Security Administration', amount: 27108, status: 'in', on: '2026-01-22' }
    ],
    notes: [
      { on: '2026-03-06', by: 'ab', text: 'Accepted 3/6. She mails a cheque for the fee within a week, every year, and does not use the portal. Print the copy and post it.' }
    ],
    ack: { batch: 'B-0306-A', transmitted: '2026-03-06T08:31:00', accepted: '2026-03-06T09:12:00' }
  },
  {
    id: 'NWO-0372', name: 'Chidera Nwosu', kind: 'individual', entity: '1040',
    occupation: 'PhD candidate, materials science', business: '',
    ssn: '•••-••-7719', filing: 'Single', preparer: 'ra', reviewer: 'gs',
    stage: 'accepted', since: '2026-03-04', due: '2026-04-15', fee: 295,
    forms: ['1040', 'Form 8863', 'Schedule 1'],
    email: 'cnwosu@berkeley.edu', phone: '(510) 555-0143', since_year: 2024,
    current: { agi: 41620, result: 1873, refundOrDue: 'refund' },
    years: [
      { y: 2024, agi: 38105, result: 1642, fee: 285, filed: '2025-03-11', extended: false }
    ],
    docs: [
      { form: 'W-2', from: 'UC Berkeley', amount: 39400, status: 'in', on: '2026-01-28' },
      { form: '1098-T', from: 'UC Berkeley', status: 'in', on: '2026-02-03' },
      { form: '1099-INT', from: 'Chase', amount: 218, status: 'in', on: '2026-02-03' }
    ],
    notes: [
      { on: '2026-03-04', by: 'ra', text: 'Fellowship portion in box 5 exceeds qualified expenses in box 1 by $2,220, so that much is taxable on Schedule 1. Explained it in the cover letter; she asked good questions and will not need it explained again next year.' }
    ],
    ack: { batch: 'B-0304-B', transmitted: '2026-03-04T13:40:00', accepted: '2026-03-04T14:03:00' }
  },
  {
    id: 'BRA-0311', name: 'Sean Brannigan', kind: 'individual', entity: '1040',
    occupation: 'Union electrician, IBEW Local 595', business: '',
    ssn: '•••-••-2248', filing: 'Single', preparer: 'ab', reviewer: 'gs',
    stage: 'accepted', since: '2026-03-05', due: '2026-04-15', fee: 465,
    forms: ['1040', 'Form 8962', 'Schedule 2'],
    email: 'sbrannigan595@gmail.com', phone: '(510) 555-0159', since_year: 2020,
    current: { agi: 88410, result: -1932, refundOrDue: 'due' },
    years: [
      { y: 2024, agi: 79265, result: 618, fee: 445, filed: '2025-03-18', extended: false },
      { y: 2023, agi: 71880, result: 1247, fee: 420, filed: '2024-03-15', extended: false }
    ],
    docs: [
      { form: 'W-2', from: 'Rosendin Electric', amount: 86200, status: 'in', on: '2026-01-31' },
      { form: '1095-A', from: 'Covered California', status: 'in', on: '2026-02-12', note: 'Only covered Jan–Apr before he went back on the union plan' }
    ],
    notes: [
      { on: '2026-03-05', by: 'ab', text: 'Advance premium credit has to be reconciled on 8962 even though he was only on the marketplace four months. Income came in higher than his estimate, so $1,932 of it is repayable. He took it well.' }
    ],
    ack: { batch: 'B-0305-A', transmitted: '2026-03-05T10:18:00', accepted: '2026-03-05T10:47:00' }
  },
  {
    id: 'YAM-0284', name: 'Lani Yamashiro', kind: 'individual', entity: '1040',
    occupation: 'Hairstylist, booth rental', business: 'Chair 4 at Ruby Salon',
    ssn: '•••-••-5061', filing: 'Single', preparer: 'ra', reviewer: 'gs',
    stage: 'transmitted', since: '2026-03-12', due: '2026-04-15', fee: 545,
    forms: ['1040', 'Schedule C', 'Schedule SE'],
    email: 'lani.yamashiro@icloud.com', phone: '(808) 555-0113', since_year: 2021,
    current: { agi: 58730, result: -2841, refundOrDue: 'due' },
    years: [
      { y: 2024, agi: 54118, result: -2205, fee: 520, filed: '2025-04-07', extended: false },
      { y: 2023, agi: 49604, result: -1730, fee: 495, filed: '2024-04-05', extended: false }
    ],
    docs: [
      { form: '1099-NEC', from: 'Ruby Salon Holdings', amount: 12400, status: 'in', on: '2026-02-07' },
      { form: 'Booth rent receipts', from: 'Client', status: 'in', on: '2026-02-25' },
      { form: 'Product and supply receipts', from: 'Client', status: 'in', on: '2026-02-25' }
    ],
    notes: [
      { on: '2026-03-12', by: 'ra', text: 'Transmitted 7:52 this morning, waiting on the acknowledgment. She wants to pay the balance by 4/15 rather than now, so the direct debit is scheduled, not immediate.' }
    ],
    ack: { batch: 'B-0312-A', transmitted: '2026-03-12T07:52:00', accepted: null }
  },
  {
    id: 'KAR-0198', name: 'Vahe Karapetyan', kind: 'business', entity: '1120-S',
    occupation: 'Auto body shop owner', business: 'Golden Gate Collision Inc',
    ein: '••-••••7702', filing: 'S corporation', preparer: 'sd', reviewer: 'mv',
    stage: 'transmitted', since: '2026-03-12', due: '2026-03-16', fee: 1875,
    forms: ['Form 1120-S', 'Schedule K-1', 'Form 4562', 'Form 1125-A'],
    email: 'vahe@ggcollision.com', phone: '(415) 555-0176', since_year: 2016,
    current: { agi: 318420, result: 0, refundOrDue: 'passthrough' },
    years: [
      { y: 2024, agi: 289655, result: 0, fee: 1780, filed: '2025-03-11', extended: false },
      { y: 2023, agi: 302118, result: 0, fee: 1700, filed: '2024-03-12', extended: false },
      { y: 2022, agi: 275940, result: 0, fee: 1625, filed: '2023-03-10', extended: false }
    ],
    docs: [
      { form: 'Trial balance', from: 'Client bookkeeper', status: 'in', on: '2026-02-17' },
      { form: 'Payroll reports Q1–Q4', from: 'ADP', status: 'in', on: '2026-02-17' },
      { form: 'Shop equipment additions', from: 'Client', status: 'in', on: '2026-02-27', note: 'Frame machine, $46,900' }
    ],
    notes: [
      { on: '2026-03-12', by: 'sd', text: 'Transmitted 8:14. Four days ahead of the 16th, which for him is a record.' }
    ],
    ack: { batch: 'B-0312-A', transmitted: '2026-03-12T08:14:00', accepted: null }
  },
  {
    id: 'ASH-0221', name: 'Grant & Yvette Ashworth-Lemieux', kind: 'individual', entity: '1040',
    occupation: 'Anaesthesiologist / at home with two children', business: '',
    ssn: '•••-••-8317', filing: 'Married filing jointly', preparer: 'ap', reviewer: 'mv',
    stage: 'signature', since: '2026-03-09', due: '2026-04-15', fee: 1095,
    forms: ['1040', 'Form 8606', 'Schedule A', 'Form 2441'],
    email: 'yvette.al@gmail.com', phone: '(650) 555-0191', since_year: 2017,
    current: { agi: 612840, result: -4106, refundOrDue: 'due' },
    years: [
      { y: 2024, agi: 588315, result: -3277, fee: 1040, filed: '2025-04-09', extended: false },
      { y: 2023, agi: 561902, result: 2841, fee: 985, filed: '2024-04-11', extended: false },
      { y: 2022, agi: 534470, result: -5192, fee: 930, filed: '2023-04-14', extended: false }
    ],
    docs: [
      { form: 'W-2', from: 'Peninsula Anesthesia Medical Group', amount: 604200, status: 'in', on: '2026-02-04' },
      { form: 'Form 5498 / backdoor Roth confirmations', from: 'Vanguard', status: 'in', on: '2026-02-20' },
      { form: 'Childcare provider statement', from: 'Bright Horizons', status: 'in', on: '2026-02-10' }
    ],
    notes: [
      { on: '2026-03-09', by: 'ap', text: 'Backdoor Roth for both, $7,000 each, non-deductible basis tracked on 8606. Grant had a $312 dividend in the traditional IRA before conversion, so the pro-rata rule bites slightly. 8879 out 3/9.' }
    ]
  },
  {
    id: 'VIL-0295', name: 'Rosa Villalobos', kind: 'individual', entity: '1040',
    occupation: 'Licensed home daycare provider', business: 'Casita Azul Family Child Care',
    ssn: '•••-••-6633', filing: 'Married filing jointly', preparer: 'ab', reviewer: 'gs',
    stage: 'prep', since: '2026-03-06', due: '2026-04-15', fee: 720,
    forms: ['1040', 'Schedule C', 'Form 8829', 'Schedule SE'],
    email: 'rosa.casitaazul@gmail.com', phone: '(510) 555-0138', since_year: 2019,
    current: { agi: 84206, result: 1519, refundOrDue: 'refund' },
    years: [
      { y: 2024, agi: 79881, result: 1204, fee: 690, filed: '2025-03-29', extended: false },
      { y: 2023, agi: 74350, result: 2016, fee: 660, filed: '2024-03-26', extended: false }
    ],
    docs: [
      { form: 'Parent payment records', from: 'Client', status: 'in', on: '2026-02-15' },
      { form: 'Food program reimbursement (CACFP)', from: 'Client', status: 'in', on: '2026-02-15' },
      { form: 'Home square footage and hours log', from: 'Client', status: 'in', on: '2026-03-01' }
    ],
    notes: [
      { on: '2026-03-06', by: 'ab', text: 'Time-space percentage recalculated at 34.8% — she extended hours to 6pm in September. Standard meal rate used rather than receipts, which is both correct and much faster.' }
    ],
    diagnostics: [
      { sev: 'attention', code: '8829-02', title: 'Time-space percentage changed mid-year', body: 'Hours of use rose from 2,704 to 3,196 in September. The 34.8% figure uses the full-year average, which is the method used in 2024 and 2023.', action: 'View calculation' }
    ]
  },
  {
    id: 'OKA-0163', name: 'Rina Okamoto', kind: 'individual', entity: '1040',
    occupation: 'Retired teacher, one rental condo', business: '',
    ssn: '•••-••-4471', filing: 'Single', preparer: 'ab', reviewer: 'gs',
    stage: 'prep', since: '2026-03-07', due: '2026-04-15', fee: 640,
    forms: ['1040', 'Schedule E', 'Form 4562'],
    email: 'rina.okamoto@sbcglobal.net', phone: '(408) 555-0126', since_year: 2013,
    current: { agi: 91375, result: 842, refundOrDue: 'refund' },
    years: [
      { y: 2024, agi: 88104, result: 1173, fee: 615, filed: '2025-03-24', extended: false },
      { y: 2023, agi: 85662, result: 906, fee: 595, filed: '2024-03-22', extended: false },
      { y: 2022, agi: 83019, result: -418, fee: 570, filed: '2023-03-27', extended: false }
    ],
    docs: [
      { form: '1099-R', from: 'CalSTRS', amount: 64800, status: 'in', on: '2026-01-26' },
      { form: 'Rental income and expense summary', from: 'Client', status: 'in', on: '2026-02-22' },
      { form: '1098', from: 'Wells Fargo', status: 'in', on: '2026-02-03' }
    ],
    notes: [
      { on: '2026-03-07', by: 'ab', text: 'Condo vacant seven weeks between tenants. Still available for rent the whole time, so the expenses stay deductible; noted in case it is ever questioned.' }
    ],
    diagnostics: [
      { sev: 'variance', code: 'VAR-02', title: 'Rental income down 13.4%', body: 'Gross rents of $31,850 against $36,780 in 2024, explained by seven vacant weeks between tenants in June and July. Expenses were unchanged.', action: 'Add explanation note' }
    ]
  },
  {
    id: 'ZAY-0347', name: 'Hala Zaydan', kind: 'individual', entity: '1040',
    occupation: 'Bakery owner, single-member LLC', business: 'Beit Halawa Bakery LLC',
    ssn: '•••-••-7128', filing: 'Married filing jointly', preparer: 'sd', reviewer: 'mv',
    stage: 'prep', since: '2026-03-08', due: '2026-04-15', fee: 1290,
    forms: ['1040', 'Schedule C', 'Form 4562', 'Form 8995', 'Schedule SE'],
    email: 'hala@beithalawa.com', phone: '(510) 555-0184', since_year: 2020,
    current: { agi: 108492, result: -3714, refundOrDue: 'due' },
    years: [
      { y: 2024, agi: 96218, result: -2905, fee: 1215, filed: '2025-04-08', extended: false },
      { y: 2023, agi: 71440, result: -1188, fee: 1120, filed: '2024-04-10', extended: false },
      { y: 2022, agi: 43907, result: 1602, fee: 950, filed: '2023-04-03', extended: false }
    ],
    docs: [
      { form: 'QuickBooks year-end file', from: 'Client', status: 'in', on: '2026-02-23' },
      { form: 'Oven purchase and installation', from: 'Client', status: 'in', on: '2026-02-23', note: 'Deck oven, $27,600, in service 2025-05-19' },
      { form: 'Payroll reports', from: 'Square Payroll', status: 'in', on: '2026-02-23' }
    ],
    notes: [
      { on: '2026-03-08', by: 'sd', text: 'Third consecutive year of growth and the fee has moved with it — $950, $1,120, $1,215, now $1,290. She has never once queried it, but tell her before the invoice goes out rather than after.' }
    ],
    diagnostics: [
      { sev: 'attention', code: 'DEP-05', title: '§179 limited by business income', body: 'The $27,600 oven fully expensed under §179 would exceed business income by $1,840. The excess carries forward; bonus depreciation on the remainder is the alternative.', action: 'Open comparison' }
    ]
  },
  {
    id: 'FIT-0109', name: 'Dorothy Fitzhugh', kind: 'individual', entity: '1040',
    occupation: 'Retired, age 88', business: '',
    ssn: '•••-••-2085', filing: 'Single', preparer: 'do', reviewer: 'gs',
    stage: 'intake', since: '2026-03-11', due: '2026-04-15', fee: 520,
    forms: ['1040', 'Schedule B', 'Schedule A'],
    email: 'via daughter: k.fitzhugh@gmail.com', phone: '(925) 555-0102', since_year: 2009,
    current: { agi: 0, result: 0, refundOrDue: 'unknown' },
    years: [
      { y: 2024, agi: 104882, result: -2146, fee: 500, filed: '2025-04-01', extended: false },
      { y: 2023, agi: 101397, result: -1873, fee: 485, filed: '2024-03-30', extended: false },
      { y: 2022, agi: 99205, result: 1240, fee: 465, filed: '2023-04-04', extended: false }
    ],
    docs: [
      { form: 'Prior-year return', from: 'Client', status: 'in', on: '2026-03-11' }
    ],
    notes: [
      { on: '2026-03-11', by: 'do', text: 'Her daughter Karen handles the paperwork now and has a signed 2848 on file. Send everything to Karen, call Dorothy. The QCD of $8,000 to St Anne’s does not show on the 1099-R, so ask for the letter before anyone starts.' }
    ]
  },
  {
    id: 'LIN-0388', name: 'Annika Lindqvist', kind: 'individual', entity: '1040',
    occupation: 'Product design contractor, US and Sweden', business: 'Lindqvist Studio (sole prop)',
    ssn: '•••-••-9530', filing: 'Single', preparer: 'ap', reviewer: 'mv',
    stage: 'intake', since: '2026-03-10', due: '2026-04-15', fee: 1420,
    forms: ['1040', 'Schedule C', 'Form 1116', 'FinCEN 114', 'Schedule SE'],
    email: 'annika@lindqvist.studio', phone: '(415) 555-0150', since_year: 2026,
    current: { agi: 0, result: 0, refundOrDue: 'unknown' },
    years: [
      { y: 2024, agi: 162740, result: -4318, fee: 1350, filed: '2025-10-14', extended: true }
    ],
    docs: [
      { form: 'Engagement letter, signed', from: 'Client', status: 'in', on: '2026-03-10' },
      { form: 'Foreign account balances — highest 2025', from: 'Client', status: 'out', requested: '2026-03-10', note: 'Needed for FinCEN 114; the Handelsbanken account was over $10,000 for most of the year' }
    ],
    notes: [
      { on: '2026-03-10', by: 'do', text: 'New client this season, referred by Minh Trần. Her 2024 return was prepared in Stockholm and the copy we hold is a translation, so do not rely on it for carryforwards without asking.' },
      { on: '2026-03-10', by: 'ap', text: 'FBAR is due 4/15 with an automatic extension to 10/15, but file it with the return rather than leaving it hanging. Foreign tax credit on the Swedish work, not the exclusion — she was in the US 291 days.' }
    ]
  },
  {
    id: 'ACH-0257', name: 'Pieter Achterberg', kind: 'individual', entity: '1040',
    occupation: 'Active securities trader', business: 'Achterberg Capital (sole prop)',
    ssn: '•••-••-1174', filing: 'Single', preparer: 'ap', reviewer: 'mv',
    stage: 'invoiced', since: '2026-03-03', due: '2026-04-15', fee: 1680,
    forms: ['1040', 'Schedule D', 'Form 8949', 'Schedule C'],
    email: 'p.achterberg@fastmail.nl', phone: '(415) 555-0195', since_year: 2021,
    current: { agi: 227918, result: -9433, refundOrDue: 'due' },
    years: [
      { y: 2024, agi: 341206, result: -18740, fee: 1595, filed: '2025-04-12', extended: false },
      { y: 2023, agi: 88415, result: 6320, fee: 1480, filed: '2024-04-08', extended: false },
      { y: 2022, agi: 194077, result: -7188, fee: 1395, filed: '2023-04-11', extended: false }
    ],
    docs: [
      { form: '1099-B', from: 'Interactive Brokers', status: 'in', on: '2026-02-18', note: '2,847 transactions, imported' },
      { form: '1099-B', from: 'Tastytrade', status: 'in', on: '2026-02-18' }
    ],
    notes: [
      { on: '2026-03-03', by: 'ap', text: 'Wash sales of $41,662 disallowed across the two brokers — IB reports its own but not the cross-broker matches, so those were adjusted by hand. He has asked about a §475(f) mark-to-market election for 2026; that has to be filed by 4/15/2026, so raise it now or it waits a year.' },
      { on: '2026-03-03', by: 'do', text: 'Pays late every year, usually 60 days. Not a collection problem, just how he works. Invoice went out with the return rather than after acceptance.' }
    ],
    ack: { batch: 'B-0303-A', transmitted: '2026-03-03T11:22:00', accepted: '2026-03-03T11:58:00' }
  },
  {
    id: 'OYE-0091', name: 'Tunde Oyelaran', kind: 'individual', entity: '1040',
    occupation: 'Restaurateur, 45% partner in Ìtan Kitchen', business: '',
    ssn: '•••-••-3364', filing: 'Married filing jointly', preparer: 'yn', reviewer: 'mv',
    stage: 'intake', since: '2026-03-12', due: '2026-04-15', fee: 985,
    forms: ['1040', 'Schedule E', 'Schedule K-1', 'Form 8995'],
    email: 'tunde@itankitchen.com', phone: '(510) 555-0192', since_year: 2026,
    current: { agi: 0, result: 0, refundOrDue: 'unknown' },
    years: [
      { y: 2024, agi: 214508, result: -11290, fee: 940, filed: '2025-09-30', extended: true },
      { y: 2023, agi: 176220, result: -8104, fee: 890, filed: '2024-10-01', extended: true }
    ],
    docs: [
      { form: 'Schedule K-1 (1065)', from: 'Ìtan Kitchen LLC', status: 'out', requested: '2026-03-09', note: 'Prepared in-house by Simone; blocked on the capital account tie-out' },
      { form: 'W-2 (spouse)', from: 'Kaiser Permanente', amount: 108400, status: 'in', on: '2026-02-02' }
    ],
    notes: [
      { on: '2026-03-09', by: 'do', text: 'Ìtan has been a client since 2021 but Tunde kept his personal return with his old accountant. He moved it to us this season, so 2024 and 2023 on file are copies, not our work.' },
      { on: '2026-03-12', by: 'yn', text: 'The guaranteed payment reclass adds roughly $40,000 of self-employment income to his personal return. He needs to hear that number from Simone before he sees the balance due, not after.' }
    ]
  },
  {
    id: 'FIN-0413', name: 'Elodie Finch-Barrow', kind: 'individual', entity: '1040',
    occupation: 'Veterinarian, associate at two practices', business: '',
    ssn: '•••-••-6809', filing: 'Single', preparer: 'ra', reviewer: 'gs',
    stage: 'invoiced', since: '2026-03-02', due: '2026-04-15', fee: 585,
    forms: ['1040', 'Schedule A', 'Schedule 1'],
    email: 'efinchbarrow@gmail.com', phone: '(707) 555-0172', since_year: 2022,
    current: { agi: 138265, result: 2417, refundOrDue: 'refund' },
    years: [
      { y: 2024, agi: 129840, result: 1975, fee: 560, filed: '2025-03-16', extended: false },
      { y: 2023, agi: 118305, result: 3082, fee: 535, filed: '2024-03-19', extended: false }
    ],
    docs: [
      { form: 'W-2', from: 'Bayside Veterinary Group', amount: 96200, status: 'in', on: '2026-01-30' },
      { form: 'W-2', from: 'Sonoma Animal Hospital', amount: 44800, status: 'in', on: '2026-02-02' },
      { form: 'Student loan interest statement', from: 'Nelnet', amount: 2712, status: 'in', on: '2026-02-06' }
    ],
    notes: [
      { on: '2026-03-02', by: 'ra', text: 'Student loan interest phases out entirely at this AGI. Left it off rather than entering it and letting the software zero it, so the return matches what she will read.' }
    ],
    ack: { batch: 'B-0302-A', transmitted: '2026-03-02T15:47:00', accepted: '2026-03-02T16:11:00' }
  }
];

/* Form 8879 signature tracking. A return cannot be transmitted without one on file. */
const SIGNATURES = {
  'TRA-0301': { sent: '2026-03-08T16:20:00', signed: '2026-03-11T21:47:00', method: 'Portal e-signature', ip: '73.202.14.88' },
  'FER-0177': { sent: '2026-03-07T11:05:00', signed: '2026-03-10T08:12:00', method: 'Portal e-signature', ip: '104.28.61.7' },
  'ASH-0221': { sent: '2026-03-09T17:40:00', signed: null, method: 'Portal e-signature', ip: null },
  'YAM-0284': { sent: '2026-03-10T09:30:00', signed: '2026-03-11T19:03:00', method: 'Portal e-signature', ip: '24.130.55.201' },
  'KAR-0198': { sent: '2026-03-10T14:15:00', signed: '2026-03-11T16:38:00', method: 'Portal e-signature', ip: '68.4.112.63' },
  'DUA-0409': { sent: '2026-03-10T12:00:00', signed: '2026-03-11T07:22:00', method: 'In office, wet signature', ip: null },
  'STE-0155': { sent: '2026-03-09T10:44:00', signed: '2026-03-09T18:15:00', method: 'Portal e-signature', ip: '76.21.98.140' },
  'BAP-0288': { sent: '2026-03-06T13:12:00', signed: '2026-03-08T11:05:00', method: 'Portal e-signature', ip: '107.77.203.19' }
};

/* Transmission batches. The firm transmits in batches through the morning. */
const BATCHES = [
  { id: 'B-0312-A', sent: '2026-03-12T07:52:00', count: 2, returns: ['YAM-0284', 'KAR-0198'], state: 'pending', note: 'Awaiting acknowledgment. The IRS typically acknowledges within 45 minutes.' },
  { id: 'B-0311-B', sent: '2026-03-11T16:22:00', count: 4, returns: ['DUA-0409'], state: 'mixed', note: '3 accepted, 1 rejected.' },
  { id: 'B-0310-A', sent: '2026-03-10T09:14:00', count: 6, returns: ['STE-0155'], state: 'mixed', note: '5 accepted, 1 rejected.' },
  { id: 'B-0309-C', sent: '2026-03-09T14:05:00', count: 3, returns: ['BAP-0288'], state: 'mixed', note: '2 accepted, 1 rejected on the second attempt.' },
  { id: 'B-0306-A', sent: '2026-03-06T08:31:00', count: 5, returns: ['KOW-0125'], state: 'accepted', note: 'All accepted.' },
  { id: 'B-0305-A', sent: '2026-03-05T10:18:00', count: 7, returns: ['BRA-0311'], state: 'accepted', note: 'All accepted.' }
];

/* Invoices. Standard fee is the schedule; billed is what went out. */
const INVOICES = [
  { no: 'INV-2026-0418', client: 'ACH-0257', issued: '2026-03-03', standard: 1680, billed: 1680, paid: 0,   status: 'overdue',  terms: 'Net 15', writeOff: 0,   note: 'Pays around 60 days every year. Second reminder 3/24.' },
  { no: 'INV-2026-0402', client: 'FIN-0413', issued: '2026-03-02', standard: 585,  billed: 585,  paid: 585, status: 'paid',     terms: 'Net 15', writeOff: 0,   note: '' },
  { no: 'INV-2026-0431', client: 'KOW-0125', issued: '2026-03-06', standard: 385,  billed: 385,  paid: 0,   status: 'sent',     terms: 'Net 15', writeOff: 0,   note: 'Pays by cheque, allow ten days for the post.' },
  { no: 'INV-2026-0436', client: 'NWO-0372', issued: '2026-03-04', standard: 350,  billed: 295,  paid: 295, status: 'paid',     terms: 'Net 15', writeOff: 55,  note: 'Student rate applied, $55 off the schedule.' },
  { no: 'INV-2026-0440', client: 'BRA-0311', issued: '2026-03-05', standard: 465,  billed: 465,  paid: 465, status: 'paid',     terms: 'Net 15', writeOff: 0,   note: '' },
  { no: 'INV-2026-0387', client: 'DUA-0409', issued: '2026-02-28', standard: 425,  billed: 305,  paid: 305, status: 'paid',     terms: 'Net 15', writeOff: 120, note: 'Wrote off $120. We missed the 8862 history at intake, so the second transmission is on us.' },
  { no: 'INV-2026-0359', client: 'STE-0155', issued: '2026-02-25', standard: 1240, billed: 1240, paid: 620, status: 'partial',  terms: 'Net 15', writeOff: 0,   note: 'Paid half, asked to split the rest across two months.' }
];

/* The six that need Danielle's attention this morning, and why each one is actually stuck. */
const AT_RISK = [
  { client: 'ITK-0071', severity: 'critical', reason: 'Partner capital accounts are $612 out of balance and the 1065 is due Monday. Three K-1s and two personal returns are waiting behind it.', owner: 'sd', age: 3 },
  { client: 'DUA-0409', severity: 'critical', reason: 'Rejected on F1040-164-01. Form 8862 has to be added before EIC will be allowed. They are counting on this refund.', owner: 'ab', age: 1 },
  { client: 'BAP-0288', severity: 'critical', reason: 'Second AGI reject. If the transcript does not come back today, transmit with a prior-year AGI of 0.', owner: 'ra', age: 3 },
  { client: 'STE-0155', severity: 'high', reason: 'Name control mismatch. Lena’s SSA record still shows her maiden name, so the return has to be filed under the card name.', owner: 'ap', age: 2 },
  { client: 'RAG-0118', severity: 'high', reason: 'Mileage log outstanding since 2/18. $7,868 of vehicle deduction has nothing behind it and the return cannot transmit.', owner: 'ap', age: 22 },
  { client: 'AMA-0356', severity: 'medium', reason: 'Four state returns cannot start without the assignment itinerary. Requested 3/2, no response.', owner: 'ab', age: 10 }
];

/* Reviewer edits, shown as a change diff when the return comes back from review. */
const REVIEW_DIFFS = {
  'HAL-0233': {
    reviewer: 'gs', preparer: 'ab', received: '2026-03-10T14:22:00', minutes: 38,
    changes: [
      { field: 'Schedule E, line 14 — Depreciation', form: 'Schedule E', before: '$18,600 deducted as repairs', after: '$676 depreciation, 27.5-year life', why: 'A full roof replacement is a capital improvement under the tangible property regulations, not a repair. Placed in service 2025-08-14.' },
      { field: 'Schedule A, line 5b — State and local taxes', form: 'Schedule A', before: '$14,200', after: '$10,000', why: 'SALT deduction capped. The software carried the full property tax through because the second parcel was entered late.' },
      { field: 'Form 4562, line 19h — Basis for depreciation', form: 'Form 4562', before: '$0', after: '$18,600', why: 'Follows from the reclassification above.' }
    ],
    delta: { refundBefore: 7182, refundAfter: 3417 }
  },
  'ITK-0071': {
    reviewer: 'mv', preparer: 'sd', received: '2026-03-09T16:40:00', minutes: 95,
    changes: [
      { field: 'Guaranteed payments to partners', form: 'Form 1065, line 10', before: '$0', after: '$40,000', why: 'A mid-year payment to Tunde Oyelaran was booked to partner draws. It is compensation for services and belongs on line 10, which changes his self-employment income.' },
      { field: 'Partner capital — Femi Adeyemi', form: 'Schedule K-1, item L', before: '$71,308', after: 'Unresolved, $612 difference', why: 'Ending capital does not tie to the trial balance. Cannot issue K-1s until it does.' },
      { field: 'Meals deduction', form: 'Form 1065, line 20', before: '$14,880 at 100%', after: '$7,440 at 50%', why: 'The 100% deduction for restaurant meals expired after 2022. Staff meals during shifts remain 50% deductible.' }
    ],
    delta: { refundBefore: 0, refundAfter: 0 }
  }
};

/* Drafted chase messages. Written the way the firm actually writes to clients. */
const CHASE_TEMPLATES = {
  'RAG-0118': {
    subject: 'One document left on your 2025 return',
    body: 'Hi Priya,\n\nYour return is drafted and everything is in except the mileage log for the location shoots. We are claiming 11,240 business miles, which is worth $7,868 of deduction, and we need the log on file before we can transmit.\n\nPhotographs of the notebook pages are fine — you do not need to type anything up.\n\nOnce it is in, the return goes to review the same day.\n\nAni',
    channel: 'Portal message and email'
  },
  'AMA-0356': {
    subject: 'Assignment dates needed for your state returns',
    body: 'Hi Nana,\n\nCross Country reported all of your wages to Arizona, including the six weeks in Bend, so we cannot allocate your income correctly without your assignment itinerary — start and end dates for each contract in 2025.\n\nWe also need to confirm you kept the Portland apartment all year. If you did, the housing stipends stay non-taxable; if the lease lapsed, they do not, and that changes the return materially.\n\nFour state returns are waiting on this, so it is the one thing holding you up.\n\nAdwoa',
    channel: 'Email'
  },
  'SEP-0264': {
    subject: 'Three items outstanding — and a note about your estimates',
    body: 'Hi Camila,\n\nStill needed: your mileage log, the square footage of both home offices with the months you were at each, and your 2025 estimated tax payment record. If you cannot find the payment confirmations, say so and we will pull your IRS account transcript instead.\n\nSeparately, and worth ten minutes on the phone: your commission income has come down three years running and your estimates have not. You overpaid Q1 and Q2 by about $4,400 between them. We should reset the 2026 figures rather than lend the IRS money again.\n\nRenato',
    channel: 'Portal message'
  },
  'WHI-0142': {
    subject: 'Holding until the trust K-1 arrives',
    body: 'Hello Priscilla,\n\nEverything else for 2025 is in and reviewed. We are waiting on the Schedule K-1 from the Whitcombe Family Trust, which Bickford & Lyle normally issue in the last week of March.\n\nWe will not chase them before 20 March. If it has not arrived by 1 April we will file Form 4868 to extend and pay an estimate against what you owe, so there is no risk of a late-filing penalty either way.\n\nNothing needed from you today.\n\nDanielle',
    channel: 'Email'
  },
  'MAR-0339': {
    subject: 'Skid steer contract and the truck log',
    body: 'Dario,\n\nTwo things left: the finance contract for the skid steer — the contract, not the dealer invoice, because the interest and the capitalised amount are split differently — and the 2025 log for the F-350.\n\nIf the lender statement is not out yet, tell me and we will extend on 4868 as usual. That is not a problem, but I would rather plan it than discover it on 12 April.\n\nSimone',
    channel: 'Email and text'
  },
  'LIN-0388': {
    subject: 'Foreign account balances for 2025',
    body: 'Hi Annika,\n\nTo start your return I need the highest balance held in each foreign account at any point during 2025, converted at the year-end Treasury rate — we will do the conversion, just send the figures in kronor.\n\nThe Handelsbanken account was over the $10,000 threshold for most of last year, so FinCEN 114 is required alongside the return.\n\nAni',
    channel: 'Portal message'
  }
};

/* Chase history: what has already been sent, when, and by whom. */
const CHASE_LOG = {
  'RAG-0118': [
    { on: '2026-02-18T09:14:00', by: 'ab', via: 'Portal message', note: 'Initial request with the document list.' },
    { on: '2026-02-25T15:30:00', by: 'ab', via: 'Email', note: 'Second request. She replied that she would photograph the notebook that weekend.' },
    { on: '2026-03-09T08:05:00', by: 'ap', via: 'Text message', note: 'Third. No reply yet.' }
  ],
  'AMA-0356': [
    { on: '2026-03-02T11:20:00', by: 'ab', via: 'Email', note: 'Itinerary and housing documentation requested.' },
    { on: '2026-03-09T10:02:00', by: 'ab', via: 'Portal message', note: 'Second request.' }
  ],
  'SEP-0264': [
    { on: '2026-02-24T13:45:00', by: 'ra', via: 'Portal message', note: 'Mileage log and home office details requested.' },
    { on: '2026-03-03T09:30:00', by: 'ra', via: 'Email', note: 'Added the estimated payment record to the request.' }
  ],
  'WHI-0142': [
    { on: '2026-02-26T14:10:00', by: 'do', via: 'Email', note: 'Acknowledged the K-1 timing. Do not chase before 3/20.' }
  ],
  'MAR-0339': [
    { on: '2026-02-20T08:50:00', by: 'sd', via: 'Email', note: 'Skid steer contract requested.' },
    { on: '2026-02-27T16:15:00', by: 'sd', via: 'Text message', note: 'Vehicle log added to the request.' }
  ],
  'OSE-0207': [
    { on: '2026-03-01T10:00:00', by: 'yn', via: 'Internal', note: 'Del Paso K-1 is ours to produce. No client chase sent.' }
  ],
  'LIN-0388': [
    { on: '2026-03-10T17:05:00', by: 'ap', via: 'Portal message', note: 'Foreign account balances requested at engagement.' }
  ],
  'OYE-0091': [
    { on: '2026-03-09T09:40:00', by: 'yn', via: 'Internal', note: 'Waiting on our own 1065. No client chase sent.' }
  ]
};

/* This morning, before Danielle opened the console. */
const ACTIVITY = [
  { at: '2026-03-12T08:14:00', by: 'sd', text: 'Transmitted Golden Gate Collision, Form 1120-S, in batch B-0312-A.' },
  { at: '2026-03-12T07:52:00', by: 'ra', text: 'Transmitted Lani Yamashiro, Form 1040, in batch B-0312-A.' },
  { at: '2026-03-12T07:31:00', by: 'yn', text: 'Started intake for Tunde Oyelaran. Blocked on the Ìtan K-1.' },
  { at: '2026-03-11T21:47:00', by: null, text: 'Minh Trần signed Form 8879 through the portal.' },
  { at: '2026-03-11T19:03:00', by: null, text: 'Lani Yamashiro signed Form 8879 through the portal.' },
  { at: '2026-03-11T16:51:00', by: null, text: 'IRS rejected Ismael & Consuelo Duarte, F1040-164-01.' },
  { at: '2026-03-11T16:38:00', by: null, text: 'Vahe Karapetyan signed Form 8879 through the portal.' },
  { at: '2026-03-11T07:22:00', by: 'ab', text: 'Recorded a wet signature on Form 8879 for the Duartes.' }
];

/* Portal preview — the taxpayer's own view. Minh Trần, mid-season, return ready to sign. */
const PORTAL = {
  client: 'ASH-0221',
  uploads: [
    { name: 'W-2 Peninsula Anesthesia 2025.pdf', size: '388 KB', on: '2026-02-04T20:11:00', state: 'accepted' },
    { name: 'Vanguard Roth conversion confirmations.pdf', size: '242 KB', on: '2026-02-20T07:48:00', state: 'accepted' },
    { name: 'Bright Horizons 2025 statement.pdf', size: '104 KB', on: '2026-02-10T12:35:00', state: 'accepted' }
  ],
  summary: [
    { label: 'Adjusted gross income', value: 612840 },
    { label: 'Total tax', value: 179204 },
    { label: 'Withheld and paid', value: 175098 },
    { label: 'Balance due', value: 4106, emphasis: true }
  ]
};

/* Line-level prior-year comparison. Only returns that have been calculated carry
   these; the rest show the summary comparison until there are numbers to compare. */
const RETURN_LINES = {
  'RAG-0118': {
    note: 'Receipts rose by a third and total tax barely moved — the QBI deduction absorbed most of it. The balance due is a payments problem, not an income problem: she cut her estimates in June.',
    rows: [
      { label: 'Gross receipts', form: 'Schedule C, line 1', now: 214180, prior: 159010 },
      { label: 'Contract labour', form: 'Schedule C, line 11', now: 18400, prior: 6250 },
      { label: 'Depreciation and §179', form: 'Form 4562', now: 31480, prior: 6842 },
      { label: 'Car and truck', form: 'Schedule C, line 9', now: 7868, prior: 5394 },
      { label: 'All other expenses', form: 'Schedule C', now: 22940, prior: 9840 },
      { label: 'Net profit', form: 'Schedule C, line 31', now: 133492, prior: 130684, rule: true },
      { label: 'Adjusted gross income', form: 'Form 1040, line 11', now: 124061, prior: 121451 },
      { label: 'Qualified business income deduction', form: 'Form 8995', now: 21662, prior: 21370 },
      { label: 'Self-employment tax', form: 'Schedule SE', now: 18862, prior: 18465 },
      { label: 'Total tax', form: 'Form 1040, line 24', now: 32839, prior: 32324, rule: true },
      { label: 'Estimated payments', form: 'Form 1040, line 26', now: 26621, prior: 35510 }
    ],
    outcome: { now: -6218, prior: 3186 }
  },
  'ZAY-0347': {
    note: 'Third consecutive year of growth. The oven is the only real decision left on the return.',
    rows: [
      { label: 'Gross receipts', form: 'Schedule C, line 1', now: 512400, prior: 448900 },
      { label: 'Cost of goods sold', form: 'Schedule C, line 42', now: 178400, prior: 156200 },
      { label: 'Wages', form: 'Schedule C, line 26', now: 132900, prior: 112400 },
      { label: 'Rent', form: 'Schedule C, line 20b', now: 42000, prior: 42000 },
      { label: 'Depreciation and §179', form: 'Form 4562', now: 25760, prior: 8940 },
      { label: 'All other expenses', form: 'Schedule C', now: 16600, prior: 25827 },
      { label: 'Net profit', form: 'Schedule C, line 31', now: 116740, prior: 103533, rule: true },
      { label: 'Adjusted gross income', form: 'Form 1040, line 11', now: 108492, prior: 96218 }
    ],
    outcome: { now: -3714, prior: -2905 }
  }
};

/* Form-by-form completion, the preparer's working checklist. */
const FORM_STATUS = {
  'RAG-0118': [
    { form: 'Form 1040', state: 'done', note: 'Income and adjustments complete' },
    { form: 'Schedule C', state: 'done', note: 'Gross receipts tied to three 1099-NECs plus $91,630 of client payments that were never reported on a 1099' },
    { form: 'Schedule SE', state: 'done', note: 'Calculated from Schedule C net profit' },
    { form: 'Form 4562', state: 'open', note: '§179 election not yet made — waiting on her decision' },
    { form: 'Form 8995', state: 'open', note: 'Recalculates once the depreciation election is set' },
    { form: 'CA 540', state: 'notstarted', note: 'Starts once the federal return is final' }
  ],
  'ZAY-0347': [
    { form: 'Form 1040', state: 'done', note: '' },
    { form: 'Schedule C', state: 'done', note: 'QuickBooks tied out to the bank; $412 of unreconciled deposits posted to owner contributions' },
    { form: 'Form 4562', state: 'open', note: '§179 limited by business income, $1,840 carries forward' },
    { form: 'Schedule SE', state: 'done', note: '' },
    { form: 'Form 8995', state: 'done', note: '' },
    { form: 'CA 540', state: 'notstarted', note: '' }
  ],
  'VIL-0295': [
    { form: 'Form 1040', state: 'done', note: '' },
    { form: 'Schedule C', state: 'done', note: 'Standard meal rate used — 1,842 meals and 610 snacks' },
    { form: 'Form 8829', state: 'open', note: 'Time-space percentage recalculated at 34.8%, needs a second read' },
    { form: 'Schedule SE', state: 'done', note: '' },
    { form: 'CA 540', state: 'notstarted', note: '' }
  ],
  'OKA-0163': [
    { form: 'Form 1040', state: 'done', note: '' },
    { form: 'Schedule E', state: 'done', note: 'Seven vacant weeks documented as available for rent' },
    { form: 'Form 4562', state: 'done', note: 'Carried forward, no additions' },
    { form: 'CA 540', state: 'notstarted', note: '' }
  ],
  'HAL-0233': [
    { form: 'Form 1040', state: 'done', note: '' },
    { form: 'Schedule E', state: 'done', note: 'Roof reclassified in review to 27.5-year depreciation' },
    { form: 'Schedule A', state: 'done', note: 'SALT capped at $10,000' },
    { form: 'Form 4562', state: 'done', note: '' },
    { form: 'CA 540', state: 'notstarted', note: '' }
  ],
  'ITK-0071': [
    { form: 'Form 1065', state: 'open', note: 'Guaranteed payment reclass posted, capital accounts still $612 out' },
    { form: 'Schedule K-1 — Tunde Oyelaran', state: 'open', note: 'Cannot issue until capital ties' },
    { form: 'Schedule K-1 — Adaeze Oyelaran', state: 'open', note: '' },
    { form: 'Schedule K-1 — Femi Adeyemi', state: 'open', note: 'The $612 difference sits in this partner’s account' },
    { form: 'Form 4562', state: 'done', note: 'Emeryville build-out, $84,200, 39-year leasehold' },
    { form: 'CA 565', state: 'notstarted', note: '' }
  ]
};
