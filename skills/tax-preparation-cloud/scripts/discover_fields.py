#!/usr/bin/env python3
"""Discover all form field names, types, and metadata in one or more PDFs.

Tries both pypdf (/TU tooltips) and PyMuPDF (XFA <speak> descriptions).
For XFA forms, also cross-references AcroForm annotations to report
checkbox/radio /AP/N keys alongside XFA field descriptions.

Usage:
    python discover_fields.py form.pdf
    python discover_fields.py f1040.pdf f8949.pdf ca540.pdf
    python discover_fields.py form.pdf --search "routing"
    python discover_fields.py form.pdf --type Btn --page 0
    python discover_fields.py form.pdf --xfa-only
    python discover_fields.py form.pdf --json
    python discover_fields.py form.pdf --json --xfa-only > fields.json
    python discover_fields.py form.pdf --compact          # minimal field→description mapping
"""

import argparse
import json
import sys


def discover_acroform(pdf_path, page_filter=None, search=None, type_filter=None):
    """Dump all AcroForm fields using pypdf."""
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    fields = []

    for pi, page in enumerate(reader.pages):
        if page_filter is not None and pi != page_filter:
            continue
        annots = page.get("/Annots") or []
        for annot in annots:
            obj = annot.get_object()
            t = str(obj.get("/T", ""))
            tu = str(obj.get("/TU", ""))
            ft = str(obj.get("/FT", ""))
            v = str(obj.get("/V", ""))
            as_val = str(obj.get("/AS", ""))
            rect = obj.get("/Rect", [])

            # Get parent info
            parent_ref = obj.get("/Parent")
            pname = ""
            if parent_ref:
                pobj = parent_ref.get_object()
                pname = str(pobj.get("/T", ""))
                if not ft:
                    ft = str(pobj.get("/FT", ""))

            # Get /AP/N keys for radio buttons
            ap = obj.get("/AP", {})
            n_keys = []
            if "/N" in ap:
                n_keys = list(ap["/N"].keys())

            # Determine display name
            name = t if t else f"(parent: {pname})"
            field_type = ft.replace("/", "") if ft else "?"

            # Apply filters
            if type_filter and field_type != type_filter:
                continue
            if search:
                searchable = f"{t} {tu} {pname}".lower()
                if search.lower() not in searchable:
                    continue

            fields.append({
                "page": pi,
                "name": name,
                "parent": pname,
                "type": field_type,
                "tooltip": tu if tu and tu != "None" else "",
                "value": v if v and v != "None" else "",
                "as": as_val if as_val and as_val != "None" else "",
                "ap_n_keys": n_keys,
                "rect": [round(float(r), 1) for r in rect] if rect else [],
            })

    return fields


def _get_acroform_btn_map(pdf_path):
    """Build a map of checkbox/radio field names to their /AP/N keys.

    Returns {field_t_value: [list of /AP/N keys]} for all Btn-type annotations.
    Used to cross-reference with XFA discovery so radio options are visible.
    """
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    btn_map = {}

    for page in reader.pages:
        annots = page.get("/Annots") or []
        for annot in annots:
            obj = annot.get_object()
            t = str(obj.get("/T", ""))
            ft = str(obj.get("/FT", ""))

            # Check parent for type if not on annotation itself
            if not ft:
                parent_ref = obj.get("/Parent")
                if parent_ref:
                    ft = str(parent_ref.get_object().get("/FT", ""))

            if ft != "/Btn":
                continue

            ap = obj.get("/AP", {})
            if "/N" in ap:
                n_keys = [k for k in ap["/N"].keys() if k != "/Off"]
                if n_keys and t:
                    btn_map.setdefault(t, []).extend(n_keys)

    return btn_map


