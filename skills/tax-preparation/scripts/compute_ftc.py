#!/usr/bin/env python3
"""Compute Foreign Tax Credit (Form 1116) with all adjustments.

This script exists because the FTC computation has a 100% error rate
when left to LLM reasoning. The two systematic failures are:
1. Currency conversion (using CAD values without converting to USD)
2. Line 18 QDCG adjustment (IRC 904(b)(2)(B)) — adjusting the
   denominator to account for income taxed at preferential rates

This script handles both correctly.

Usage:
    from compute_ftc import compute_ftc

    result = compute_ftc(
        foreign_tax_paid_local=3200.00,        # in foreign currency
        foreign_income_local=8500.00,          # in foreign currency
        exchange_rate=1.25,                    # foreign currency per USD
        filing_status="single",
        total_agi=120000,
        taxable_income=104250,
        us_tax=17400,                          # 1040 line 16
        deduction_amount=15750,                # std or itemized deduction used
        qualified_dividends=500,               # 1040 line 3a
        net_capital_gain=3000,                 # Schedule D line 16 (if positive)
        top_marginal_rate=0.22,                # highest bracket rate
    )

    print(result)
    # Returns dict with: foreign_tax_usd, foreign_income_usd,
    # allocated_deduction, net_foreign_income, qdcg_adjustment,
    # adjusted_taxable, limitation_ratio, max_credit, credit_allowed,
    # carryover, rows (for TaxWorkbook.computation())
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_workbook import Row, round_dollar


def compute_ftc(
    foreign_tax_paid_local: float,
    foreign_income_local: float,
    exchange_rate: float,
    filing_status: str,
    total_agi: int,
    taxable_income: int,
    us_tax: int,
    deduction_amount: int,
    qualified_dividends: int = 0,
    net_capital_gain: int = 0,
    top_marginal_rate: float = 0.37,
    lt_rate: float = 0.20,
    category: str = "general",
    country: str = "Canada",
) -> dict:
    """Compute Foreign Tax Credit per Form 1116 instructions.

    All inputs should be rounded to whole dollars where they come from
    form lines (AGI, taxable income, tax, deduction). The foreign
    amounts should be exact (pre-rounding).

    Args:
        foreign_tax_paid_local: Tax paid in foreign currency
        foreign_income_local: Foreign source income in foreign currency
        exchange_rate: Foreign currency units per 1 USD (e.g., 1.398 CAD/USD)
        filing_status: "single", "mfj", etc.
        total_agi: Form 1040 line 11
        taxable_income: Form 1040 line 15
        us_tax: Form 1040 line 16
        deduction_amount: Form 1040 line 14 (std or itemized deduction used)
        qualified_dividends: Form 1040 line 3a (for QDCG adjustment)
        net_capital_gain: Schedule D line 16 if positive (for QDCG adjustment)
        top_marginal_rate: Highest marginal tax rate (0.37 for 2025)
        lt_rate: Long-term capital gains rate applicable (0.20 for high income)
        category: "general", "passive", "section_901j", etc.
        country: Country name for documentation

    Returns:
        Dict with all intermediate values, final credit, carryover, and
        Row objects for TaxWorkbook.computation().
    """

    # ---------------------------------------------------------------
    # Step 1: Convert foreign currency to USD
    # ---------------------------------------------------------------
    # exchange_rate is "foreign per USD" (e.g., 1.398 CAD = 1 USD)
    # So divide by the rate to get USD
    foreign_tax_usd = foreign_tax_paid_local / exchange_rate
    foreign_income_usd = foreign_income_local / exchange_rate

    # ---------------------------------------------------------------
    # Step 2: Allocate deductions to foreign income (Part I)
    # ---------------------------------------------------------------
    # Form 1116 Line 3: allocate the deduction proportionally
    allocation_ratio = round_dollar(foreign_income_usd) / total_agi
    allocated_deduction = deduction_amount * allocation_ratio
    net_foreign_income = round_dollar(foreign_income_usd) - round_dollar(allocated_deduction)

    # ---------------------------------------------------------------
    # Step 3: Line 18 — QDCG adjustment (IRC 904(b)(2)(B))
    # ---------------------------------------------------------------
    # When the QDCG worksheet is used (qualified dividends or capital
    # gains exist), the denominator must be adjusted to prevent the
    # FTC from being inflated by income taxed at preferential rates.
    #
    # The adjustment removes the "rate differential" portion of QDCG
    # income from the denominator. For income taxed at 20% instead of
    # 37%, the adjustment factor is (37% - 20%) / 37% = 0.4595.
    #
    # This is the computation that 100% of test agents got wrong.

    qdcg_amount = qualified_dividends + net_capital_gain
    qdcg_adjustment = 0

    if qdcg_amount > 0 and top_marginal_rate > 0:
        # Determine which QDCG is at 20% vs 15% vs 0%
        # For simplicity and correctness: if the taxpayer's ordinary
        # income exceeds the 15%/20% threshold, ALL QDCG is at the
        # lt_rate. This is the common case for high-income filers.
        #
        # The adjustment factor: (top_rate - preferential_rate) / top_rate
        # At 20% CG rate: (0.37 - 0.20) / 0.37 = 0.4595
        # At 15% CG rate: (0.37 - 0.15) / 0.37 = 0.5946
        # At 0% CG rate:  (0.37 - 0.00) / 0.37 = 1.0000

        adjustment_factor = (top_marginal_rate - lt_rate) / top_marginal_rate
        qdcg_adjustment = qdcg_amount * adjustment_factor

    adjusted_taxable = taxable_income - round_dollar(qdcg_adjustment)

    # ---------------------------------------------------------------
    # Step 4: Limitation ratio and maximum credit (Part III)
    # ---------------------------------------------------------------
    if adjusted_taxable > 0:
        limitation_ratio = net_foreign_income / adjusted_taxable
    else:
        limitation_ratio = 0

    max_credit = round_dollar(us_tax * limitation_ratio)

    # ---------------------------------------------------------------
    # Step 5: Credit allowed = lesser of tax paid or max credit
    # ---------------------------------------------------------------
    foreign_tax_rounded = round_dollar(foreign_tax_usd)
    credit_allowed = min(foreign_tax_rounded, max_credit)
    carryover = foreign_tax_rounded - credit_allowed

    # ---------------------------------------------------------------
    # Build result
    # ---------------------------------------------------------------
    rows = [
        Row(f"Foreign tax paid ({country} currency)",
            val=foreign_tax_paid_local,
            formula=f"From T4 / foreign tax document"),
        Row(f"Foreign income ({country} currency)",
            val=foreign_income_local,
            formula=f"From T4 / foreign tax document"),
        Row(f"Exchange rate ({country} per USD)",
            val=exchange_rate,
            formula="IRS yearly average rate"),
        Row(""),
        Row("Foreign tax (USD)", line="9",
            val=foreign_tax_usd,
            formula=f"{foreign_tax_paid_local} / {exchange_rate}"),
        Row("Foreign income (USD)", line="1a",
            val=foreign_income_usd,
            formula=f"{foreign_income_local} / {exchange_rate}"),
        Row(""),
        Row("Deduction allocation ratio", line="3f",
            val=allocation_ratio,
            formula=f"{round_dollar(foreign_income_usd)} / {total_agi}"),
        Row("Allocated deduction", line="3g",
            val=allocated_deduction,
            formula=f"{deduction_amount} × {allocation_ratio:.6f}"),
        Row("Net foreign source income", line="7",
            val=net_foreign_income,
            formula=f"{round_dollar(foreign_income_usd)} - {round_dollar(allocated_deduction)}",
            is_subtotal=True),
        Row(""),
        Row("QDCG amount (qual div + net CG)",
            val=qdcg_amount,
            formula=f"{qualified_dividends} + {net_capital_gain}"),
        Row(f"QDCG adjustment factor ({top_marginal_rate}-{lt_rate})/{top_marginal_rate}",
            val=adjustment_factor if qdcg_amount > 0 else 0,
            formula=f"({top_marginal_rate} - {lt_rate}) / {top_marginal_rate}",
            notes="IRC 904(b)(2)(B)"),
        Row("QDCG adjustment",
            val=qdcg_adjustment,
            formula=f"{qdcg_amount} × {adjustment_factor:.4f}" if qdcg_amount > 0 else "N/A"),
        Row("Adjusted taxable income", line="18",
            val=adjusted_taxable,
            formula=f"{taxable_income} - {round_dollar(qdcg_adjustment)}",
            is_subtotal=True),
        Row(""),
        Row("Limitation ratio", line="19",
            val=limitation_ratio,
            formula=f"{net_foreign_income} / {adjusted_taxable}"),
        Row("US tax", line="20", val=us_tax),
        Row("Maximum credit", line="21",
            val=max_credit,
            formula=f"{us_tax} × {limitation_ratio:.5f}"),
        Row(""),
        Row("Credit allowed", line="24",
            val=credit_allowed,
            formula=f"min({foreign_tax_rounded}, {max_credit})",
            is_total=True),
        Row("Carryover to next year",
            val=carryover,
            formula=f"{foreign_tax_rounded} - {credit_allowed}",
            notes="10-year carryforward"),
    ]

    return {
        "foreign_tax_usd": foreign_tax_rounded,
        "foreign_income_usd": round_dollar(foreign_income_usd),
        "allocated_deduction": round_dollar(allocated_deduction),
        "net_foreign_income": net_foreign_income,
        "qdcg_adjustment": round_dollar(qdcg_adjustment),
        "adjusted_taxable": adjusted_taxable,
        "limitation_ratio": limitation_ratio,
        "max_credit": max_credit,
        "credit_allowed": credit_allowed,
        "carryover": carryover,
        "rows": rows,
        "category": category,
        "country": country,
    }


if __name__ == "__main__":
    # Self-test with example values
    result = compute_ftc(
        foreign_tax_paid_local=3200.00,
        foreign_income_local=8500.00,
        exchange_rate=1.25,
        filing_status="single",
        total_agi=120000,
        taxable_income=104250,
        us_tax=17400,
        deduction_amount=15750,
        qualified_dividends=500,
        net_capital_gain=3000,
    )

    print("FTC Self-Test:")
    print(f"  Foreign tax (USD):    ${result['foreign_tax_usd']:,}")
    print(f"  Foreign income (USD): ${result['foreign_income_usd']:,}")
    print(f"  Net foreign income:   ${result['net_foreign_income']:,}")
    print(f"  QDCG adjustment:      ${result['qdcg_adjustment']:,}")
    print(f"  Adjusted taxable:     ${result['adjusted_taxable']:,}")
    print(f"  Limitation ratio:     {result['limitation_ratio']:.5f}")
    print(f"  Max credit:           ${result['max_credit']:,}")
    print(f"  Credit allowed:       ${result['credit_allowed']:,}")
    print(f"  Carryover:            ${result['carryover']:,}")
