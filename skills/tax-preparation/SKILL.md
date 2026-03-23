---
name: tax-preparation
description: Prepare and fill federal and state tax return PDF forms. Use this skill whenever the user mentions taxes, tax returns, filing taxes, 1040, W-2, refund, deductions, or wants help with any aspect of preparing or completing their tax return — even if they just say "help me do my taxes." Also trigger for questions about tax brackets, deductions, credits, or anything tax-related.
user-invocable: true
---

# Tax Preparation Skill

Prepare federal and state income tax returns: read source documents, compute taxes, fill official PDF forms.

**Year-agnostic** — always look up current-year brackets, deductions, and credits. Never reuse prior-year values.

## Folder Structure

Organize all work into subfolders of the working directory:

```
working_dir/
  source/              ← user's source documents (W-2, 1099s, prior return, CSVs)
  work/                ← ALL intermediate files (extracted data, field maps, computations)
    tax_data.txt       ← extracted figures from source docs
    computations.txt   ← all tax math (federal, state, capital gains, rental)
    f1040_fields.json  ← field discovery dumps (one per form)
    f8949_fields.json
    f1040sd_fields.json
    ca540_fields.json  ← (or equivalent state form)
    ...                ← add more as needed (Schedule E, Form 4562, Form 1116, etc.)
    expected_*.json    ← verification expected values
  forms/               ← blank downloaded PDF forms
    f1040_blank.pdf
    f8949_blank.pdf
    f1040sd_blank.pdf
    ca540_blank.pdf    ← (or equivalent state form)
    ...                ← add all applicable forms (Schedule E, A, B, 1-3, 8959, 8960, 4562, etc.)
  output/              ← final filled PDFs + fill script
    fill_YEAR.py       ← the fill script
    f1040_filled.pdf
    f8949_filled.pdf
    f1040sd_filled.pdf
    ca540_filled.pdf   ← (or equivalent state form)
    ...                ← all filled forms
```

Create these folders at the start. Keep the working directory clean — no loose files.

## Computation Rules

**ALL math must be done in code (Python), NEVER by reasoning/inference.** LLMs are
unreliable calculators. Even simple arithmetic (multiplying percentages, summing
columns) must be executed in a Python script or one-liner, not reasoned about in text.

Specific rules:
- **Never round intermediate results.** Use exact values (fractions, full decimal
  precision) throughout. Only round to whole dollars at the final step when writing
  to the Form Values sheet. Rounding a percentage from 50.9227% to 50.90% at an
  intermediate step can introduce $100+ errors that compound across years.
- **Use exact fractions** (e.g., `1200/4500`) instead of decimal approximations
  in all allocation computations.
- **Cross-check computed values** against prior year returns where available
  (e.g., `prior_depreciation / prior_MACRS_rate` should equal the depreciable basis).

### The Computation Workbook

All tax computations are captured in `work/tax_computations.xlsx` — a spreadsheet
built by a Python script (`work/build_computations.py`) using the `build_workbook.py`
framework. This workbook is the single source of truth for all numbers on the return.

**Required sheets:**

| Sheet | Contents | Rule |
|-------|----------|------|
| Source Data | Raw numbers from tax documents and user input | No computation — extraction only |
| Tax Tables | Brackets, rates, thresholds, MACRS rates | Values from government sources |
| *(computation sheets)* | One per area: Capital Gains, Rental Property, Depreciation, FTC, QDCG Worksheet, etc. | ALL values are computed in Python with exact precision; each row records its formula as a string for auditing |
| Federal Return | One row per 1040 line | Formula references to computation sheets |
| State Return | One row per state form line | Same |
| Form Values | Rounded output for the fill script | `round_dollar()` applied here and ONLY here |
| Validation | Cross-form consistency checks | Must all PASS before filling forms |
| Carryforwards | Items carrying to next year | For next year's preparer |

**Workflow:**
1. Run `extract_tax_tables.py forms/` → produces `work/extracted_tables.json`
   with values parsed directly from the downloaded forms (standard deductions,
   thresholds, exemption credits). Import these into your build script — do NOT
   look up these values separately.
2. Write `work/build_computations.py` — a Python script that imports
   `build_workbook.TaxWorkbook` and computes everything. The script must call
   `preflight_check(work_dir, forms_dir)` before building — this verifies
   that instruction-notes files exist (proving you read the instructions).
3. Run it → produces `work/tax_computations.xlsx`
4. Run `validate_return.py work/tax_computations.xlsx --forms-dir forms/`
   → must pass ALL checks, including input-level checks that cross-verify
   Tax Tables values against the actual forms.
5. The fill script reads from the Form Values sheet — no hardcoded values

