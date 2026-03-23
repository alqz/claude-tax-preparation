---
name: tax-preparation-cloud
description: Prepare and fill federal and state tax return PDF forms. Use this skill whenever the user mentions taxes, tax returns, filing taxes, 1040, W-2, refund, deductions, or wants help with any aspect of preparing or completing their tax return — even if they just say "help me do my taxes." Also trigger for questions about tax brackets, deductions, credits, or anything tax-related.
---

# Tax Preparation Skill (Claude.ai Edition)

Prepare federal and state income tax returns: read source documents, compute taxes, fill official PDF forms.

**Year-agnostic** — always look up current-year brackets, deductions, and credits. Never reuse prior-year values.

## Claude.ai Environment Setup

This skill is adapted for the Claude.ai computer-use environment. Run these steps **once** at the start of every tax session:

```bash
# 1. Install PyMuPDF (needed for IRS XFA field discovery)
pip install PyMuPDF --break-system-packages

# 2. Set up workspace
mkdir -p /home/claude/tax/source /home/claude/tax/work /home/claude/tax/forms /home/claude/tax/output
```

**Script location:** All helper scripts live at the skill install path. Reference them as:
```bash
SKILL_DIR=$(find /mnt/skills -path "*/tax-preparation-cloud/scripts" -type d 2>/dev/null | head -1)
```

### Network Constraints

The bash environment **cannot** reach IRS or state tax websites (only allowlisted domains like PyPI and GitHub work). The `web_fetch` tool can reach these sites but returns content into the conversation — it **cannot save binary PDF files to disk**. This means:

- **Tax documents**: User must upload them directly in the chat.
- **Blank PDF forms**: User must download them from the IRS/state websites and upload them. Claude provides the exact URLs.
- **Tax instructions and reference data**: Use `web_search` and `web_fetch` to look up brackets, thresholds, and form instructions (text content works fine — it's only binary PDF saving that doesn't work).

### Delivering Final Output

When filled PDFs are ready:
```bash
cp /home/claude/tax/output/*.pdf /mnt/user-data/outputs/
```
Then use the `present_files` tool to make them downloadable.

---

## Folder Structure

All work goes under `/home/claude/tax/`:

```
/home/claude/tax/
  source/              <- user's source documents (W-2, 1099s, prior return, CSVs)
  work/                <- ALL intermediate files (extracted data, field maps, computations)
    tax_data.txt       <- extracted figures from source docs
    computations.txt   <- all tax math (federal, state, capital gains, rental)
    f1040_fields.json  <- field discovery dumps (one per form)
    f8949_fields.json
    f1040sd_fields.json
    ca540_fields.json  <- (or equivalent state form)
    expected_*.json    <- verification expected values
  forms/               <- blank downloaded PDF forms
  output/              <- final filled PDFs + fill script
    fill_YEAR.py       <- the fill script
```

Create these folders at the start. Keep the working directory clean — no loose files.

## Context Budget Rules

These rules prevent context blowouts that cause compaction:

1. **NEVER read PDFs with the View tool.** Each page becomes ~250KB of base64 images. Extract text instead:
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

**Explicitly ask the user to upload their tax documents.** Say something like: "Please upload your tax documents — W-2s, 1099s, brokerage statements, and your prior year's tax return if you have it. You can attach them right here in the chat." Don't assume files are already present — check `/mnt/user-data/uploads/` and tell the user what you see (and what's missing).

**Sync uploads into the workspace** every time the user provides new documents (not just at the start):
```bash
cp /mnt/user-data/uploads/*.pdf /home/claude/tax/source/ 2>/dev/null
cp /mnt/user-data/uploads/*.csv /home/claude/tax/source/ 2>/dev/null
ls /home/claude/tax/source/
```
Run this each time the user says they've uploaded more files, or at the start of any message where new uploads might be present.

Read files from `source/`. Use pdfplumber for PDFs, view tool for CSVs. **Also ask for the prior year's tax return** — it contains carryforward items (depreciation schedules, suspended losses, loss carryovers, prior-year overpayments applied).

**Prior year diff:** If the user provides a prior year return, don't just extract carryforwards — also compare what forms were filed last year vs. this year. Any form present last year but absent this year should be flagged: ask the user if that income/situation still applies or has changed. This catches regressions (e.g., rental income that stopped, a K-1 partnership that was exited, foreign accounts that were closed) that the user might forget to mention.

