---
name: tax-filing
description: Prepare and fill federal and state tax return PDF forms
user_invocable: true
triggers:
  - do my taxes
  - prepare tax return
  - fill tax forms
  - file taxes
  - tax preparation
---

# Tax Filing Skill

Prepare federal (IRS) and state (CA) income tax returns by extracting data from source documents, computing taxes, and filling official PDF forms.

**Year-agnostic**: This skill works for any tax year. You must look up the correct tax brackets, standard deduction amounts, exemption credits, and other year-specific values for the tax year being filed. Do NOT hardcode or assume values from a previous year.

## Workflow

### Step 1: Gather Source Documents

Ask the user for:
- W-2 (wages, withholding)
- 1099-INT (interest income)
- 1099-DIV (dividends, qualified dividends)
- 1099-B / brokerage CSV (capital gains/losses)
- Any other 1099s, K-1s, or income documents
- Prior year tax return (to check for capital loss carryover, etc.)

Read files from the working directory. Parse CSVs, extract numbers from PDFs, or ask the user to provide key figures.

### Step 2: Confirm Filing Details

Ask the user:
- Filing status (Single, MFJ, MFS, HOH, QSS)
- Dependents (number, names)
- State of residence
- Standard vs. itemized deduction preference
- Digital asset / cryptocurrency transactions (Yes/No) — note: stock trades are NOT digital assets
- Health coverage status (for CA)
- Any estimated tax payments made
- Any other credits or adjustments

### Step 3: Look Up Year-Specific Values

Before computing, research the correct values for the tax year being filed:
- **Federal tax brackets** (for the filing status)
- **Standard deduction** amount
- **Qualified dividends / capital gains** 0%/15%/20% bracket thresholds
- **CA tax brackets** (for the filing status)
- **CA standard deduction** amount
- **CA personal exemption credit** amount
- Any other year-specific thresholds (EITC, AMT, etc.)

Use IRS.gov and FTB.ca.gov as authoritative sources. Do NOT reuse prior-year amounts.

### Step 4: Compute Federal Return

Follow this sequence:

1. **Gross Income**: Sum W-2 wages (Line 1a), interest (2b), dividends (3b), capital gain/loss (7), other income
2. **Adjustments**: Student loan interest, HSA, IRA, etc. → Line 10
3. **AGI**: Gross income minus adjustments → Line 11
4. **Deductions**: Standard deduction or Schedule A → Line 12-14
5. **Taxable Income**: AGI minus deductions → Line 15
6. **Tax Computation**:
   - If qualified dividends or capital gains exist: use QDCG Tax Worksheet
   - Otherwise: use tax tables or bracket computation
7. **Credits**: Child tax credit, education, etc. → Lines 19-21
8. **Other Taxes**: SE tax, penalty, etc. → Lines 23
9. **Total Tax**: Line 24
10. **Payments**: W-2 withholding (25a), estimated payments (26), credits (27-31) → Line 33
11. **Refund/Owed**: Line 34-37 (overpaid/refund) or Line 37 (amount owed)
12. **Direct Deposit**: If refund, collect routing number, account number, and account type (checking/savings) for Lines 35b-d

### Step 5: Compute Capital Gains (if applicable)

If the user has stock/option sales:
1. Fill **Form 8949** with individual transactions (Part I short-term, Part II long-term)
2. Fill **Schedule D** with totals from Form 8949
3. Apply $3,000 capital loss limitation (Schedule D Line 21)
4. Calculate carryover for next year
5. Report net gain/loss on 1040 Line 7

### Step 6: Compute State Return (CA Form 540)

1. Start with federal AGI (Line 13)
2. Apply CA subtractions (Line 14) and additions (Line 16) → CA AGI (Line 17)
3. Subtract CA standard deduction → Taxable income (Line 19)
4. Look up tax from CA tax table or compute from brackets → Line 31
5. Subtract exemption credits → Line 33
6. Add any special taxes (mental health tax on income over $1M, AMT) → Total tax (Line 64)
7. Subtract CA withholding (W-2 box 17) → Refund/Owed

