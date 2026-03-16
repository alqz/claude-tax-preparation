---
name: tax-filing
description: Prepare and fill federal and state tax return PDF forms
user-invocable: true
---

# Tax Filing Skill

Prepare federal and state income tax returns: read source documents, compute taxes, fill official PDF forms.

**Year-agnostic** — always look up current-year brackets, deductions, and credits. Never reuse prior-year values.

## Folder Structure

Organize all work into subfolders of the working directory:

```
working_dir/
  source/              ← user's source documents (W-2, 1099s, prior return, CSVs)
  work/                ← ALL intermediate files (extracted data, field maps, computations)
    tax_data.txt       ← extracted figures from source docs
    computations.txt   ← all tax math (federal, state, capital gains)
    f1040_fields.json  ← field discovery dumps
    f8949_fields.json
    f1040sd_fields.json
    ca540_fields.json
    expected_*.json    ← verification expected values
  forms/               ← blank downloaded PDF forms
    f1040_blank.pdf
    f8949_blank.pdf
    f1040sd_blank.pdf
    ca540_blank.pdf
  output/              ← final filled PDFs + fill script
    fill_YEAR.py       ← the fill script
    f1040_filled.pdf
    f8949_filled.pdf
    f1040sd_filled.pdf
    ca540_filled.pdf
```

Create these folders at the start. Keep the working directory clean — no loose files.

## Context Budget Rules

These rules prevent context blowouts that cause compaction:

1. **NEVER read PDFs with the Read tool.** Each page becomes ~250KB of base64 images (a 9-page return = 1.8 MB). Extract text instead:
   ```bash
   python3 -c "
   import pdfplumber
   with pdfplumber.open('source/document.pdf') as pdf:
       for p in pdf.pages: print(p.extract_text())
   "
   ```
2. **NEVER read the same document twice.** Save extracted figures to `work/tax_data.txt` on first read.
3. **Run field discovery ONCE per form** as a bulk JSON dump to `work/`. Do NOT use `--search` repeatedly.
4. **Save all computed values to `work/computations.txt`** so they survive compaction.

## Workflow

### Step 1: Gather Source Documents & Follow Up on Implications

Ask the user what documents they have. Read files from `source/` (move them there if needed). Use pdfplumber for PDFs, Read tool for CSVs.

Save all extracted figures to `work/tax_data.txt` immediately — one section per document with every relevant number.

**Follow up on what documents imply.** Each document type may reveal additional filing requirements. Examples:

- **Mortgage statement (1098):** What type of property? Who are the co-borrowers? Ownership percentage? Do you rent out any part? Who makes the payments?
- **Retirement distribution (1099-R):** What type — rollover, early withdrawal, conversion?
- **Partnership/trust income (K-1):** What entity? Active or passive involvement?
- **Foreign tax docs (T4, etc.):** Did you file a return in that country? What was the actual tax owed (not just withheld)?
- **Brokerage (1099-B) with basis not reported:** Are these employer stock plan shares? Do you have supplemental cost basis statements?

### Step 2: Ask About Life Situations — MANDATORY

**You MUST ask the user about each category below and WAIT for answers before proceeding.** Do NOT skip this step. Do NOT rely on a vague catch-all like "any other credits or adjustments" — people don't know what they don't know. Ask in plain language about life situations, not tax form jargon.

**Filing basics:**
- Filing status (Single, MFJ, MFS, HOH, QSS)
- Dependents (number, names)
- State of residence

**Work & business:**
- Any freelance, side jobs, gig work, or self-employment income?
- Any business expenses if self-employed?

**Property:**
- Do you own any property? What type? (single-family, multi-unit, condo)
- Do you rent out any property or any part of your home?
- If rental: ownership percentage, unit sizes (sq ft), rental income by unit, expenses, existing depreciation schedule
- Did you buy or sell a home this year?
- Any renovations or improvements? (these may need their own depreciation schedules)

**Investments:**
- Any cryptocurrency or digital asset transactions? (stock trades are NOT digital assets)

**Deductions (ask specifically — do NOT just ask "standard or itemized"):**
- Charitable contributions?
- Significant medical expenses?
- Student loan interest?
- Retirement account contributions outside of payroll?
- Health savings account contributions outside of payroll?

**Credits:**
- Child or dependent care expenses?
- Education expenses or tuition?
- Energy improvements to your home?

