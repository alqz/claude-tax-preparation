# IRS Form 1040 - Field Name Mappings (2024)

> **Year note**: Created from 2024 forms. Field names are generally stable year-to-year but MUST be spot-checked with `discover_fields.py` when filing a new tax year. Verify ~5 key fields (name, SSN, AGI, tax, refund) — if they match, trust the rest.

Field names are fully qualified paths from the PDF form structure.

**Field discovery**: AcroForm has NO `/TU` tooltips. Use PyMuPDF to extract the XFA template stream — field descriptions are in `<assist><speak>` XML elements. Run `python scripts/discover_fields.py form.pdf --xfa-only` for quick discovery.

## Prefixes

```
P1 = "topmostSubform[0].Page1[0]"
P2 = "topmostSubform[0].Page2[0]"
ADDR = f"{P1}.Address_ReadOrder[0]"
LINE = f"{P1}.Line4a-11_ReadOrder[0]"
```

## Page 1 - Identity & Income

### Header (DO NOT USE - fiscal year fields)
| Field | y | x | Purpose |
|-------|---|---|---------|
| `{P1}.f1_01[0]` | 718 | 226 | Fiscal year begin - NOT a name field |
| `{P1}.f1_02[0]` | 718 | 348 | Fiscal year end - NOT a name field |
| `{P1}.f1_03[0]` | 718 | 439 | Fiscal year - NOT a name field |

### Name & SSN (y~690)
| Field | y | x | Purpose | Notes |
|-------|---|---|---------|-------|
| `{P1}.f1_04[0]` | 690 | 36 | Your first name | |
| `{P1}.f1_05[0]` | 690 | 239 | Last name | |
| `{P1}.f1_06[0]` | 690 | 469 | Your SSN | 9 chars max, no dashes |
| `{P1}.f1_07[0]` | 666 | 36 | Spouse first name | |
| `{P1}.f1_08[0]` | 666 | 239 | Spouse last name | |
| `{P1}.f1_09[0]` | 666 | 469 | Spouse SSN | |

### Address (under Address_ReadOrder)
| Field | y | x | Purpose |
|-------|---|---|---------|
| `{ADDR}.f1_10[0]` | 642 | 36 | Street address |
| `{ADDR}.f1_11[0]` | 642 | 419 | Apt number |
| `{ADDR}.f1_12[0]` | 618 | 36 | City |
| `{ADDR}.f1_13[0]` | 618 | 339 | State (2-letter) |
| `{ADDR}.f1_14[0]` | 618 | 404 | ZIP code |
| `{ADDR}.f1_15[0]` | 594 | 36 | Foreign country |
| `{ADDR}.f1_16[0]` | 594 | 260 | Foreign province |
| `{ADDR}.f1_17[0]` | 594 | 404 | Foreign postal code |

### Checkboxes - Filing Status
| Field | y | x | Status |
|-------|---|---|--------|
| `{P1}.FilingStatus_ReadOrder[0].c1_3[0]` | 584 | 103 | Single |
| `{P1}.FilingStatus_ReadOrder[0].c1_3[1]` | 572 | 103 | Married Filing Jointly |
| `{P1}.FilingStatus_ReadOrder[0].c1_3[2]` | 560 | 103 | Married Filing Separately |
| `{P1}.c1_3[0]` | 584 | 369 | Head of Household |
| `{P1}.c1_3[1]` | 560 | 369 | Qualifying Surviving Spouse |