### Step 7: Download Blank PDF Forms

Find and download the correct blank PDF forms for the tax year and state being filed.

**Federal (IRS)**: Use `/irs-prior/` for prior-year forms. `/irs-pdf/` always has the **current** year.
```
# Prior-year forms (replace YEAR, e.g. 2024)
https://www.irs.gov/pub/irs-prior/f1040--YEAR.pdf
https://www.irs.gov/pub/irs-prior/f8949--YEAR.pdf
https://www.irs.gov/pub/irs-prior/f1040sd--YEAR.pdf

# Current-year forms
https://www.irs.gov/pub/irs-pdf/f1040.pdf
```

**State**: Search the state's tax authority website (e.g. `ftb.ca.gov/forms/YEAR/` for CA).

Download each form needed and save as `*_blank.pdf` in the working directory. Verify each download is a real PDF (check for `%PDF-` header, not an HTML error page).

### Step 8: Discover Field Names & Fill PDF Forms

**Every tax year, discover field names fresh** using `discover_fields.py`:

```bash
# Discover all forms at once (accepts multiple PDFs)
python scripts/discover_fields.py f1040_blank.pdf f8949_blank.pdf f1040sd_blank.pdf ca540_blank.pdf

# IRS forms (XFA-based) — use --xfa-only for human-readable descriptions
python scripts/discover_fields.py f1040_blank.pdf --xfa-only
python scripts/discover_fields.py f1040_blank.pdf --xfa-only --search "first name"

# CA Form 540 (AcroForm with /TU tooltips)
python scripts/discover_fields.py ca540_blank.pdf
python scripts/discover_fields.py ca540_blank.pdf --search "adjusted gross"

# JSON output for programmatic consumption
python scripts/discover_fields.py f1040_blank.pdf --json --xfa-only > f1040_fields.json
```

For IRS XFA forms, discovery also cross-references AcroForm annotations to report
radio button `/AP/N` options (e.g. which value = "Single" vs "MFJ" for filing status).
These show up as `radio: /1=c1_3[0], /2=c1_3[1]` in text mode, or as `radio_options`
in JSON mode.

#### Writing the Fill Script

Use `scripts/fill_forms.py` which provides:
- **`add_suffix(d)`** — Appends `[0]` to text field keys (skips checkbox keys starting with `c`). Required for all IRS forms.
- **`fill_irs_pdf(input, output, fields, checkboxes, radio_values)`** — For IRS forms. Matches checkboxes by `/T` value directly. The `radio_values` parameter handles IRS exclGroup fields (filing status, yes/no questions, etc.) where multiple annotations share a `/T` prefix with different `/AP/N` keys. Example: `radio_values={"c1_3": "/1"}` selects "Single".
- **`fill_pdf(input, output, fields, checkboxes)`** — For CA and other forms. Matches checkboxes/radio buttons by walking the `/Parent` chain and inspecting `/AP/N` keys.

Write a year-specific fill script (e.g. `fill_2025.py`) that:
1. Defines field name → value dictionaries for each form
2. Defines checkbox and radio dictionaries
3. Calls `fill_irs_pdf()` (with `add_suffix()`) for IRS forms — pass `radio_values` for filing status, digital assets, checking/savings, etc.
4. Calls `fill_pdf()` for CA forms

#### Filtering Discovery Results

```bash
# Filter by page or field type
python scripts/discover_fields.py form.pdf --page 1 --type Btn

# JSON output — useful for programmatic field mapping
python scripts/discover_fields.py form.pdf --json > fields.json
```

Different forms use different PDF metadata:
- **IRS forms**: XFA `<assist><speak>` elements (use `--xfa-only`). Radio button `/AP/N` options are cross-referenced from AcroForm annotations automatically.
- **CA Form 540**: AcroForm `/TU` tooltips (automatic with default mode)