**The fill script must not contain any tax math.** It is a thin mapping from
the Form Values sheet to PDF field names. If a number needs to change, change
the build script and re-run — never edit the fill script's values directly.

```python
# Example: build_computations.py structure
import sys
sys.path.insert(0, "path/to/scripts")
from build_workbook import TaxWorkbook, Row, FormField, Check, round_dollar, macrs_rate

wb = TaxWorkbook(tax_year=YEAR, taxpayer="Jane Doe")

# 1. Source data (from extracted documents)
wb.source_data("W-2", [
    ("Box 1 - Wages", 92347.50, "w-2.pdf"),
    ("Box 2 - Federal withheld", 14283.00, "w-2.pdf"),
])

# 2. Computation (all math in Python, exact precision)
wages = 92347.50
std_ded = 15750
taxable = wages - std_ded
tax = compute_tax_simple(taxable, fed_brackets)  # looked up in 1b

wb.computation("Federal Tax", [
    Row("Wages", val=wages, formula="SourceData[W-2 Box 1]"),
    Row("Standard deduction", val=std_ded, formula="TaxTables[Single std ded]"),
    Row("Taxable income", val=taxable, formula="wages - std_ded", is_subtotal=True),
    Row("Tax", val=tax, formula="compute_tax_simple(taxable, brackets)", is_total=True),
])

# 3. Form values (rounding happens here)
wb.form_values("1040", [
    FormField("1a", "Wages", val=round_dollar(wages), pdf_field="f1_47"),
    FormField("15", "Taxable income", val=round_dollar(taxable), pdf_field="f2_06"),
])

# 4. Validation
wb.validate([Check("Tax > 0", expected=True, actual=tax > 0)])

wb.save("work/tax_computations.xlsx")
```

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

### Phase 1: Gather Information

Do all automated/cheap work first, then ask the user.

#### 1a. Read and extract user-provided documents

Read files from `source/` (move them there if needed). Use pdfplumber for PDFs, Read tool for CSVs. Save all extracted figures to `work/tax_data.txt` immediately — one section per document with every relevant number.

**Prior year diff:** If the user provides a prior year return, don't just extract carryforwards — also compare what forms were filed last year vs. this year. Any form present last year but absent this year should be flagged later in 1c.

**Follow up on what documents imply.** Each document type may reveal additional forms or schedules. Don't just extract numbers — ask what's behind them:
- **1098 (Mortgage):** Property type? Co-borrowers? Ownership %? Rental use?
- **1099-R:** Rollover, early withdrawal, or conversion?
- **K-1:** What entity? Active or passive?
- **T4 / foreign tax docs:** Filed a return in that country? Actual tax owed vs. withheld? If not yet filed and expecting a refund, recommend filing the foreign return FIRST.
- **1099-B with basis not reported:** Employer stock plan? Supplemental basis statements?

#### 1b. Research tax policy, instructions, and year-specific values

**Start with government sources, then cross-check broadly.** The primary goal is **completeness** — you must not miss any applicable threshold, rate, or rule change.

**Layer 1 — Government sources (mandatory, comprehensive):**
1. **IRS Revenue Procedure** for the tax year's inflation adjustments (e.g., Rev. Proc. 2024-40 for 2025)
2. **Form instructions**: download 1040 instructions, extract Tax Computation Worksheet and QDCG Worksheet
3. **IRS Newsroom** (irs.gov/newsroom): mid-year legislative changes (e.g., OBBB Act)
4. **State tax authority**: form instructions, tax rate schedules, conformity announcements
5. Cross-check: standard deduction on the 1040 form itself

**Layer 2 — Broader sources (cross-checking):**
Search tax publications, CPA firm summaries, and news for the tax year. These surface recent legislation, known form issues, and state-specific gotchas. If a broader source contradicts a government source, investigate.

Do NOT hardcode thresholds — always look up fresh. These values go into the **Tax Tables** sheet:
- Federal brackets, standard deduction, QDCG thresholds
- Additional Medicare Tax / NIIT thresholds
- AMT exemption and phase-out thresholds
- Passive activity loss phase-out thresholds
- State brackets, standard deduction, exemption credits, phase-outs
- MACRS depreciation rates (use `macrs_rate()` from `build_workbook.py`)

**For state returns**, download the state form instructions and write line-by-line notes to `work/state_instructions_notes.txt`. For each line, note what it requires and flag any worksheets, limitations, phase-outs, or non-conformity with federal treatment.

#### 1c. Ask about life situations and reconcile documents — MANDATORY

**Generate the questionnaire dynamically from the current year's forms.**
Using the 1040, Schedules 1–3, and state form downloaded in 1b, scan each
line description and identify what information is needed that the documents
from 1a don't already provide. Convert each gap into a plain-language
question about the user's life situation — not tax jargon.

