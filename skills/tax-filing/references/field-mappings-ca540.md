# CA Form 540 - Field Name Mappings (2024)

> **Year note**: Created from 2024 forms. Field names are generally stable year-to-year but MUST be spot-checked with `discover_fields.py` when filing a new tax year. Verify ~5 key fields (name, SSN, AGI, tax, refund) — if they match, trust the rest.

## Naming Convention

CA Form 540 uses flat field names: `540-PPNN` where:
- `PP` = page number (1-6)
- `NN` = sequential field number within that page

**Important**: Field numbers are sequential per page, NOT form line numbers. You must map by y-coordinate position when debugging.

Checkbox fields end with `" CB"` suffix (note the space before CB).
Radio button groups end with `" RB"` suffix.

**Field discovery**: No XFA. Every AcroForm field has a `/TU` tooltip with a clear description. Use pypdf to read them:
```python
from pypdf import PdfReader
for annot in page.get("/Annots", []):
    obj = annot.get_object()
    print(f"{obj.get('/T')}: {obj.get('/TU')}")
```

## Side 1 (Page 1) - Filing Status, Name, Address, Exemptions

### Header
| Field | Description | Notes |
|-------|-------------|-------|
| `540-1001 CB` | Amended return checkbox | |
| `540-1002` | Fiscal year end month | max:2 |

### Filing Status
| Field | Description | Notes |
|-------|-------------|-------|
| `540-1035 CB` | CA filing status different from federal | |
| `540-1036 RB` | Filing status radio buttons | 5 children: 1=Single, 2=MFJ, 3=MFS, 4=HOH, 5=QSS |
| `540-1037` | Line 3 - Spouse SSN (if MFS) | |
| `540-1038` | Line 5 - Year spouse died (QSS) | max:4 |
| `540-1039` | Line 5 - See instructions field | |
| `540-1040 CB` | Line 6 - Dependent of another person | |

### Identity
| Field | Description | Notes |
|-------|-------------|-------|
| `540-1003` | Your first name | |
| `540-1004` | Middle initial | max:1 |
| `540-1005` | Last name | |
| `540-1006` | Suffix | max:4 |
| `540-1007` | Your SSN/ITIN | max:9 |
| `540-1008` | Spouse/RDP first name | |
| `540-1009` | Spouse/RDP middle initial | max:1 |
| `540-1010` | Spouse/RDP last name | |
| `540-1011` | Spouse/RDP suffix | max:4 |
| `540-1012` | Spouse/RDP SSN/ITIN | max:9 |

### Additional Info
| Field | Description | Notes |
|-------|-------------|-------|
| `540-1013` | Additional information | |
| `540-1014` | Principal Business Activity code | max:6 |
| `540-1024` | Your DOB (MM/DD/YYYY) | max:10 |
| `540-1025` | Spouse/RDP DOB | max:10 |
| `540-1026` | Your prior name | |
| `540-1027` | Spouse/RDP prior name | |
| `540-1028` | County at time of filing | |

### Address
| Field | Description | Notes |
|-------|-------------|-------|
| `540-1015` | Street address | |
| `540-1016` | Apt/Suite number | |
| `540-1017` | Private Mailbox | |
| `540-1018` | City | |
| `540-1019` | State | max:2 |
| `540-1020` | ZIP code | max:10 |
| `540-1021` | Foreign country name | |
| `540-1022` | Foreign province/state/county | |
| `540-1023` | Foreign postal code | |

### Principal Residence (if different)
| Field | Description | Notes |
|-------|-------------|-------|
| `540-1029 CB` | Same as principal residence checkbox | |
| `540-1030` | Principal residence street address | |
| `540-1031` | Principal residence apt number | |
| `540-1032` | Principal residence city | |
| `540-1033` | Principal residence state | max:2 |
| `540-1034` | Principal residence ZIP | max:10 |

### Exemptions (Lines 7-9)
| Field | Line | Description | Notes |
|-------|------|-------------|-------|
| `540-1041` | 7 | Number of personal exemptions | max:1 |
| `540-1042` | 7 | Exemption amount (N x $149 for 2024) | max:12 |
| `540-1043` | 8 | Blind exemptions count | max:1 |
| `540-1044` | 8 | Blind exemption amount | max:12 |
| `540-1045` | 9 | Senior (65+) exemptions count | max:1 |
| `540-1046` | 9 | Senior exemption amount | max:12 |

## Side 2 (Page 2) - Dependents, Income, Tax

### Page Header (repeated on all pages)
| Field | Description |
|-------|-------------|
| `540-2001` | Your name |
| `540-2002` | Your SSN |

### Dependents
| Field | Description | Notes |
|-------|-------------|-------|
| `540-2003` | Dependent 1 first name | |
| `540-2004` | Dependent 1 last name | |
| `540-2005` | Dependent 1 SSN | max:11 |
| `540-2006` | Dependent 1 relationship | |
| `540-2007`-`540-2010` | Dependent 2 (same pattern) | |
| `540-2011`-`540-2014` | Dependent 3 (same pattern) | |
| `540-2015` | Line 10 - Total dependent exemptions | max:2 |
| `540-2016` | Line 10 - Dependent exemption amount | max:12 |

### Income & Deductions
| Field | Line | Description |
|-------|------|-------------|
| `540-2017` | 11 | Total exemption amount |
| `540-2018` | 12 | State wages (W-2 box 16) |
| `540-2019` | **13** | **Federal AGI** |
| `540-2020` | 14 | CA adjustments - subtractions |
| `540-2021` | 15 | Line 13 minus Line 14 |
| `540-2022` | 16 | CA adjustments - additions |
| `540-2023` | 17 | CA adjusted gross income |
| `540-2024` | 18 | Standard deduction or itemized |
| `540-2025` | **19** | **Taxable income** |