def discover_xfa(pdf_path, search=None):
    """Extract XFA field descriptions using PyMuPDF (fitz).

    Finds the XFA template by parsing /AcroForm -> /XFA array to locate the
    template xref directly. Does NOT use brute-force xref scanning (unreliable).

    Uses regex instead of xml.etree.ElementTree because IRS XFA XML has
    unbound namespace prefixes and line-breaks inside closing tags that
    break XML parsers.

    Also cross-references AcroForm Btn annotations to include /AP/N keys
    for checkbox and radio fields, so callers can see radio options.
    """
    try:
        import fitz
    except ImportError:
        print("  PyMuPDF (fitz) not installed — skipping XFA discovery", file=sys.stderr)
        return []

    import re

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"  Cannot open PDF: {e}", file=sys.stderr)
        return []

    # Phase 1: Find XFA template xref via /AcroForm -> /XFA array
    template_xref = None
    for i in range(1, doc.xref_length()):
        try:
            obj = doc.xref_object(i)
            if '/XFA' in obj:
                match = re.search(r'\(template\)\s+(\d+)\s+0\s+R', obj)
                if match:
                    template_xref = int(match.group(1))
                    break
        except Exception:
            continue

    if template_xref is None:
        doc.close()
        return []

    # Phase 2: Extract fields using regex (NOT XML parser)
    stream = doc.xref_stream(template_xref)
    text = stream.decode('utf-8', errors='replace')
    doc.close()

    # Phase 3: Get AcroForm Btn annotations for cross-referencing
    btn_map = _get_acroform_btn_map(pdf_path)

    xfa_fields = []
    for m in re.finditer(r'<(?:field|exclGroup)\s+[^>]*name="([^"]+)"', text):
        name = m.group(1)
        tag = "exclGroup" if "exclGroup" in text[m.start():m.start()+20] else "field"
        chunk = text[m.start():m.start() + 2000]
        speak_m = re.search(
            r'<speak[^>]*\n?>(.*?)</speak\s*\n?\s*>', chunk, re.DOTALL
        )
        speak = ""
        if speak_m:
            speak = speak_m.group(1).strip()
            if 'Cat. No.' in speak:
                speak = ""

        if not name:
            continue
        if search and search.lower() not in f"{name} {speak}".lower():
            continue

        # Cross-reference: collect /AP/N keys from all AcroForm annotations
        # whose /T starts with this field name (e.g. c1_3[0], c1_3[1], ...)
        ap_n_options = {}
        for btn_t, keys in btn_map.items():
            if btn_t.startswith(name + "[") or btn_t == name:
                for k in keys:
                    ap_n_options[btn_t] = k
        # Deduplicate: group by option value
        radio_options = {}
        for btn_t, val in ap_n_options.items():
            radio_options.setdefault(val, []).append(btn_t)

        entry = {"name": name, "speak": speak, "tag": tag}
        if radio_options:
            entry["radio_options"] = radio_options
        xfa_fields.append(entry)

    return xfa_fields


def _format_text(pdf_path, acroform_fields, xfa_fields, xfa_only):
    """Format discovery results as human-readable text."""
    lines = []

    if not xfa_only:
        lines.append(f"=== AcroForm Fields: {pdf_path} ===")
        if acroform_fields:
            for f in acroform_fields:
                parts = [f"Page {f['page']}", f"Name={f['name']}"]
                if f["parent"]:
                    parts.append(f"Parent={f['parent']}")
                parts.append(f"Type={f['type']}")
                if f["tooltip"]:
                    parts.append(f"TU={f['tooltip'][:100]}")
                if f["value"]:
                    parts.append(f"V={f['value']}")
                if f["as"]:
                    parts.append(f"AS={f['as']}")
                if f["ap_n_keys"]:
                    parts.append(f"AP/N={f['ap_n_keys']}")
                if f["rect"]:
                    parts.append(f"Rect={f['rect']}")
                lines.append("  " + " | ".join(parts))
            lines.append(f"\n  Total: {len(acroform_fields)} fields")
        else:
            lines.append("  No AcroForm fields found (or none matched filters)")

    lines.append(f"\n=== XFA Field Descriptions: {pdf_path} ===")
    if xfa_fields:
        for f in xfa_fields:
            speak = f": {f['speak']}" if f["speak"] else ""
            tag_note = f" [{f['tag']}]" if f["tag"] == "exclGroup" else ""
            radio = ""
            if f.get("radio_options"):
                opts = ", ".join(
                    f"{v}={ks[0]}" for v, ks in f["radio_options"].items()
                )
                radio = f"  radio: {opts}"
            lines.append(f"  {f['name']}{tag_note}{speak}{radio}")
        lines.append(f"\n  Total: {len(xfa_fields)} XFA fields")
    else:
        lines.append("  No XFA template found (or PyMuPDF not installed)")

    return "\n".join(lines)