**Health:**
- Health coverage all year? (relevant for states with individual mandates)

**Payments (ask broadly):**
- Did you make any tax payments for this tax year? This includes:
  - Quarterly estimated payments
  - Payment with an extension
  - Prior-year overpayment applied to this year
- Did you file for an extension?

**Life changes:**
- Marriage, divorce, or separation?
- New child (birth or adoption)?
- Job change or relocation?

**Foreign:**
- Any foreign financial accounts?
- Any foreign assets?

**Do NOT proceed to Step 3 until the user has answered.** "Same as last year" counts as confirmation.

After gathering answers, **validate coverage against the 1040**: download the current year's Form 1040 and Schedules 1–3, scan each line description, and confirm you have information for every applicable line. Flag any gaps back to the user before proceeding.

### Step 3: Look Up Year-Specific Values

**Use authoritative IRS sources, not web search results.** Web searches for "YEAR tax brackets" frequently return the wrong year's values (e.g., searching for "2024 tax brackets" may return 2025 brackets).

Required approach:
1. Fetch the IRS Revenue Procedure that sets the tax year's inflation adjustments (e.g., Rev. Proc. 2023-34 for tax year 2024). This is the authoritative source for brackets, standard deduction, and thresholds.
2. Alternatively, download the 1040 instructions for the tax year and extract values from the Tax Computation Worksheet and Qualified Dividends and Capital Gain Tax Worksheet.
3. Cross-check: verify that the standard deduction amount matches what's printed on the 1040 form itself.
4. Do NOT hardcode any thresholds or phase-out amounts — always look them up fresh for the applicable tax year.

Gather and save to `work/computations.txt`:
- Federal tax brackets and standard deduction
- Qualified dividends / capital gains rate thresholds
- Additional Medicare Tax and net investment income tax thresholds
- AMT exemption and phase-out thresholds
- Passive activity loss phase-out thresholds (if rental property applies)
- State tax brackets, standard deduction, exemption credits and phase-outs

### Step 4: Compute Federal Return

1. Gross Income: W-2 wages (1a) + interest (2b) + dividends (3b) + capital gain/loss (7) + Schedule 1 income (8)
2. Adjustments → AGI (Line 11)
3. Deductions → Taxable Income (Line 15)
   - Do NOT ask "standard or itemized?" — compute both and use whichever is larger
   - For mortgage interest: account for property type (personal vs. rental allocation), ownership percentage, and acquisition debt limits
4. Tax: use QDCG worksheet if qualified dividends/capital gains exist
5. Credits, other taxes → Total Tax (Line 24)
6. Payments (withholding, estimated, extension, prior-year applied) → Refund/Owed
7. If refund: collect direct deposit info (routing, account, type)

Save all line values to `work/computations.txt`.

### Step 4a: Compute Rental Income (if applicable — Schedule E)

If the user has rental property:

1. **Allocate shared expenses** between personal and rental use based on square footage (not a naive unit count). For multi-unit owner-occupied properties: measure the owner's unit vs. total livable area.
2. **Rental income:** total rents received by unit
3. **Rental expenses:** mortgage interest (rental portion × ownership %), property tax (rental portion × ownership %), insurance, repairs, utilities, property management, etc.
4. **Depreciation:** compute or carry forward from prior year
   - Building: residential rental property uses 27.5-year MACRS from placed-in-service date
   - Improvements/renovations: separate depreciation schedule per improvement, from their own placed-in-service date
   - Land is not depreciable — need land vs. building allocation (from appraisal, tax assessor, or purchase closing statement)
   - First year is prorated by month placed in service (mid-month convention)
5. **Net rental income or loss** per property
6. **Passive activity loss rules:** if net loss, check if the taxpayer can deduct it. The allowance for active participation phases out with AGI — look up the current year's phase-out range. At high AGI, the entire loss is typically suspended and carried forward.
7. Net result → Schedule 1 → 1040 Line 8

### Step 5: Compute Capital Gains (if applicable)

1. Form 8949: individual transactions (Part I short-term, Part II long-term)
2. Schedule D: totals, loss limitation, carryover calculation
3. Net gain/loss → 1040 Line 7

### Step 6: Compute State Return (CA Form 540)

1. Federal AGI → CA adjustments → CA taxable income
2. Tax from brackets − exemption credits → total tax
3. Withholding → Refund/Owed

