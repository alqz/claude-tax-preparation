# Tax Computation Reference

**Year-agnostic**: This file contains formulas, worksheets, and rules that are stable across tax years. All bracket amounts, standard deductions, thresholds, and credit amounts MUST be looked up fresh from IRS.gov and FTB.ca.gov for the tax year being filed. Do NOT hardcode or reuse prior-year values.

## QDCG Tax Worksheet (Qualified Dividends and Capital Gain Tax)

Use this when the taxpayer has qualified dividends (1040 Line 3a > 0) or net capital gain (Schedule D Line 15 > 0, or Line 16 > 0).

### Steps:
1. **Line 1**: Taxable income (Form 1040 Line 15)
2. **Line 2**: Qualified dividends (Form 1040 Line 3a)
3. **Line 3**: Schedule D Line 15 (if > 0), else capital gain from 1040 Line 7 (if > 0), else 0
4. **Line 4**: Add lines 2 + 3
5. **Line 5**: Investment interest expense deduction (if applicable, usually 0)
6. **Line 6**: Subtract line 5 from line 4
7. **Line 7**: Subtract line 6 from line 1 (this is ordinary income)
8. **Line 8**: Enter the 0% capital gains threshold for the filing status (look up from IRS)
9. **Line 9**: Smaller of line 1 or line 8
10. **Line 10**: Smaller of line 7 or line 9
11. **Line 11**: Subtract line 10 from line 9 (taxed at 0%)
12. **Line 12**: Smaller of line 1 or line 6
13. **Line 13**: Line 11
14. **Line 14**: Subtract line 13 from line 12
15. **Line 15**: Enter the 15% capital gains threshold for the filing status (look up from IRS)
16. **Line 16**: Smaller of line 1 or line 15
17. **Line 17**: Add lines 7 + 11
18. **Line 18**: Subtract line 17 from line 16 (if ≤ 0, enter 0)
19. **Line 19**: Smaller of line 14 or line 18
20. **Line 20**: Multiply line 19 by 15%
21. **Line 21**: Subtract line 19 from line 14
22. **Line 22**: Multiply line 21 by 20%
23. **Line 23**: Tax on line 7 (ordinary income) using regular brackets
24. **Line 24**: Add lines 20 + 22 + 23
25. **Line 25**: Tax on line 1 using regular brackets (full taxable income)
26. **Line 26**: **Tax = smaller of line 24 or line 25**

### Key insight:
- Line 11 = amount taxed at 0% (qualified dividends/gains within the 0% threshold)
- Line 19 = amount taxed at 15%
- Line 21 = amount taxed at 20%
- Line 7 = ordinary income taxed at regular bracket rates
- The final tax is the LESSER of the QDCG calculation or the regular bracket tax

## Capital Loss Rules

- **Annual deduction limit**: $3,000 ($1,500 if MFS) against ordinary income
- **Carryover**: Excess losses carry forward indefinitely
- **Carryover character**: Short-term losses offset short-term gains first; long-term losses offset long-term gains first
- **Netting order**:
  1. Net short-term gains/losses within Part I
  2. Net long-term gains/losses within Part II
  3. Combine on Schedule D Line 16
  4. If net loss > $3,000, limit to -$3,000 on Line 21
  5. Carryover = total net loss - $3,000

### Capital Loss Carryover Worksheet

When prior year had a net capital loss greater than $3,000, compute the carryover:

1. Start with prior year's Schedule D Line 21 (the $3,000 loss claimed)
2. Prior year's taxable income (1040 Line 15) — if negative, use 0
3. Add back the capital loss deduction to taxable income
4. Apply remaining loss to offset short-term first, then long-term
5. Any remaining short-term loss carries forward as short-term
6. Any remaining long-term loss carries forward as long-term

The IRS publishes a "Capital Loss Carryover Worksheet" in the Schedule D instructions each year. Follow that worksheet exactly.

## California Tax Computation

### CA vs Federal Differences
- CA does NOT tax qualified dividends at preferential rates — all income taxed at regular CA rates
- CA has its own standard deduction (different from federal — look up from FTB)
- CA uses **exemption credits** (subtracted from tax), not exemption deductions
- CA mental health services tax: additional 1% on taxable income over $1,000,000
- CA SDI (State Disability Insurance) from W-2 box 14 is a payroll deduction, NOT claimed on Form 540

### CA 540 Computation Flow
1. Federal AGI → Line 13
2. CA subtractions (Line 14) and additions (Line 16) → CA AGI (Line 17)
3. Subtract CA standard deduction → Taxable income (Line 19)
4. Compute tax from CA brackets (look up current year rates from FTB.ca.gov)
5. Subtract personal exemption credits (look up current year amount from FTB.ca.gov)
6. Result = tax after credits

## Values to Look Up Each Year

Before computing, you MUST look up these values from authoritative sources:

### Federal (from IRS.gov)
- Tax brackets for all filing statuses
- Standard deduction amounts
- 0% / 15% / 20% capital gains rate thresholds
- Additional standard deduction for age 65+ or blind

### California (from FTB.ca.gov)
- Tax rate schedules for all filing statuses
- Standard deduction amounts
- Personal exemption credit amount
- Dependent exemption credit amount
- Mental health services tax threshold (historically $1M)
