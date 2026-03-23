# PDF Form Filling Reference

Read this document when you reach Step 8 (Discover Field Names & Fill Forms).

## Field Discovery

- Field names change between years — always discover fresh
- XFA template is in `/AcroForm` → `/XFA` array, NOT from brute-force xref scanning
- Do NOT use `xml.etree` for XFA — use regex (IRS XML has broken namespaces)

## PDF Filling Mechanics

- Remove XFA from AcroForm, set NeedAppearances=True, use auto_regenerate=False
- Checkboxes: set both `/V` and `/AS` to `/1` or `/Off`
- IRS fields need `[0]` suffix — use `add_suffix()`
- IRS checkboxes match by `/T` directly; radio groups match by `/AP/N` key via `radio_values`

## Form-Specific Notes (IRS)

- **1040**: First few fields (`f1_01`-`f1_03`) are fiscal year headers, not name fields. SSN = 9 digits, no dashes. Digital assets = crypto only, not stocks.
- **8949**: Box A/B/C checkboxes are 3-way radio buttons. Totals at high field numbers (e.g. `f1_115`-`f1_119`), not after last data row. Schedule D lines 1b/8b (from 8949), not 1a/8a.
- **Schedule D**: Some fields have `_RO` suffix (read-only) — skip those.
- **Downloads**: Prior-year IRS = `irs.gov/pub/irs-prior/`, current = `irs.gov/pub/irs-pdf/`

## Form-Specific Notes (State)

- State forms vary widely in structure. Always run field discovery fresh.
- Some states use IRS-style XFA forms, others use simple AcroForm. Use `fill_irs_pdf` or `fill_pdf` accordingly based on what discovery reveals.
- Read the state form instructions to understand field naming conventions before mapping.

### CA 540 Field Conventions

- Field names are `540-PPNN` (page+sequence, NOT line numbers). Checkboxes end with `" CB"`, radio buttons use named AP keys.
- CA forms available at `ftb.ca.gov/forms/YEAR/`.