### Checkboxes - Other Page 1
| Field | y | x | Purpose | Notes |
|-------|---|---|---------|-------|
| `{P1}.c1_1[0]` | 598 | 504 | Presidential Campaign - You | |
| `{P1}.c1_2[0]` | 598 | 540 | Presidential Campaign - Spouse | |
| `{P1}.c1_4[0]` | 524 | 103 | Nonresident alien spouse treated as resident | |
| `{P1}.c1_5[0]` | 483 | 504 | **Digital Assets: Yes** | |
| `{P1}.c1_5[1]` | 483 | 540 | **Digital Assets: No** | |
| `{P1}.c1_6[0]` | 470 | 182 | Someone can claim You as dependent | Do NOT check for single filer |
| `{P1}.c1_7[0]` | 470 | 283 | Someone can claim Spouse as dependent | Do NOT check for single filer |
| `{P1}.c1_8[0]` | 458 | 96 | **Spouse itemizes / dual-status alien** | NOT born before 1/2/1960 |
| `{P1}.c1_9[0]` | 441 | 117 | You born before Jan 2, 1960 | |
| `{P1}.c1_10[0]` | 441 | 261 | You are blind | |
| `{P1}.c1_11[0]` | 441 | 362 | Spouse born before Jan 2, 1960 | |
| `{P1}.c1_12[0]` | 441 | 506 | Spouse is blind | |
| `{LINE}.c1_22[0]` | 176 | 465 | **Line 6c: Lump-sum SS election** | NOT Schedule D |
| `{LINE}.c1_23[0]` | 164 | 465 | Line 7: Schedule D not required | |

**Warning**: `c1_22` is the lump-sum Social Security election (Line 6c), NOT a Schedule D checkbox despite its y-position near Line 7.

### Dependents Table
| Field | Purpose |
|-------|---------|
| `{P1}.Dependents_ReadOrder[0].c1_13[0]` | More than 4 dependents checkbox |
| `Table_Dependents[0].Row1[0].f1_20[0]` | Dependent 1 name |
| `Table_Dependents[0].Row1[0].f1_21[0]` | Dependent 1 SSN |
| `Table_Dependents[0].Row1[0].f1_22[0]` | Dependent 1 relationship |
| `Table_Dependents[0].Row1[0].c1_14[0]` | Dependent 1 child tax credit |
| `Table_Dependents[0].Row1[0].c1_15[0]` | Dependent 1 credit for other dependents |
| (Rows 2-4 follow same pattern with sequential field numbers) | |

### MFS / HOH Info
| Field | y | x | Purpose |
|-------|---|---|---------|
| `{P1}.f1_18[0]` | 534 | 288 | MFS spouse name / HOH qualifying child name |
| `{P1}.f1_19[0]` | 510 | 338 | Nonresident alien spouse name |

### Income Section
| Field | y | x | Line | Description |
|-------|---|---|------|-------------|
| `{P1}.f1_32[0]` | 354 | 504 | **1a** | Wages, salaries, tips (W-2 box 1) |
| `{P1}.f1_33[0]` | 342 | 504 | 1b | Household employee income |
| `{P1}.f1_34[0]` | 330 | 504 | 1c | Tip income not on W-2 |
| `{P1}.f1_35[0]` | 318 | 504 | 1d | Medicaid waiver payments |
| `{P1}.f1_36[0]` | 306 | 504 | 1e | Employer-provided adoption benefits |
| `{P1}.f1_37[0]` | 294 | 504 | 1f | Wages from Form 8919 |
| `{P1}.f1_38[0]` | 282 | 504 | 1g | Strike benefits |
| `{P1}.f1_39[0]` | 270 | 504 | 1h | Other earned income |
| `{P1}.f1_40[0]` | 258 | **410** | **1i** | Nontaxable combat pay (**OFFSET x=410, not 504**) |
| `{P1}.f1_41[0]` | 246 | 504 | **1z** | Total W-2 income |
| `{P1}.f1_42[0]` | 234 | 252 | 2a | Tax-exempt interest (left column) |
| `{P1}.f1_43[0]` | 234 | 504 | **2b** | Taxable interest |
| `{P1}.f1_44[0]` | 222 | 252 | **3a** | Qualified dividends (left column) |
| `{P1}.f1_45[0]` | 222 | 504 | **3b** | Ordinary dividends |