**⚠️ HARD FAIL**: If neither method produces human-readable field descriptions, **STOP IMMEDIATELY**. Do not fill the form. Do not guess from field names or positions. Tell the user that field discovery failed and needs debugging. Filling with unmapped opaque field names like `f1_32[0]` will produce WRONG values in WRONG fields — this is worse than not filling at all.

**Validation**: Expect roughly these field counts — significantly fewer means discovery is broken:
- Form 1040: ~100+ fields
- Schedule D: ~35 fields
- Form 8949: ~126 fields
- CA Form 540: ~120+ fields

### Step 9: Verify and Fix

After filling, use the verification script:

```bash
python scripts/verify_filled.py filled.pdf expected.json
```

Where `expected.json` contains `text_fields`, `checkboxes`, and `radio_buttons` sections with expected values. The script reports OK/MISSING/MISMATCH for each field and exits with code 1 on any failure.

Also:
1. Cross-check key numbers: AGI, taxable income, tax, refund
2. Fix any misaligned fields by re-examining field names with `discover_fields.py`
3. Re-run the fill script after corrections

### Step 10: Present Results & Filing Instructions

After all forms are filled and verified, present a celebration + checklist + action items:

#### Celebration & Summary Table
Start with a brief celebratory note (e.g. "Your taxes are done! 🎉"), then show the key numbers:

| | Federal | State |
|---|---------|-------|
| AGI | ... | ... |
| Taxable Income | ... | ... |
| Tax | ... | ... |
| Withholding | ... | ... |
| **Refund** / **Amount Owed** | ... | ... |

#### Verification Checklist
Show what was checked/verified with checkmarks:
- ✅ W-2 wages, withholding matched to source
- ✅ 1099-INT / 1099-DIV amounts matched
- ✅ Capital gains/losses computed, Form 8949 filled
- ✅ Schedule D totals verified, $3,000 loss limitation applied
- ✅ Capital loss carryover from prior year applied
- ✅ Federal tax computed via QDCG worksheet (or brackets)
- ✅ State tax computed from brackets + exemption credits
- ✅ All PDF fields programmatically verified
- ✅ Checkboxes (filing status, digital assets, etc.) confirmed
- (Include/exclude items as relevant to the specific return)

#### Capital Loss Carryover (if applicable)
Note the carryover amounts for next year (short-term and long-term separately).

#### ⚠️ CRITICAL: Sign Your Returns!
**You MUST sign and date your returns before mailing or e-filing.** Unsigned returns are not valid and will be rejected.
- Federal 1040: Sign on Page 2, "Sign Here" section
- CA 540: Sign on Side 6, "Sign Here" section

#### Payment Instructions (if taxes are owed)
If the user OWES taxes (not getting a refund), make this **prominent and unmissable**:
- **Federal**: Pay via IRS Direct Pay (irs.gov/payments), EFTPS, or mail a check with Form 1040-V
- **California**: Pay via FTB Web Pay (ftb.ca.gov), or mail a check with the return
- **Deadline**: April 15 (or extension deadline). Late payments incur penalties + interest.
- **Filing an extension extends the filing deadline but NOT the payment deadline.** Taxes owed are still due April 15.

#### Refund Delivery — Recommend Direct Deposit
If the user is getting a refund and hasn't provided direct deposit info, **ask if they want to add it**. Direct deposit is much faster (~21 days vs 6+ weeks by mail).
- Federal 1040: Lines 35b (routing), 35c (account type), 35d (account number)
- CA 540: Lines 116-118 (routing, account type, account number)

If they decline, explain that without direct deposit their refund will arrive by **paper check in the mail** (6+ weeks). Note: starting with 2025 returns (filed in 2026), the IRS is phasing out paper checks — refunds without direct deposit info may be delayed while the IRS requests banking details.

