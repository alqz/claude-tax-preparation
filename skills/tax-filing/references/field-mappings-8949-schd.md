# Form 8949 & Schedule D - Field Name Mappings (2024)

> **Year note**: Created from 2024 forms. Field names are generally stable year-to-year but MUST be spot-checked with `discover_fields.py` when filing a new tax year. Verify ~5 key fields — if they match, trust the rest.

**Field discovery**: Both forms have XFA templates with `<assist><speak>` descriptions. AcroForm has NO `/TU` tooltips. Run `python scripts/discover_fields.py form.pdf --xfa-only` for quick discovery.

## Form 8949 - Sales and Other Dispositions of Capital Assets

### Prefixes

```
P1 = "topmostSubform[0].Page1[0]"
P2 = "topmostSubform[0].Page2[0]"
T1 = f"{P1}.Table_Line1[0]"    # Part I table
T2 = f"{P2}.Table_Line1[0]"    # Part II table
```

### Header
| Field | Purpose |
|-------|---------|
| `{P1}.f1_1[0]` | Name (Page 1) |
| `{P1}.f1_2[0]` | SSN (Page 1) |
| `{P2}.f2_1[0]` | Name (Page 2) |
| `{P2}.f2_2[0]` | SSN (Page 2) |

### Checkbox: Basis Reported to IRS
| Field | Box |
|-------|-----|
| `{P1}.c1_1[0]` | Box A - Short-term, basis reported to IRS |
| `{P1}.c1_1[1]` | Box B - Short-term, basis NOT reported |
| `{P1}.c1_1[2]` | Box C - Short-term, no 1099-B |
| `{P2}.c2_1[0]` | Box D - Long-term, basis reported to IRS |
| `{P2}.c2_1[1]` | Box E - Long-term, basis NOT reported |
| `{P2}.c2_1[2]` | Box F - Long-term, no 1099-B |

### Part I - Short-Term (Page 1)

Each row has columns: (a) description, (b) date acquired, (c) date sold, (d) proceeds, (e) cost basis, (f) code, (g) adjustment, (h) gain/loss.

| Row | (a) Desc | (b) Acquired | (c) Sold | (d) Proceeds | (e) Cost | (f) Code | (g) Adjust | (h) Gain/Loss |
|-----|----------|--------------|----------|---------------|----------|----------|------------|----------------|
| Row1 | `{T1}.Row1[0].f1_3[0]` | `f1_4[0]` | `f1_5[0]` | `f1_6[0]` | `f1_7[0]` | `f1_8[0]` | `f1_9[0]` | `f1_10[0]` |
| Row2 | `{T1}.Row2[0].f1_11[0]` | `f1_12[0]` | `f1_13[0]` | `f1_14[0]` | `f1_15[0]` | `f1_16[0]` | `f1_17[0]` | `f1_18[0]` |
| Row3 | `{T1}.Row3[0].f1_19[0]` | `f1_20[0]` | `f1_21[0]` | `f1_22[0]` | `f1_23[0]` | `f1_24[0]` | `f1_25[0]` | `f1_26[0]` |
| Row4 | `{T1}.Row4[0].f1_27[0]` | `f1_28[0]` | `f1_29[0]` | `f1_30[0]` | `f1_31[0]` | `f1_32[0]` | `f1_33[0]` | `f1_34[0]` |
| ... | Pattern continues: Row5-Row14 | | | | | | | |

**Note**: Each row's fields follow the pattern `f1_{base + (row-1)*8}[0]` through `f1_{base + (row-1)*8 + 7}[0]` starting from f1_3 for Row1.

### Part I - Totals (Page 1)
| Field | Column | Description |
|-------|--------|-------------|
| `{P1}.f1_115[0]` | (d) | Total proceeds |
| `{P1}.f1_116[0]` | (e) | Total cost basis |
| `{P1}.f1_117[0]` | (f) | Total code |
| `{P1}.f1_118[0]` | (g) | Total adjustment |
| `{P1}.f1_119[0]` | (h) | Total gain/loss |

### Part II - Long-Term (Page 2)

Same column structure as Part I but field names use `f2_` prefix.

| Row | (a) Desc | (b) Acquired | (c) Sold | (d) Proceeds | (e) Cost | (f) Code | (g) Adjust | (h) Gain/Loss |
|-----|----------|--------------|----------|---------------|----------|----------|------------|----------------|
| Row1 | `{T2}.Row1[0].f2_3[0]` | `f2_4[0]` | `f2_5[0]` | `f2_6[0]` | `f2_7[0]` | `f2_8[0]` | `f2_9[0]` | `f2_10[0]` |
| Row2 | `{T2}.Row2[0].f2_11[0]` | `f2_12[0]` | `f2_13[0]` | `f2_14[0]` | `f2_15[0]` | `f2_16[0]` | `f2_17[0]` | `f2_18[0]` |
| Row3 | `{T2}.Row3[0].f2_19[0]` | `f2_20[0]` | `f2_21[0]` | `f2_22[0]` | `f2_23[0]` | `f2_24[0]` | `f2_25[0]` | `f2_26[0]` |
| Row4 | `{T2}.Row4[0].f2_27[0]` | `f2_28[0]` | `f2_29[0]` | `f2_30[0]` | `f2_31[0]` | `f2_32[0]` | `f2_33[0]` | `f2_34[0]` |
| ... | Pattern continues: Row5-Row14 | | | | | | | |