### Income Lines 4a-6b (under Line4a-11_ReadOrder)
| Field | y | x | Line | Description |
|-------|---|---|------|-------------|
| `{LINE}.f1_46[0]` | 210 | 252 | 4a | IRA distributions (left column) |
| `{LINE}.f1_47[0]` | 210 | 504 | 4b | Taxable IRA |
| `{LINE}.f1_48[0]` | 198 | 252 | 5a | Pensions/annuities (left column) |
| `{LINE}.f1_49[0]` | 198 | 504 | 5b | Taxable pensions |
| `{LINE}.f1_50[0]` | 186 | 252 | 6a | Social Security benefits (left column) |
| `{LINE}.f1_51[0]` | 186 | 504 | 6b | Taxable Social Security |

### Income Lines 7-15
| Field | y | x | Line | Description |
|-------|---|---|------|-------------|
| `{LINE}.f1_52[0]` | 162 | 504 | **7** | Capital gain/loss (from Schedule D) |
| `{LINE}.f1_53[0]` | 150 | 504 | 8 | Other income (Schedule 1) |
| `{LINE}.f1_54[0]` | 138 | 504 | **9** | Total income |
| `{LINE}.f1_55[0]` | 126 | 504 | 10 | Adjustments (Schedule 1) |
| `{LINE}.f1_56[0]` | 114 | 504 | **11** | AGI |
| `{P1}.f1_57[0]` | 102 | 504 | **12** | Standard deduction or itemized |
| `{P1}.f1_58[0]` | 90 | 504 | 13 | Qualified business income deduction |
| `{P1}.f1_59[0]` | 78 | 504 | **14** | Total deductions |
| `{P1}.f1_60[0]` | 66 | 504 | **15** | Taxable income |

## Page 2 - Tax, Credits, Payments

### Tax & Credits
| Field | y | x | Line | Description |
|-------|---|---|------|-------------|
| `{P2}.c2_1[0]` | 746 | 297 | 16 | Tax checkbox: from 8814 |
| `{P2}.c2_2[0]` | 746 | 348 | 16 | Tax checkbox: from 4972 |
| `{P2}.c2_3[0]` | 746 | 398 | 16 | Tax checkbox: other form |
| `{P2}.f2_01[0]` | 744 | 410 | 16 | Tax from other form (partial) |
| `{P2}.f2_02[0]` | 744 | 504 | **16** | Tax |
| `{P2}.f2_03[0]` | 732 | 504 | 17 | Amount from Schedule 2 Part I |
| `{P2}.f2_04[0]` | 720 | 504 | **18** | Sum of 16 + 17 |
| `{P2}.f2_05[0]` | 708 | 504 | 19 | Child tax credit |
| `{P2}.f2_06[0]` | 696 | 504 | 20 | Amount from Schedule 3 Part I |
| `{P2}.f2_07[0]` | 684 | 504 | 21 | Sum of 19 + 20 |
| `{P2}.f2_08[0]` | 672 | 504 | **22** | Subtract 21 from 18 |
| `{P2}.f2_09[0]` | 660 | 504 | 23 | Other taxes (Schedule 2 Part II) |
| `{P2}.f2_10[0]` | 648 | 504 | **24** | Total tax |

### Payments
| Field | y | x | Line | Description |
|-------|---|---|------|-------------|
| `{P2}.f2_11[0]` | 624 | 410 | **25a** | W-2 federal withholding |
| `{P2}.f2_12[0]` | 612 | 410 | 25b | 1099 withholding |
| `{P2}.f2_13[0]` | 600 | 410 | 25c | Other withholding |
| `{P2}.f2_14[0]` | 588 | 504 | **25d** | Total withholding |
| `{P2}.f2_15[0]` | 576 | 504 | 26 | Estimated tax payments |
| `{P2}.f2_16[0]` | 564 | 410 | 27a | EIC |
| `{P2}.f2_17[0]` | 552 | 410 | 27b | Nontaxable combat pay (EIC) |
| `{P2}.f2_18[0]` | 540 | 410 | 27c | Prior year earned income (EIC) |
| `{P2}.f2_19[0]` | 528 | 410 | 28 | Additional child tax credit |
| `{P2}.f2_20[0]` | 516 | 410 | 29 | American opportunity credit |
| `{P2}.f2_21[0]` | 504 | 504 | 31 | Amount from Schedule 3 Part II |
| `{P2}.f2_22[0]` | 492 | 504 | **32** | Total other payments |
| `{P2}.f2_23[0]` | 480 | 504 | **33** | Total payments |