Save all extracted figures to `work/tax_data.txt` immediately — one section per document with every relevant number.

**Follow up on what documents imply.** Each document type may reveal additional forms or schedules. Don't just extract numbers — ask what's behind them. Examples:

- **Mortgage statement (1098):** What type of property? Who are the co-borrowers? Ownership percentage? Do you rent out any part? Who makes the payments?
- **Retirement distribution (1099-R):** What type — rollover, early withdrawal, conversion?
- **Partnership/trust income (K-1):** What entity? Active or passive involvement?
- **Foreign tax docs (T4, etc.):** Did you file a return in that country? What was the actual tax owed (not just withheld)? If the taxpayer hasn't filed the foreign return yet and expects a refund (tax owed < withholding), recommend filing the foreign return FIRST to get exact tax figures for the FTC. Using withholding as a proxy means potential amendments later if a refund reduces the actual tax paid.
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

After gathering answers, **validate coverage against the 1040**: download the current year's Form 1040 and Schedules 1-3, scan each line description, and confirm you have information for every applicable line. Flag any gaps back to the user before proceeding.

### Step 3: Look Up Year-Specific Values

**Use `web_search` and `web_fetch` tools to find authoritative IRS sources.** Do not rely on training data for tax numbers. Web searches for "YEAR tax brackets" frequently return the wrong year's values (e.g., searching for "2024 tax brackets" may return 2025 brackets).

Required approach:
1. Search for and fetch the IRS Revenue Procedure that sets the tax year's inflation adjustments (e.g., Rev. Proc. 2023-34 for tax year 2024). This is the authoritative source for brackets, standard deduction, and thresholds.
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

### Step 4: Compute Supporting Schedules First

Compute all supporting schedules BEFORE the main 1040, since their results flow into it.

**Capital Gains (if applicable):**
1. Form 8949: individual transactions (Part I short-term, Part II long-term)
2. Schedule D: totals, loss limitation, carryover calculation (check prior year return for carryovers)
3. Net gain/loss -> 1040 Line 7

**Rental Income (if applicable — Schedule E):**
1. **Allocate shared expenses** between personal and rental use based on square footage (not a naive unit count). For multi-unit owner-occupied properties: measure the owner's unit vs. total livable area.
2. **Rental income:** total rents received by unit
3. **Rental expenses:** mortgage interest (rental portion x ownership %), property tax (rental portion x ownership %), insurance, repairs, utilities, property management, etc.
4. **Depreciation (Form 4562):** carry forward from prior year return, or set up from scratch if new property. Download the Form 4562 instructions and follow them for the applicable depreciation method and recovery period. Improvements/renovations get their own depreciation schedules. Land is not depreciable.
5. **Net rental income or loss** per property
6. **Passive activity loss rules:** if net loss, download Form 8582 instructions and determine if the loss is deductible or must be suspended. Check prior year return for suspended losses that may now be usable.
7. Net result -> Schedule 1 -> 1040 Line 8

**Self-Employment (if applicable — Schedule C):**
Follow Schedule C instructions. Net result -> Schedule 1 -> 1040 Line 8, and compute SE tax.

**Foreign Tax Credit (if applicable — Form 1116):**
Follow Form 1116 instructions for the applicable income category.

### Step 5: Compute Federal Return (Form 1040)

1. Gross Income: W-2 wages (1a) + interest (2b) + dividends (3b) + capital gain/loss (7) + Schedule 1 income (8)
2. Adjustments -> AGI (Line 11)
3. Deductions -> Taxable Income (Line 15)
   - Do NOT ask "standard or itemized?" — compute both and use whichever is larger
   - For mortgage interest: account for property type (personal vs. rental allocation), ownership percentage, and acquisition debt limits
4. Tax: use QDCG worksheet if qualified dividends/capital gains exist
5. Credits, other taxes -> Total Tax (Line 24)
6. Payments (withholding, estimated, extension, prior-year applied) -> Refund/Owed
7. If refund: collect direct deposit info (routing, account, type)

Save all line values to `work/computations.txt`.

### Step 6: Compute State Return

Use `web_search` and `web_fetch` to find the state's tax form AND its instructions. Read the instructions to identify:
- How the state uses federal AGI as a starting point (or not)
- State-specific adjustments to federal income (additions and subtractions)
- State conformity issues (areas where the state does not follow federal treatment)
- State tax brackets, deductions, exemptions, and credits
- Any state-specific taxes (e.g., supplemental taxes on high income)