### Part II - Totals (Page 2)
| Field | Column | Description |
|-------|--------|-------------|
| `{P2}.f2_115[0]` | (d) | Total proceeds |
| `{P2}.f2_116[0]` | (e) | Total cost basis |
| `{P2}.f2_117[0]` | (f) | Total code |
| `{P2}.f2_118[0]` | (g) | Total adjustment |
| `{P2}.f2_119[0]` | (h) | Total gain/loss |

---

## Schedule D - Capital Gains and Losses

### Prefixes

```
P1 = "topmostSubform[0].Page1[0]"
P2 = "topmostSubform[0].Page2[0]"
T1 = f"{P1}.Table_PartI[0]"     # Part I table
T2 = f"{P1}.Table_PartII[0]"    # Part II table
```

### Header
| Field | Purpose |
|-------|---------|
| `{P1}.f1_01[0]` | Name(s) shown on return |
| `{P1}.f1_02[0]` | SSN (MaxLen=11) |
| `{P1}.c1_1[0]` | Disposed of qualified opportunity fund? **Yes** |
| `{P1}.c1_1[1]` | Disposed of qualified opportunity fund? **No** |

### Part I - Short-Term Capital Gains and Losses

Each row: (d) proceeds, (e) cost basis, (g) adjustments, (h) gain/loss.

| Line | XFA Description | (d) | (e) | (g) | (h) |
|------|-----------------|-----|-----|-----|-----|
| 1a (1099-B basis reported, no adj) | `{T1}.Row1a[0]` | `f1_03[0]` | `f1_04[0]` | `f1_05_RO[0]` **READ-ONLY** | `f1_06[0]` |
| 1b (8949 Box A) | `{T1}.Row1b[0]` | `f1_07[0]` | `f1_08[0]` | `f1_09[0]` | `f1_10[0]` |
| 2 (8949 Box B) | | `f1_11[0]` | `f1_12[0]` | `f1_13[0]` | `f1_14[0]` |
| 3 (8949 Box C) | | `f1_15[0]` | `f1_16[0]` | `f1_17[0]` | `f1_18[0]` |
| 4 (Form 6252/4684/6781/8824) | | | | | `f1_19[0]` |
| 5 (K-1 ST gain/loss) | | | | | `f1_20[0]` |
| 6 (ST capital loss carryover) | | | | | `f1_21[0]` |

| Field | Line | Description |
|-------|------|-------------|
| `{P1}.f1_22[0]` | **7** | **Net short-term capital gain/loss** |

### Part II - Long-Term Capital Gains and Losses

| Line | XFA Description | (d) | (e) | (g) | (h) |
|------|-----------------|-----|-----|-----|-----|
| 8a (1099-B basis reported, no adj) | `{T2}.Row8a[0]` | `f1_23[0]` | `f1_24[0]` | `f1_25_RO[0]` **READ-ONLY** | `f1_26[0]` |
| 8b (8949 Box D) | `{T2}.Row8b[0]` | `f1_27[0]` | `f1_28[0]` | `f1_29[0]` | `f1_30[0]` |
| 9 (8949 Box E) | | `f1_31[0]` | `f1_32[0]` | `f1_33[0]` | `f1_34[0]` |
| 10 (8949 Box F) | | `f1_35[0]` | `f1_36[0]` | `f1_37[0]` | `f1_38[0]` |
| 11 (Form 4797 Pt I / 2439/6252/4684/6781/8824) | | | | | `f1_39[0]` |
| 12 (K-1 LT gain/loss) | | | | | `f1_40[0]` |
| 13 (Capital gain distributions) | | | | | `f1_41[0]` |
| 14 (LT capital loss carryover) | | | | | `f1_42[0]` |

| Field | Line | Description |
|-------|------|-------------|
| `{P1}.f1_43[0]` | **15** | **Net long-term capital gain/loss** |

### Page 2 - Summary

| Field | Line | Description |
|-------|------|-------------|
| `{P2}.f2_01[0]` | **16** | Combine lines 7 and 15 |
| `{P2}.f2_02[0]` | 18 | 28% Rate Gain Worksheet amount |
| `{P2}.f2_03[0]` | 19 | Unrecaptured Section 1250 Gain Worksheet amount |
| `{P2}.TagCorrectingSubform[0].f2_04[0]` | **21** | Capital loss deduction (smaller of loss on line 16 or $3,000/$1,500) |

### Page 2 - Checkboxes
| Field | Line | Answer |
|-------|------|--------|
| `{P2}.c2_1[0]` | 17 Yes | Both lines 15 and 16 are gains |
| `{P2}.c2_1[1]` | 17 No | Go to line 21 |
| `{P2}.c2_2[0]` | 20 Yes | Lines 18 & 19 both zero, not filing Form 4952 → use QDCG Worksheet |
| `{P2}.c2_2[1]` | 20 No | Complete lines 18-19 and Sched D Tax Worksheet |
| `{P2}.c2_3[0]` | 22 Yes | Have qualified dividends → use QDCG Worksheet |
| `{P2}.c2_3[1]` | 22 No | |

### Notes
- Line 21 is nested under `TagCorrectingSubform[0]` — a common IRS PDF quirk
- `f1_05_RO` and `f1_25_RO` are **read-only** fields (adjustments col for lines 1a/8a) — cannot be filled programmatically
- Schedule D has 3 Yes/No checkbox pairs (lines 17, 20, 22) that control which worksheet to use for tax computation