### Refund / Amount Owed
| Field | y | x | Line | Description |
|-------|---|---|------|-------------|
| `{P2}.f2_24[0]` | 468 | 504 | **34** | Overpaid |
| `{P2}.c2_4[0]` | 470 | 465 | 34 | Amount overpaid checkbox |
| `{P2}.c2_5[0]` | 457 | 377 | 35b | Checking account |
| `{P2}.c2_5[1]` | 457 | 435 | 35b | Savings account |
| `{P2}.f2_25[0]` | 457 | 173 | 35b | Routing number (via `RoutingNo[0]`) |
| `{P2}.f2_26[0]` | 445 | 173 | 35d | Account number (via `AccountNo[0]`) |
| `{P2}.f2_27[0]` | 432 | 410 | **35a** | Refund amount |
| `{P2}.f2_28[0]` | 408 | 504 | 36 | Applied to next year estimated tax |
| `{P2}.f2_29[0]` | 396 | 410 | 37 | Amount you owe |
| `{P2}.f2_30[0]` | | | 38 | Estimated tax penalty |

### Third Party Designee
| Field | y | x | Line | Description |
|-------|---|---|------|-------------|
| `{P2}.c2_6[0]` | 376 | | | Third party designee: **Yes** |
| `{P2}.c2_6[1]` | 376 | | | Third party designee: **No** |
| `{P2}.f2_30[0]` | 354 | 144 | | Designee's name |
| `{P2}.f2_31[0]` | 354 | 331 | | Designee phone number |
| `{P2}.f2_32[0]` | 354 | 504 | | Designee PIN (MaxLen=5) |

### Sign Here
| Field | y | x | Description |
|-------|---|---|-------------|
| `{P2}.f2_33[0]` | 300 | 325 | Your occupation |
| `{P2}.f2_34[0]` | 300 | 504 | Your Identity Protection PIN (MaxLen=6) |
| `{P2}.f2_35[0]` | 270 | 325 | Spouse's occupation |
| `{P2}.f2_36[0]` | 270 | 504 | Spouse's Identity Protection PIN (MaxLen=6) |
| `{P2}.f2_37[0]` | 258 | 135 | **Phone no.** (NOT preparer name) |
| `{P2}.f2_38[0]` | 258 | 324 | **Email address** (NOT preparer signature) |

### Paid Preparer
| Field | y | x | Description |
|-------|---|---|-------------|
| `{P2}.f2_39[0]` | 234 | 92 | Preparer's name |
| `{P2}.f2_40[0]` | 234 | 447 | PTIN (MaxLen=11) |
| `{P2}.c2_7[0]` | 237 | | Self-employed checkbox |
| `{P2}.f2_41[0]` | 222 | 143 | Firm's name |
| `{P2}.f2_42[0]` | 222 | 500 | Firm's phone no. |
| `{P2}.f2_43[0]` | 210 | 151 | Firm's address |
| `{P2}.f2_44[0]` | 210 | 500 | Firm's EIN (MaxLen=10) |

### Notes
- Signature line itself is NOT fillable — must be signed by hand after printing
- `f2_37` and `f2_38` are YOUR phone/email, not the preparer's
- Mailing address (refund, CA resident): Department of the Treasury, IRS, Fresno, CA 93888-0002