### Step 7: Download Blank PDF Forms

Save to `forms/` directory.

**IRS**: Use `/irs-prior/` for prior-year forms (`/irs-pdf/` is always current year):
```
https://www.irs.gov/pub/irs-prior/f1040--YEAR.pdf
https://www.irs.gov/pub/irs-prior/f8949--YEAR.pdf
https://www.irs.gov/pub/irs-prior/f1040sd--YEAR.pdf
```

**CA**: `ftb.ca.gov/forms/YEAR/` for state forms.

Verify each download has `%PDF-` header (not an HTML error page).

### Step 8: Discover Field Names & Fill Forms

#### Discovery — ONCE per form, use `--compact`

```bash
python scripts/discover_fields.py forms/f1040_blank.pdf --compact > work/f1040_fields.json
python scripts/discover_fields.py forms/f8949_blank.pdf --compact > work/f8949_fields.json
python scripts/discover_fields.py forms/f1040sd_blank.pdf --compact > work/f1040sd_fields.json
python scripts/discover_fields.py forms/ca540_blank.pdf --compact > work/ca540_fields.json
```

`--compact` outputs a minimal `{field_name: description}` mapping — each field name is paired with its tooltip/speak description so you can map line numbers to field names directly without manual inspection. Radio buttons include their option values (e.g. `{"/2": "Single", "/1": "MFJ"}`).

Do NOT use `--search` repeatedly or `--json` (which dumps raw metadata and wastes context).

**HARD FAIL**: If discovery returns 0 human-readable descriptions, STOP. Do not guess field names.

#### Fill Script

Write `output/fill_YEAR.py` using `scripts/fill_forms.py`:

- **`add_suffix(d)`** — appends `[0]` to text field keys. Required for IRS forms.
- **`fill_irs_pdf(in, out, fields, checkboxes, radio_values)`** — IRS forms. `radio_values` for filing status, yes/no, checking/savings.
- **`fill_pdf(in, out, fields, checkboxes)`** — CA forms. Matches by `/Parent` chain + `/AP/N` keys.

Output filled PDFs to `output/`.

### Step 9: Verify

```bash
python scripts/verify_filled.py output/f1040_filled.pdf work/expected_f1040.json
```

Fix any failures, re-run fill script.

### Step 10: Present Results

Show a summary table, verification checklist, capital loss carryover (if any), then:

- **Sign your returns** — unsigned returns are rejected
- **Payment instructions** (if owed) — IRS Direct Pay, FTB Web Pay, deadline April 15
- **Direct deposit** — recommend it for refunds; ask for bank info if not provided
- **Filing options** — e-file (Free File, CalFile) or mailing addresses

## Key Gotchas

### Context
- NEVER use Read tool on PDFs — use pdfplumber
- NEVER read same document twice — save to `work/tax_data.txt`
- Field discovery once per form with `--compact` — no `--json` (wastes context), no repeated `--search`

### Field Discovery
- Field names change between years — always discover fresh
- XFA template is in `/AcroForm` → `/XFA` array, NOT from brute-force xref scanning
- Do NOT use `xml.etree` for XFA — use regex (IRS XML has broken namespaces)

### PDF Filling
- Remove XFA from AcroForm, set NeedAppearances=True, use auto_regenerate=False
- Checkboxes: set both `/V` and `/AS` to `/1` or `/Off`
- IRS fields need `[0]` suffix — use `add_suffix()`
- IRS checkboxes match by `/T` directly; radio groups match by `/AP/N` key via `radio_values`

### Form-Specific
- **1040**: First few fields (`f1_01`-`f1_03`) are fiscal year headers, not name fields. SSN = 9 digits, no dashes. Digital assets = crypto only, not stocks.
- **8949**: Box A/B/C checkboxes are 3-way radio buttons. Totals at high field numbers (e.g. `f1_115`-`f1_119`), not after last data row. Schedule D lines 1b/8b (from 8949), not 1a/8a.
- **Schedule D**: Some fields have `_RO` suffix (read-only) — skip those.
- **CA 540**: Field names are `540-PPNN` (page+sequence, NOT line numbers). Checkboxes end with `" CB"`, radio buttons use named AP keys.
- **Downloads**: Prior-year IRS = `irs.gov/pub/irs-prior/`, current = `irs.gov/pub/irs-pdf/`