def _format_json(pdf_path, acroform_fields, xfa_fields, xfa_only):
    """Format discovery results as JSON."""
    result = {"pdf": pdf_path}
    if not xfa_only:
        result["acroform"] = acroform_fields
    result["xfa"] = xfa_fields
    return result


def _format_compact(pdf_path, acroform_fields, xfa_fields):
    """Format as a minimal {field_name: description} mapping.

    For text fields: {"f1_32": "Line 1a. Wages, salaries, tips..."}
    For radios:      {"c1_3": {"desc": "Filing status", "options": {"/1": "MFJ", "/2": "Single"}}}
    For checkboxes:  {"540-1029 CB": {"desc": "Same address", "type": "checkbox"}}

    Prefers XFA speak descriptions when available, falls back to AcroForm tooltips.
    """
    mapping = {}

    # XFA fields (IRS forms) — these have the best descriptions
    for f in xfa_fields:
        name = f["name"]
        desc = f.get("speak", "")
        if f.get("radio_options"):
            # Radio/exclGroup — include the option values
            mapping[name] = {"desc": desc, "options": {
                val: kids[0] for val, kids in f["radio_options"].items()
            }}
        elif desc:
            mapping[name] = desc

    # AcroForm fields (CA forms, or fallback for IRS) — use tooltip
    for f in acroform_fields:
        name = f["name"]
        parent = f.get("parent", "")
        tooltip = f.get("tooltip", "")

        # For radio children, group under parent name
        if parent and f["type"] == "Btn" and f.get("ap_n_keys"):
            key = parent
            if key not in mapping:
                mapping[key] = {"desc": tooltip, "options": {}}
            opts = mapping[key].get("options", {})
            for k in f["ap_n_keys"]:
                if k != "/Off":
                    opts[k] = name
            mapping[key]["options"] = opts
            continue

        # Standalone checkbox (parent name with CB/RB suffix)
        if f["type"] == "Btn" and not f.get("ap_n_keys"):
            full = f"{parent} CB" if parent else name
            if full not in mapping:
                mapping[full] = {"desc": tooltip, "type": "checkbox"}
            continue

        # Text field — skip if already from XFA with a description
        if name in mapping:
            continue

        # Use parent-prefixed name if the field itself has no /T
        if not name or name.startswith("(parent:"):
            continue

        if tooltip:
            mapping[name] = tooltip

    return {"pdf": pdf_path, "fields": mapping}


def main():
    parser = argparse.ArgumentParser(
        description="Discover PDF form field names, types, and metadata."
    )
    parser.add_argument("pdfs", nargs="+", metavar="PDF",
                        help="Path(s) to PDF form(s)")
    parser.add_argument("--page", type=int, default=None,
                        help="Only show fields on this page (0-indexed)")
    parser.add_argument("--search", "-s", default=None,
                        help="Filter fields by keyword (searches name, tooltip, parent)")
    parser.add_argument("--type", "-t", default=None, dest="type_filter",
                        help="Filter by field type: Tx (text), Btn (checkbox/radio), Ch (choice)")
    parser.add_argument("--xfa-only", action="store_true",
                        help="Only show XFA field descriptions (skip AcroForm)")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Output as JSON instead of human-readable text")
    parser.add_argument("--compact", action="store_true",
                        help="Output minimal {field_name: description} mapping as JSON")

    args = parser.parse_args()

    all_results = []
    for pdf_path in args.pdfs:
        acroform_fields = discover_acroform(
            pdf_path, args.page, args.search, args.type_filter
        )
        xfa_fields = discover_xfa(pdf_path, args.search)

        if args.compact:
            all_results.append(
                _format_compact(pdf_path, acroform_fields, xfa_fields)
            )
        elif args.json_output:
            all_results.append(
                _format_json(pdf_path, acroform_fields, xfa_fields, args.xfa_only)
            )
        else:
            print(_format_text(pdf_path, acroform_fields, xfa_fields, args.xfa_only))
            if pdf_path != args.pdfs[-1]:
                print("\n" + "=" * 60 + "\n")

    if args.compact or args.json_output:
        output = all_results if len(all_results) > 1 else all_results[0]
        json.dump(output, sys.stdout, indent=2)
        print()


if __name__ == "__main__":
    main()