Compute the state return by following the form instructions line by line. Do not assume federal treatment carries over — verify each item.

### Step 7: Obtain Blank PDF Forms

You need the blank PDF forms to discover field names and fill them. In Claude.ai, **bash cannot reach IRS or state tax websites**, and `web_fetch` returns PDF content into the conversation context (it cannot be saved to disk as a binary file). So the user must upload the blank forms.

**Tell the user exactly which forms you need** based on the computations so far. Give them the download URLs so they can grab the forms themselves:

**IRS** — use `/irs-prior/` for prior-year forms (`/irs-pdf/` is always current year):
```
https://www.irs.gov/pub/irs-prior/f1040--YEAR.pdf
https://www.irs.gov/pub/irs-prior/f8949--YEAR.pdf
https://www.irs.gov/pub/irs-prior/f1040sd--YEAR.pdf
```
Same pattern for all IRS forms (f1040sa, f1040sb, f1040s1, f1116, f8959, f8960, f4562, etc.)

**State forms**: Tell the user the state tax authority URL (e.g., `ftb.ca.gov/forms/YEAR/` for CA).

**Example message to the user:**
> "I need the blank PDF forms to fill in your return. Please download these and upload them here:
> - Form 1040: https://www.irs.gov/pub/irs-prior/f1040--2024.pdf
> - Schedule D: https://www.irs.gov/pub/irs-prior/f1040sd--2024.pdf
> - (etc.)"

Once uploaded, sync them into the workspace:
```bash
cp /mnt/user-data/uploads/*.pdf /home/claude/tax/forms/
ls /home/claude/tax/forms/
```

Verify each file has a `%PDF-` header (not an HTML error page).

### Step 8: Discover Field Names & Fill Forms

#### Discovery — ONCE per form, use `--compact`

```bash
SKILL_DIR=$(find /mnt/skills -path "*/tax-preparation-cloud/scripts" -type d 2>/dev/null | head -1)
cd /home/claude/tax

python "$SKILL_DIR/discover_fields.py" forms/f1040_blank.pdf --compact > work/f1040_fields.json
python "$SKILL_DIR/discover_fields.py" forms/f8949_blank.pdf --compact > work/f8949_fields.json
# ...repeat for each form
```

`--compact` outputs a minimal `{field_name: description}` mapping — each field name is paired with its tooltip/speak description so you can map line numbers to field names directly without manual inspection. Radio buttons include their option values (e.g. `{"/2": "Single", "/1": "MFJ"}`).

Do NOT use `--search` repeatedly or `--json` (which dumps raw metadata and wastes context).

**HARD FAIL**: If discovery returns 0 human-readable descriptions, STOP. Do not guess field names.

#### Fill Script

Write `output/fill_YEAR.py` importing from the skill scripts:

```python
import sys
SKILL_DIR = "..."  # result of find command above
sys.path.insert(0, SKILL_DIR)
from fill_forms import fill_pdf, fill_irs_pdf, add_suffix
```

- **`add_suffix(d)`** — appends `[0]` to text field keys. Required for IRS forms.
- **`fill_irs_pdf(in, out, fields, checkboxes, radio_values)`** — IRS forms. `radio_values` for filing status, yes/no, checking/savings.
- **`fill_pdf(in, out, fields, checkboxes)`** — CA forms. Matches by `/Parent` chain + `/AP/N` keys.

Output filled PDFs to `output/`.

### Step 9: Verify Filled Forms

```bash
python "$SKILL_DIR/verify_filled.py" output/f1040_filled.pdf work/expected_f1040.json
```

Fix any failures, re-run fill script.

### Step 10: Verify Against Form Instructions — MANDATORY

**For EVERY form you filled**, you MUST:

1. Fetch the form's instructions using `web_fetch` from `https://www.irs.gov/instructions/i{form}` (e.g., `i1116`, `i1040sd`, `i8960`). For state forms, fetch the instruction booklet from the state tax authority's website.
2. Read the instruction text for every line you filled. Pay special attention to lines that reference **worksheets**, **special computations**, or **"see instructions"** — these are where the form's logic diverges from what you might assume.
3. For each line, confirm your computation matches the instruction's method. If the instruction describes a worksheet you didn't use, work through that worksheet now.
4. Save verification notes to `work/verification.txt` documenting what you checked and any corrections made.