#### Filing Options
- E-file options (IRS Free File, CalFile, etc.)
- Mailing addresses for paper filing
- Payment due date

## Key Gotchas

### Field Discovery — CRITICAL
- **No stored field mappings**: Field names change between tax years. Always derive mappings fresh from the downloaded PDF using `scripts/discover_fields.py`. Never rely on cached, stored, or memorized mappings from a prior year.
- **XFA template location**: The template is in `/AcroForm` → `/XFA` array. Look for `(template) N 0 R` in the object. Brute-force xref scanning (iterating all xrefs checking for `<template` in stream bytes) does NOT work reliably.
- **Do NOT use XML parser for XFA**: `xml.etree.ElementTree` chokes on IRS XFA XML (unbound namespace prefixes, line-breaks inside closing tags like `</speak\n>`). Use regex extraction instead.
- **HARD FAIL on zero fields**: If discovery returns 0 human-readable descriptions, STOP. Never guess field mappings. Never fill with unmapped opaque names. The risk of putting wrong values in wrong fields is the worst possible outcome.

### PDF Form Filling
- **Remove XFA**: Delete `/XFA` from `/AcroForm` dictionary to force AcroForm rendering
- **NeedAppearances**: Set to `True` so PDF viewers regenerate field appearances
- **auto_regenerate=False**: Pass this to `update_page_form_field_values` to avoid corruption
- **Checkboxes**: Set both `/V` and `/AS` to `/1` (checked) or `/Off` (unchecked)
- **Field names**: Walk the `/Parent` chain to build fully-qualified field paths
- **IRS field name `[0]` suffix**: IRS XFA-based forms have `/T` values like `f1_04[0]` (with `[0]` suffix). When using `update_page_form_field_values`, field keys MUST include the `[0]` suffix to match. Use a helper like `add_suffix()` to append `[0]` to all text field keys.
- **IRS checkbox matching**: `fill_irs_pdf()` matches checkboxes by `/T` value directly (not full parent-chain path). For simple on/off checkboxes, use `checkbox_values`. For radio-button-style exclGroups (filing status, yes/no questions, checking/savings), use `radio_values` with a `/T` prefix and the target `/AP/N` key value. Run `discover_fields.py --xfa-only` to see radio options.

### IRS Form 1040 (historically stable field patterns)
- First few fields (e.g. `f1_01`, `f1_02`, `f1_03`) are often **fiscal year header fields**, NOT name fields — always verify via XFA discovery
- Address fields are often nested under a `ReadOrder` parent
- The digital assets question is about **cryptocurrency**, not stock trades
- Some checkboxes near Line 7 may be misidentified — always verify by XFA `<speak>` text, not by y-position
- SSN field typically has a 9-character max — use digits only, no dashes

### IRS Schedule D & Form 8949
- Schedule D may have read-only fields (e.g. `_RO` suffix) — don't try to fill those
- Form 8949 checkboxes for Box A/B/C (and D/E/F) are typically 3-way radio buttons, not Yes/No pairs
- When using Form 8949, Schedule D data goes to Line 1b/8b (from 8949), NOT Line 1a/8a (direct from 1099-B)
- Form 8949 totals row fields are at high numbers (e.g. `f1_115`-`f1_119`), NOT immediately after the last data row

### CA Form 540
- Field names often follow a `540-PPNN` pattern: PP = page number, NN = sequential field number
- Field numbers are sequential per page, **NOT** form line numbers
- Checkbox fields often end with `" CB"` suffix (note the space)
- Radio buttons (filing status, account type) use named AP keys — inspect `/AP/N` keys to find the correct value

### Downloading Forms
- For prior-year IRS forms: use `irs.gov/pub/irs-prior/` (NOT `/irs-pdf/`)
- `/irs-pdf/` always has the **current** year's forms
- Always verify downloads are real PDFs (check for `%PDF-` header), not HTML error pages
