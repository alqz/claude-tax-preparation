#!/usr/bin/env python3
"""Download blank tax form PDFs for a given tax year.

Downloads federal IRS forms and optionally CA FTB forms.
Validates each download is actually a PDF (not an HTML error page).

Usage:
    python download_forms.py 2025 ./forms
    python download_forms.py 2025 ./forms --state CA
    python download_forms.py 2025 ./forms --forms f1040 f8949
"""

import argparse
import os
import subprocess
import sys

# Federal forms: (filename, description)
FEDERAL_FORMS = [
    ("f1040", "Form 1040"),
    ("f8949", "Form 8949 (Sales and Dispositions)"),
    ("f1040sd", "Schedule D (Capital Gains and Losses)"),
]

# State forms: state -> [(filename_template, description)]
# filename_template uses {year} placeholder
STATE_FORMS = {
    "CA": [
        ("{year}-540", "CA Form 540"),
    ],
}


def download_file(url, output_path):
    """Download a file using curl. Returns True if successful PDF."""
    result = subprocess.run(
        ["curl", "-sL", "-o", output_path, "-w", "%{http_code}", url],
        capture_output=True, text=True
    )
    http_code = result.stdout.strip()

    if http_code != "200":
        return False, f"HTTP {http_code}"

    # Verify it's actually a PDF
    try:
        with open(output_path, "rb") as f:
            header = f.read(5)
        if header != b"%PDF-":
            os.remove(output_path)
            return False, "Not a PDF (got HTML or other content)"
    except Exception as e:
        return False, str(e)

    # Get file size
    size = os.path.getsize(output_path)
    if size < 1000:
        os.remove(output_path)
        return False, f"File too small ({size} bytes)"

    return True, f"{size:,} bytes"


def download_federal(year, output_dir, form_filter=None):
    """Download federal IRS forms."""
    forms = FEDERAL_FORMS
    if form_filter:
        forms = [(f, d) for f, d in forms if f in form_filter]

    results = []
    for filename, description in forms:
        output_path = os.path.join(output_dir, f"{filename}_blank.pdf")

        # Try irs-prior first (works for all years)
        url = f"https://www.irs.gov/pub/irs-prior/{filename}--{year}.pdf"
        ok, msg = download_file(url, output_path)

        if not ok:
            # Try irs-pdf (current year only, no year suffix)
            url = f"https://www.irs.gov/pub/irs-pdf/{filename}.pdf"
            ok, msg = download_file(url, output_path)

        status = "OK" if ok else "FAILED"
        results.append((status, description, filename, msg))
        print(f"  {status}: {description} ({filename}) — {msg}")

    return results


def download_state(state, year, output_dir):
    """Download state tax forms."""
    if state not in STATE_FORMS:
        print(f"  No forms configured for state: {state}")
        return []

    results = []
    for filename_tmpl, description in STATE_FORMS[state]:
        filename = filename_tmpl.format(year=year)

        if state == "CA":
            url = f"https://www.ftb.ca.gov/forms/{year}/{filename}.pdf"
            output_name = f"ca{filename.split('-')[-1]}_blank.pdf"
        else:
            url = f"https://example.com/{filename}.pdf"
            output_name = f"{filename}_blank.pdf"

        output_path = os.path.join(output_dir, output_name)
        ok, msg = download_file(url, output_path)

        status = "OK" if ok else "FAILED"
        results.append((status, description, output_name, msg))
        print(f"  {status}: {description} ({output_name}) — {msg}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Download blank tax form PDFs for a given tax year."
    )
    parser.add_argument("year", type=int, help="Tax year (e.g., 2025)")
    parser.add_argument("output_dir", help="Directory to save PDFs")
    parser.add_argument("--state", default=None,
                        help="State to download forms for (e.g., CA)")
    parser.add_argument("--forms", nargs="+", default=None,
                        help="Specific federal forms to download (e.g., f1040 f8949)")

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"=== Downloading {args.year} Federal Forms ===")
    fed_results = download_federal(args.year, args.output_dir, args.forms)

    state_results = []
    if args.state:
        print(f"\n=== Downloading {args.year} {args.state} State Forms ===")
        state_results = download_state(args.state, args.year, args.output_dir)

    # Summary
    all_results = fed_results + state_results
    ok_count = sum(1 for r in all_results if r[0] == "OK")
    fail_count = sum(1 for r in all_results if r[0] == "FAILED")

    print(f"\n=== Summary: {ok_count} downloaded, {fail_count} failed ===")
    if fail_count > 0:
        print("  Check URLs — forms may not yet be available for this tax year.")
        sys.exit(1)


if __name__ == "__main__":
    main()
