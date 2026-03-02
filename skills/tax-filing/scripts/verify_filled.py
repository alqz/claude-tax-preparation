#!/usr/bin/env python3
"""Verify filled PDF form fields against expected values.

Reads back all field values from a filled PDF and compares them to an
expected values JSON file. Reports OK / MISSING / MISMATCH for each field.

Usage:
    python verify_filled.py filled.pdf expected.json

    # expected.json format:
    {
        "text_fields": {
            "f1_04[0]": "Robert",
            "f1_05[0]": "Balian",
            "540-2019": "55,364"
        },
        "checkboxes": {
            "c1_3[0]": true,
            "c1_5[1]": true
        },
        "radio_buttons": {
            "540-1036 RB": "/Box 1 . Single.",
            "540-5010 RB": "/Checking"
        }
    }
"""

import argparse
import json
import sys

from pypdf import PdfReader


def verify(pdf_path, expected):
    """Verify filled PDF fields against expected values.

    Args:
        pdf_path: Path to filled PDF
        expected: Dict with optional keys:
            - text_fields: {field_name: expected_string_value}
            - checkboxes: {field_t_value: True/False}
            - radio_buttons: {parent_name: expected_ap_value}

    Returns:
        (ok_count, fail_count, results) where results is a list of
        (status, field, expected, actual) tuples.
    """
    reader = PdfReader(pdf_path)

    text_expected = expected.get("text_fields", {})
    check_expected = expected.get("checkboxes", {})
    radio_expected = expected.get("radio_buttons", {})

    text_found = {}
    check_found = {}
    radio_found = {}

    for page in reader.pages:
        annots = page.get("/Annots") or []
        for annot in annots:
            obj = annot.get_object()
            t = str(obj.get("/T", ""))
            v = str(obj.get("/V", ""))
            as_val = str(obj.get("/AS", ""))

            # Text fields — match by /T
            if t in text_expected:
                text_found[t] = v if v != "None" else ""

            # Checkboxes — match by /T
            if t in check_expected:
                check_found[t] = as_val

            # Radio buttons — match by parent /T
            parent_ref = obj.get("/Parent")
            if parent_ref:
                pobj = parent_ref.get_object()
                pname = str(pobj.get("/T", ""))
                if pname in radio_expected and as_val not in ("", "None", "/Off"):
                    radio_found[pname] = as_val

    results = []
    ok = 0
    fail = 0

    # Check text fields
    for field, exp_val in text_expected.items():
        actual = text_found.get(field)
        if actual is None:
            results.append(("MISSING", field, exp_val, "(not found)"))
            fail += 1
        elif actual != exp_val:
            results.append(("MISMATCH", field, exp_val, actual))
            fail += 1
        else:
            results.append(("OK", field, exp_val, actual))
            ok += 1

    # Check checkboxes
    for field, exp_val in check_expected.items():
        actual_as = check_found.get(field)
        expected_as = "/1" if exp_val else "/Off"
        if actual_as is None:
            results.append(("MISSING", field, expected_as, "(not found)"))
            fail += 1
        elif actual_as != expected_as:
            results.append(("MISMATCH", field, expected_as, actual_as))
            fail += 1
        else:
            results.append(("OK", field, expected_as, actual_as))
            ok += 1

    # Check radio buttons
    for field, exp_val in radio_expected.items():
        actual = radio_found.get(field)
        if actual is None:
            results.append(("MISSING", field, exp_val, "(not found)"))
            fail += 1
        elif actual != exp_val:
            results.append(("MISMATCH", field, exp_val, actual))
            fail += 1
        else:
            results.append(("OK", field, exp_val, actual))
            ok += 1

    return ok, fail, results


def main():
    parser = argparse.ArgumentParser(
        description="Verify filled PDF form fields against expected values."
    )
    parser.add_argument("pdf", help="Path to filled PDF form")
    parser.add_argument("expected", help="Path to expected values JSON file")

    args = parser.parse_args()

    with open(args.expected) as f:
        expected = json.load(f)

    ok, fail, results = verify(args.pdf, expected)

    print(f"=== Verifying: {args.pdf} ===\n")
    for status, field, exp, actual in results:
        if status == "OK":
            print(f"  OK:       {field} = {actual}")
        elif status == "MISMATCH":
            print(f"  MISMATCH: {field} expected={exp} actual={actual}")
        else:
            print(f"  MISSING:  {field} expected={exp}")

    print(f"\n  Results: {ok} OK, {fail} FAILED")
    if fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