Always ask about these regardless (they affect filing but may not appear
on any document): filing status, dependents, state of residence, life
changes (marriage, divorce, new child, relocation), and tax payments made
(estimated, extension, prior-year overpayment applied).

Do NOT rely on a vague catch-all like "any other income or deductions?"
— people don't know what they don't know. Ask specifically about each
applicable area. When a topic comes up, ask the follow-up details that
forms alone won't tell you — for example:
- Rental property → ownership %, unit sizes (sq ft), rental income by unit, expense breakdown, existing depreciation schedule
- Home purchase/sale → date, price, primary residence or investment, co-owners
- Self-employment → type of business, estimated income, major expense categories
- Foreign income → which country, type of income, whether foreign return was filed

**Do NOT proceed until the user has answered.** "Same as last year" counts.

**After gathering answers, reconcile documents:**

1. **Generate an expected document checklist** from the user's answers.
   For each situation, identify the documents that should exist (e.g.,
   employed → W-2 + 1095-C; brokerage → 1099-B/DIV/INT; rental →
   depreciation schedule; foreign income → T4; mortgage → 1098).

2. **Compare against what was received in 1a.** Flag missing documents
   by name. Don't proceed until confirmed complete.

3. **Validate coverage against the 1040**: scan each line of the 1040
   and Schedules 1–3, confirm you have information for every applicable line.

### Phase 2: Build the Computation Workbook

Write `work/build_computations.py` — a Python script that creates the computation workbook using `build_workbook.TaxWorkbook`. This single script contains ALL tax math. Run it to produce `work/tax_computations.xlsx`.

**Before computing each form/schedule**, download its instructions and read the relevant sections. Do not compute any line from memory. This is especially important for:
- Worksheets embedded in form instructions (e.g., QDCG worksheet)
- Phase-outs and limitations that change with inflation adjustments
- New lines or changed line numbers between tax years

Compute supporting schedules BEFORE the main 1040, since their results flow into it.

**Capital Gains (if applicable):**
1. Form 8949: individual transactions (Part I short-term, Part II long-term)
2. Schedule D: totals, loss limitation, carryover (check prior year for carryovers)
3. Net gain/loss → 1040 Line 7

**Rental Income (if applicable — Schedule E):**
1. **Allocate shared expenses** by square footage (not naive unit count). **Use exact fractions (e.g., 1200/4500) — never round percentages at intermediate steps.**
2. Rental income by unit
3. Rental expenses: mortgage interest, property tax, insurance, repairs, utilities — each allocated by sq ft × ownership %
4. **Depreciation:** carry forward from prior year or set up from scratch. **Cross-check:** `prior_year_dep ÷ prior_year_MACRS_rate` should equal the depreciable basis.
5. Net per property
6. **Passive activity loss rules:** if net loss, check Form 8582. Check prior year for suspended losses.
7. Net result → Schedule 1 → 1040 Line 8

**Self-Employment (if applicable):** Follow Schedule C instructions.

**Foreign Tax Credit (if applicable):** Use `compute_ftc.py` — do NOT implement
the Form 1116 computation manually. The script handles currency conversion and
the Line 18 QDCG adjustment (IRC 904(b)(2)(B)) which has a 100% manual error rate.
Pass the foreign amounts in their original currency along with the IRS yearly
average exchange rate.

**Federal Return:** Add a sheet with one row per 1040 line:
1. Gross Income (1a + 2b + 3b + 4b + 5b + 6b + 7a + 8)
2. Adjustments → AGI
3. Deductions → Taxable Income (compute both standard and itemized, use whichever is larger)
4. Tax (QDCG worksheet if applicable)
5. Credits, other taxes → Total Tax
6. Payments → Refund/Owed