**Do NOT skip this step.** Do NOT verify from memory — you must have the actual instruction text in context. The most common errors come from computing a line using a simplified formula when the instructions require a specific worksheet (e.g., Form 1116 Line 18 QDCG adjustment, Schedule D Line 22 flow control).

**Do NOT proceed to Step 11 until every form has been verified.**

**Additional self-checks:**
1. **Verify the tax bracket year.** Confirm the brackets you used match the tax year, not the filing year. Check against the standard deduction printed on the 1040 form itself.
2. **Validate arithmetic.** Totals should add up. AGI should equal the sum of all income minus adjustments. Total tax should equal tax + credits + other taxes.
3. **Check for carryforward items.** If the user provided a prior year return, verify that all carryforwards were picked up (depreciation, suspended losses, capital loss carryover).
4. **Standard vs. itemized.** Verify you computed both and used the larger. If mortgage interest is involved, verify the personal vs. rental allocation and ownership percentage.
5. **Payments.** Verify ALL payments are included — withholding, estimated, extension, prior-year overpayment.
6. **State return.** Verify the state return doesn't blindly follow federal treatment — check the state instructions for any adjustments.

### Step 11: Review Other Obligations

Before presenting results, systematically check whether the user's situation triggers any obligations beyond the federal and state returns. Walk through the table below and flag every item that applies. Present each as a concrete action item with a deadline — do not bury these in passing remarks.

| Trigger | Obligation | Details |
|---------|-----------|---------|
| Foreign financial accounts with aggregate balance > $10K at any point during the year | **FBAR (FinCEN Form 114)** | Filed separately online at bsaefiling.fincen.treas.gov — NOT part of the tax return. Deadline: April 15, auto-extended to October 15. Report account names, numbers, and maximum balances. |
| Foreign financial assets > $50K (Single) or $200K (MFJ) at year-end, or $75K/$300K at any point | **Form 8938 (FATCA)** | Filed WITH the tax return. Check whether it was included in the forms you prepared. |
| Foreign taxes claimed as FTC based on withholding (foreign return not yet filed) | **File foreign return first** | If the taxpayer expects a refund from the foreign country, recommend completing the foreign return before finalizing the US return. Otherwise, warn that a refund will require amending or adjusting the FTC in the refund year. |
| Received distribution from or had transactions with a foreign trust | **Form 3520** | Separate filing, due with the tax return. Severe penalties for late filing (up to 35% of distribution). |
| Owns shares in foreign mutual funds or ETFs (Passive Foreign Investment Companies) | **Form 8621 (PFIC)** | Filed with the tax return. Complex — may need QEF or mark-to-market election. |
| Gave gifts > annual exclusion ($19K per recipient for 2025) to any individual | **Form 709 (Gift Tax Return)** | Separate filing, due April 15. No tax is usually owed (uses lifetime exemption), but the return is still required. |
| Paid any contractor or vendor > $600 for rental property services | **File 1099-NEC or 1099-MISC** for that person | Due January 31 of the following year. If the deadline has passed, advise filing late (penalties increase over time). |
| Return shows an underpayment penalty | **Adjust withholding or make estimated payments** for next year | Compute the safe harbor (110% of current year tax if AGI > $150K). Recommend specific W-4 changes or quarterly 1040-ES amounts. |
| Cannot complete the return by April 15 | **File Form 4868 (extension)** | Extension gives 6 months to file, but does NOT extend the payment deadline — estimated tax is still due April 15. |
| Exercised incentive stock options (ISOs) | **AMT exposure** | May need Form 6251. Must track AMT basis separately from regular basis for future sale. |
| HSA contributions (employer or individual) | **Form 8889 required**; state conformity | Some states (e.g., CA, NJ) don't recognize HSA — add-back required on state return. |
| Sold a home | **Exclusion rules** | $250K (Single) / $500K (MFJ) exclusion if owned and lived in 2 of last 5 years. Partial exclusion may apply if < 2 years. Report on Form 8949 if gain exceeds exclusion. |
| Rental property in a jurisdiction with registration requirements | **Local rental registration or business license** | Varies by city/county. Not a tax filing but a legal obligation the taxpayer may not know about. |
| Crypto/digital asset transactions | **Form 1099-DA (new for 2025)** | Cost basis tracking is complex. Brokers may not report basis. Taxpayer may need to reconstruct from transaction history. |
| Prior year overpayment applied to current year | **Verify it's reflected in payments** | Easy to miss. Check prior year return Line 36 and current year 1040-ES records. |