### Tax Computation
| Field | Line | Description | Notes |
|-------|------|-------------|-------|
| `540-2026 CB` | 31 | Tax Table checkbox (A) | |
| `540-2027 CB` | 31 | Rate Schedule checkbox (B) | |
| `540-2028 CB` | 31 | FTB 3800 checkbox (C) | |
| `540-2029 CB` | 31 | FTB 3803 checkbox (D) | |
| `540-2030` | **31** | **Tax amount** | |
| `540-2031` | 32 | Exemption credits (from Line 11) | |
| `540-2032` | 33 | Tax minus exemption credits | |
| `540-2033 CB` | 34 | Schedule G-1 checkbox (A) | |
| `540-2034 CB` | 34 | FTB 5870A checkbox (B) | |
| `540-2035` | 34 | Additional tax | |
| `540-2036` | 35 | Line 33 + Line 34 | |

### Credits (Lines 40-44)
| Field | Line | Description |
|-------|------|-------------|
| `540-2037` | 40 | Child/Dependent Care credit |
| `540-2038`-`540-2043` | 43-44 | Other credits (name, code, amount pairs) |

## Side 3 (Page 3) - Credits, Other Taxes, Payments

### Credits
| Field | Line | Description |
|-------|------|-------------|
| `540-3003` | 45 | Additional credits |
| `540-3004` | 46 | Renter's credit |
| `540-3005` | 47 | Total credits |
| `540-3006` | 48 | Tax after credits (Line 35 - Line 47) |

### Other Taxes
| Field | Line | Description |
|-------|------|-------------|
| `540-3007` | 61 | AMT |
| `540-3008` | 62 | Mental Health Services Tax (1% on >$1M) |
| `540-3009` | 63 | Other taxes / credit recapture |
| `540-3010` | **64** | **Total tax** |

### Payments
| Field | Line | Description |
|-------|------|-------------|
| `540-3011` | **71** | **CA income tax withheld** (W-2 box 17) |
| `540-3012` | 72 | Estimated tax payments |
| `540-3013` | 73 | Withholding (592-B/593) |
| `540-3014` | 74 | Reserved |
| `540-3015` | 75 | Earned income tax credit (EITC) |
| `540-3016` | 76 | Young Child Tax Credit (YCTC) |
| `540-3017` | 77 | Foster Youth Tax Credit (FYTC) |
| `540-3018` | **78** | **Total payments and credits** |

### Use Tax & ISR
| Field | Line | Description | Notes |
|-------|------|-------------|-------|
| `540-3019` | 91 | Use tax | Enter 0 if none, don't leave blank |
| `540-3020 RB` | 91 | Use tax zero reason radio buttons | 2 options |
| `540-3021 CB` | 92 | ISR penalty checkbox | |
| `540-3022` | 92 | ISR penalty amount | |
| `540-3023` | 93 | Payments balance | |
| `540-3024` | 94 | Use tax balance | |
| `540-3025` | 95 | Payments after ISR | |
| `540-3026` | 96 | ISR penalty balance | |
| `540-3027` | 97 | Overpaid | |

## Side 4 (Page 4) - Overpaid, Contributions

| Field | Line | Description |
|-------|------|-------------|
| `540-4003` | 98 | Applied to 2025 estimated tax |
| `540-4004` | 99 | Overpaid tax available |
| `540-4005` | 100 | Tax due |
| `540-4006`-`540-4023` | | Voluntary contributions (18 funds, codes 400-447) |
| `540-4024` | 110 | Total contributions |

## Side 5 (Page 5) - Amount Owed / Refund

| Field | Line | Description | Notes |
|-------|------|-------------|-------|
| `540-5002` | 111 | Amount you owe | |
| `540-5003` | 112 | Interest/late penalties | |
| `540-5004 RB` | 113 | Underpayment reason radio buttons | 2 options |
| `540-5005` | 113 | Underpayment of estimated tax | |
| `540-5006` | 114 | Total amount due | |
| `540-5007` | **115** | **REFUND** | |
| `540-5008` | 116 | Direct deposit amount | |
| `540-5009` | 116 | Routing number | max:9 |
| `540-5010 RB` | 116 | Account type (Checking/Savings) | 2 options |
| `540-5011` | 116 | Account number | max:17 |
| `540-5012` | 117 | Secondary deposit amount | |
| `540-5013` | 117 | Secondary routing number | |
| `540-5014 RB` | 117 | Secondary account type | 2 options |
| `540-5015` | 117 | Secondary account number | |
| `540-5016 CB` | | Voter registration info checkbox | |
| `540-5017 RB` | | Health care coverage (Yes/No) | 2 options |

## Side 6 (Page 6) - Signature, Preparer, Third Party

| Field | Description | Notes |
|-------|-------------|-------|
| `540-6001` | Date signed (MM/DD/YYYY) | max:10 |
| `540-6002` | Email address | |
| `540-6003` | Phone number | max:10 |
| `540-6004` | Preparer firm name | |
| `540-6005` | PTIN | max:9 |
| `540-6006` | Firm address | |
| `540-6007` | Firm FEIN | max:9 |
| `540-6008 RB` | Third party designee (Yes/No) | 2 options |
| `540-6009` | Third party designee name | |
| `540-6010` | Third party phone | max:10 |