**State Return:** Follow your line-by-line notes from 1b. Common non-conformity traps (not exhaustive — the instructions are authoritative):
- Itemized deduction limitations (e.g., CA Pease limitation — still applies post-TCJA)
- HSA non-conformity (CA, NJ don't recognize)
- Capital gains taxed as ordinary (CA)
- Exemption credit phase-outs, state-specific taxes (e.g., CA BH Tax > $1M)
- Different standard deduction amounts and itemization rules

**Run validation after building:**
```bash
python scripts/validate_return.py work/tax_computations.xlsx --forms-dir forms/
```
All checks must PASS before proceeding. This runs both consistency checks
(do the numbers add up?) and input checks (do the Tax Tables values match
what's printed on the actual forms?).

### Phase 3: Fill and Verify Forms

#### 3a. Download blank PDF forms

Download applicable forms to `forms/`. Use `/irs-prior/` for prior-year IRS forms (`/irs-pdf/` is always current year). Find state forms on the state tax authority's website. Verify each download has `%PDF-` header.

#### 3b. Discover fields, fill forms, and verify

**Discovery** — ONCE per form, use `--compact` (see `docs/form-filling.md` for details):
```bash
python scripts/discover_fields.py forms/f1040_blank.pdf --compact > work/f1040_fields.json
```

**Fill script** — Write `output/fill_YEAR.py` using `scripts/fill_forms.py`. The fill script reads values from `work/tax_computations.xlsx` (Form Values sheet). It must not contain any tax math. See `docs/form-filling.md` for `fill_irs_pdf` vs `fill_pdf` usage.

**Verify** — Run `scripts/verify_filled.py` against expected values. Fix failures, re-run.

#### 3c. Verify against form instructions — MANDATORY

**For EVERY form you filled**, you MUST:
1. Fetch the form's instructions (IRS: `irs.gov/instructions/i{form}`; state: from state tax authority)
2. Read instruction text for every line you filled — especially **worksheets**, **special computations**, and **"see instructions"** references
3. Confirm each computation matches the instruction's method
4. Save verification notes to `work/verification.txt`

**Do NOT skip this.** Do NOT verify from memory — you must have the actual instruction text in context. With 1M token context, there is no cost reason to skip. The most common errors come from using a simplified formula when the instructions require a specific worksheet (e.g., Form 1116 Line 18 QDCG adjustment, Schedule CA Line 29 Pease limitation worksheet).

**Self-checks:**
1. Tax bracket year matches tax year (not filing year)
2. Arithmetic: totals add up, AGI = income − adjustments
3. Carryforwards picked up from prior year
4. Standard vs. itemized: computed both, used larger; state limitations applied
5. All payments included (withholding, estimated, extension, prior-year overpayment)
6. State return doesn't blindly follow federal treatment

#### 3d. Review other obligations

Systematically check whether the user's situation triggers obligations beyond the
returns. Look up current-year thresholds for each — do not assume prior-year values.

| Trigger | Obligation | Details |
|---------|-----------|---------|
| Foreign accounts > FBAR threshold | **FBAR (FinCEN 114)** | Separate filing at bsaefiling.fincen.treas.gov. Report account names, numbers, max balances. Look up current deadline. |
| Foreign assets > FATCA threshold | **Form 8938 (FATCA)** | Filed WITH the return. Look up current thresholds by filing status. |
| FTC based on withholding, foreign return not filed | **File foreign return first** | If expecting a refund, file foreign return before US return. Otherwise, warn that a refund will require amending. |
| Foreign trust distribution | **Form 3520** | Separate filing, due with return. Severe penalties for late filing. |
| Foreign mutual funds/ETFs (PFICs) | **Form 8621** | Filed with return. May need QEF or mark-to-market election. |
| Gifts > annual exclusion per recipient | **Form 709 (Gift Tax)** | Separate filing. No tax usually owed (uses lifetime exemption), but return still required. |
| Paid contractor > reporting threshold for rental | **File 1099-NEC/MISC** | Due Jan 31 of following year. If late, advise filing anyway (penalties increase over time). |
| Underpayment penalty | **Adjust W-4 or estimated payments** | Compute safe harbor for next year. Recommend specific W-4 line 4(c) amount or quarterly 1040-ES amounts. |
| Can't file by deadline | **File for extension** | Extension = more time to file, NOT more time to pay. Estimated tax still due on original deadline. |
| ISO stock options exercised | **AMT exposure** | May need Form 6251. Must track AMT basis separately from regular basis for future sale. |
| HSA contributions | **Form 8889**; state conformity | Some states don't recognize HSA — add-back required on state return. |
| Home sold | **Exclusion rules** | Look up current exclusion. Must have owned and lived in home 2 of last 5 years. Partial exclusion may apply. |
| Rental property | **Local registration/license** | Varies by jurisdiction. Not a tax filing but a legal obligation. |
| Digital asset transactions | **Report per current-year requirements** | Cost basis tracking is complex. Brokers may not report basis. |
| Prior year overpayment applied | **Verify reflected in payments** | Easy to miss. Check prior year return and current year 1040-ES records. |

**Then pause and reason:** are there any obligations not covered by this table,
given everything you know about this taxpayer?

### Phase 4: Present Results

Show a summary table, then:
- **Sign your returns** — unsigned returns are rejected
- **Payment instructions** (if owed) — IRS Direct Pay, state web pay, deadline = filing deadline
- **Direct deposit** — recommend for refunds; ask for bank info
- **How to file** — e-file (IRS Free File, state e-file options) or mailing addresses
- **Action items** — every obligation from 3d, with deadlines, as a numbered checklist
