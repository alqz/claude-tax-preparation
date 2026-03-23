#!/usr/bin/env python3
"""Extract year-specific tax values directly from downloaded PDF forms.

Parses the actual IRS and state forms to extract standard deductions,
thresholds, and other values — eliminating the risk of the LLM looking
up wrong-year values.

Usage:
    python extract_tax_tables.py forms/ > work/extracted_tables.json

    # Or import programmatically:
    from extract_tax_tables import extract_all
    tables = extract_all("forms/")

The output is a JSON dict that the build script imports as its Tax Tables
source. Values come directly from the forms — not from web searches or
LLM knowledge.

Supported extractions:
- Federal 1040: standard deduction (Single, MFJ, HOH)
- CA 540: standard deduction, Pease threshold, exemption credit amount
- CA Schedule CA: Pease limitation thresholds
- More can be added as needed
"""

import argparse
import json
import os
import re
import sys

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber required. Install with: pip install pdfplumber", file=sys.stderr)
    sys.exit(1)


def _extract_text(pdf_path):
    """Extract all text from a PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join(p.extract_text() or "" for p in pdf.pages)


def _find_dollar(text, pattern):
    """Find a dollar amount near a pattern. Returns float or None."""
    # Search for pattern, then grab the nearest dollar amount
    for line in text.split('\n'):
        if re.search(pattern, line, re.IGNORECASE):
            amounts = re.findall(r'\$([0-9,]+(?:\.[0-9]+)?)', line)
            if amounts:
                return float(amounts[0].replace(',', ''))
    return None


def _find_dollar_after(text, pattern):
    """Find the first dollar amount on the same line or next line after pattern."""
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if re.search(pattern, line, re.IGNORECASE):
            # Check this line
            amounts = re.findall(r'\$([0-9,]+(?:\.[0-9]+)?)', line)
            if amounts:
                return float(amounts[0].replace(',', ''))
            # Check next line
            if i + 1 < len(lines):
                amounts = re.findall(r'\$([0-9,]+(?:\.[0-9]+)?)', lines[i + 1])
                if amounts:
                    return float(amounts[0].replace(',', ''))
    return None


def extract_f1040(forms_dir):
    """Extract values from federal Form 1040."""
    path = _find_form(forms_dir, "f1040")
    if not path:
        return {}

    text = _extract_text(path)
    result = {}

    # Standard deduction — appears as "$XX,XXX" near "Single or"
    # The 1040 lists them in order: Single/MFS, MFJ/QSS, HOH
    # Find the section with "Standard deduction for—"
    std_ded_section = False
    amounts = []
    for line in text.split('\n'):
        if 'standard deduction' in line.lower() and ('single' in line.lower() or 'for—' in line.lower() or 'for-' in line.lower()):
            std_ded_section = True
        if std_ded_section:
            found = re.findall(r'\$([0-9,]+)', line)
            for f in found:
                val = float(f.replace(',', ''))
                if val > 5000:  # filter out line numbers
                    amounts.append(val)
        if len(amounts) >= 3:
            break

    if len(amounts) >= 1:
        result["standard_deduction_single"] = amounts[0]
    if len(amounts) >= 2:
        result["standard_deduction_mfj"] = amounts[1]
    if len(amounts) >= 3:
        result["standard_deduction_hoh"] = amounts[2]

    result["_source"] = os.path.basename(path)
    return result


def extract_ca540(forms_dir):
    """Extract values from California Form 540."""
    path = _find_form(forms_dir, "ca540")
    if not path:
        return {}

    text = _extract_text(path)
    result = {}

    # CA standard deduction — appears in the section that says
    # "Your California standard deduction shown below"
    # The values are on lines like "• Single or ... $5,706"
    in_std_section = False
    for line in text.split('\n'):
        if 'standard deduction' in line.lower() and ('shown below' in line.lower() or 'your california' in line.lower()):
            in_std_section = True
            continue
        if in_std_section:
            amounts = re.findall(r'\$([0-9,]+)', line)
            for a in amounts:
                val = float(a.replace(',', ''))
                if val < 50000:  # standard deductions are < $50K
                    if 'single' in line.lower() and 'standard_deduction_single' not in result:
                        result["standard_deduction_single"] = val
                    elif ('jointly' in line.lower() or 'head of' in line.lower()) and 'standard_deduction_mfj' not in result:
                        result["standard_deduction_mfj"] = val
            if len(result) >= 2:
                in_std_section = False

    # Exemption credit per dependent — look for "X $NNN ="
    match = re.search(r'X\s+\$([0-9,]+)\s*=', text)
    if match:
        result["dependent_exemption_credit"] = float(match.group(1).replace(',', ''))

    # Personal exemption credit — look for single exemption amount
    # Usually near "personal" and a small dollar amount
    for line in text.split('\n'):
        match = re.search(r'(\d+)\s*X\s+\$(\d+)\s*=', line)
        if match:
            count = int(match.group(1))
            amount = float(match.group(2))
            if count <= 2 and amount < 500:
                result["personal_exemption_credit"] = amount
                break

    result["_source"] = os.path.basename(path)
    return result


def extract_ca540ca(forms_dir):
    """Extract values from California Schedule CA (540)."""
    path = _find_form(forms_dir, "ca540ca")
    if not path:
        return {}

    text = _extract_text(path)
    result = {}

    # Pease limitation threshold — near "Single or married/RDP filing separately"
    # on the line about "Is your federal AGI more than"
    pease_section = False
    for line in text.split('\n'):
        if 'is your federal agi' in line.lower() and 'more than' in line.lower():
            pease_section = True
        if pease_section and ('single' in line.lower() or 'married' in line.lower()):
            amounts = re.findall(r'\$([0-9,]+)', line)
            for a in amounts:
                val = float(a.replace(',', ''))
                if val > 100000:  # threshold is > $100K
                    if 'single' in line.lower() and 'pease_threshold_single' not in result:
                        result["pease_threshold_single"] = val
                    elif 'married' in line.lower() and 'jointly' in line.lower() and 'pease_threshold_mfj' not in result:
                        result["pease_threshold_mfj"] = val

    result["_source"] = os.path.basename(path)
    return result


def _find_form(forms_dir, prefix):
    """Find a form PDF by exact prefix (e.g., 'f1040' matches 'f1040_blank.pdf'
    but NOT 'f1040s1_blank.pdf')."""
    candidates = []
    for fname in os.listdir(forms_dir):
        if not fname.endswith('.pdf'):
            continue
        # Strip _blank and .pdf to get the form name
        base = fname.lower().replace('_blank', '').replace('.pdf', '')
        if base == prefix:
            candidates.append((0, fname))  # exact match
        elif fname.lower().startswith(prefix + '_') or fname.lower().startswith(prefix + '.'):
            candidates.append((1, fname))  # prefix match with separator
    if candidates:
        candidates.sort()
        return os.path.join(forms_dir, candidates[0][1])
    return None


def extract_all(forms_dir):
    """Extract all available tax table values from forms in a directory.

    Returns:
        Dict with keys like "federal", "ca", each containing extracted values.
    """
    result = {}

    federal = extract_f1040(forms_dir)
    if federal:
        result["federal"] = federal

    ca = extract_ca540(forms_dir)
    if ca:
        result["ca_540"] = ca

    ca_ca = extract_ca540ca(forms_dir)
    if ca_ca:
        result["ca_schedule_ca"] = ca_ca

    return result


def main():
    parser = argparse.ArgumentParser(description="Extract tax table values from PDF forms")
    parser.add_argument("forms_dir", help="Directory containing blank PDF forms")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    if not os.path.isdir(args.forms_dir):
        print(f"ERROR: {args.forms_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    tables = extract_all(args.forms_dir)

    if not tables:
        print("WARNING: No values extracted. Check that forms are in the directory.", file=sys.stderr)
        sys.exit(1)

    indent = 2 if args.pretty else None
    print(json.dumps(tables, indent=indent))

    # Print summary to stderr
    total = sum(len(v) - 1 for v in tables.values())  # -1 for _source keys
    print(f"\nExtracted {total} values from {len(tables)} forms:", file=sys.stderr)
    for section, values in tables.items():
        source = values.get("_source", "?")
        count = len(values) - 1
        print(f"  {section}: {count} values from {source}", file=sys.stderr)


if __name__ == "__main__":
    main()