**Open-ended reasoning step:** After checking the table above, pause and consider: "Given everything I now know about this taxpayer's full situation — income sources, life events, assets, residency — are there any obligations, filings, or action items that aren't covered by the checklist above?" This is where broad knowledge catches edge cases that a static table cannot anticipate.

### Step 12: Present Results

Show a summary table, verification checklist, capital loss carryover (if any), then:

- **Sign your returns** — unsigned returns are rejected
- **Payment instructions** (if owed) — IRS Direct Pay, FTB Web Pay, deadline April 15
- **Direct deposit** — recommend it for refunds; ask for bank info if not provided
- **How to file** — e-file (Free File, CalFile) or mailing addresses
- **Action items** — list every obligation flagged in Step 11, with deadlines. Present as a numbered checklist so the user can track completion. Example:

  > **Action items before/after filing:**
  > 1. Pay $4,237 federal — IRS Direct Pay — by filing deadline
  > 2. Pay $1,892 California — FTB Web Pay — by filing deadline
  > 3. File FBAR at bsaefiling.fincen.treas.gov — by extended deadline
  > 4. Adjust W-4 withholding for next year to avoid underpayment penalty

**Deliver the files:**
```bash
cp /home/claude/tax/output/*.pdf /mnt/user-data/outputs/
```
Then use the `present_files` tool to share all filled PDFs with the user.

## Key Gotchas

### Environment (Claude.ai specific)
- Install PyMuPDF at start: `pip install PyMuPDF --break-system-packages`
- Use `web_fetch` tool (not curl/wget) to download forms from IRS/state sites
- All work in `/home/claude/tax/` — final output to `/mnt/user-data/outputs/`
- Locate scripts: `find /mnt/skills -path "*/tax-preparation-cloud/scripts" -type d`

### Field Discovery
- Field names change between years — always discover fresh
- XFA template is in `/AcroForm` -> `/XFA` array, NOT from brute-force xref scanning
- Do NOT use `xml.etree` for XFA — use regex (IRS XML has broken namespaces)

### PDF Filling
- Remove XFA from AcroForm, set NeedAppearances=True, use auto_regenerate=False
- Checkboxes: set both `/V` and `/AS` to `/1` or `/Off`
- IRS fields need `[0]` suffix — use `add_suffix()`
- IRS checkboxes match by `/T` directly; radio groups match by `/AP/N` key via `radio_values`

### Form-Specific (IRS)
- **1040**: First few fields (`f1_01`-`f1_03`) are fiscal year headers, not name fields. SSN = 9 digits, no dashes. Digital assets = crypto only, not stocks.
- **8949**: Box A/B/C checkboxes are 3-way radio buttons. Totals at high field numbers (e.g. `f1_115`-`f1_119`), not after last data row. Schedule D lines 1b/8b (from 8949), not 1a/8a.
- **Schedule D**: Some fields have `_RO` suffix (read-only) — skip those.
- **Downloads**: Prior-year IRS = `irs.gov/pub/irs-prior/`, current = `irs.gov/pub/irs-pdf/`

### Form-Specific (State)
- State forms vary widely in structure. Always run field discovery fresh.
- Some states use IRS-style XFA forms, others use simple AcroForm. Use `fill_irs_pdf` or `fill_pdf` accordingly based on what discovery reveals.
- Read the state form instructions to understand field naming conventions before mapping.

### CA 540 (if applicable — replace with equivalent for other states)
- Field names are `540-PPNN` (page+sequence, NOT line numbers). Checkboxes end with `" CB"`, radio buttons use named AP keys.
- CA does not tax capital gains at preferential rates — all income taxed as ordinary.
- CA does not recognize federal HSA deductions — add back on Schedule CA if HSA contributions reduced federal wages.
- CA has a Mental Health Services Tax (additional tax on high income) — check current year threshold.
- CA exemption credit phases out at high AGI — check current year phase-out threshold.
- CA has an individual mandate for health coverage — penalties may apply if uninsured.
- CA forms available at `ftb.ca.gov/forms/YEAR/`.
- **If the user resides in a different state**, replace all CA-specific guidance above with the equivalent for that state. Research the state's tax forms, instructions, conformity with federal law, and any state-specific taxes or credits.
