#!/usr/bin/env python3
"""Reusable PDF form-filling engine for tax forms.

Usage:
    from fill_forms import fill_pdf, fill_irs_pdf, add_suffix

    # Generic PDF forms (CA 540, etc.) — handles checkboxes and radio buttons
    fill_pdf("blank.pdf", "filled.pdf",
             {"field_name": "value"},
             {"checkbox_name": True, "radio_parent RB": "/SelectedValue"})

    # IRS forms (1040, 8949, Schedule D) — matches checkboxes by /T value
    fields = add_suffix({"f1_04": "Robert", "f1_05": "Balian"})
    fill_irs_pdf("f1040_blank.pdf", "f1040_filled.pdf",
                 fields,
                 checkbox_values={"c1_1[0]": True},
                 radio_values={"c1_3": "/1", "c1_5": "/2"})
"""

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    NameObject, BooleanObject, DictionaryObject
)


def add_suffix(d, suffix="[0]"):
    """Add [0] suffix to text field keys for IRS XFA-based forms.

    IRS forms have field /T values like f1_04[0]. Text fields need the suffix
    appended to match. Checkbox keys (starting with 'c') are left as-is since
    they already include the suffix in the key name.

    Args:
        d: Dict of {field_name: value}
        suffix: Suffix to append (default "[0]")

    Returns:
        New dict with suffixed keys for text fields.
    """
    return {
        f"{k}{suffix}" if not k.startswith("c") else k: v
        for k, v in d.items()
    }


def fill_pdf(input_path, output_path, field_values, checkbox_values=None):
    """Fill a PDF form with given field values and checkbox states.

    Handles checkboxes (bool values) and radio buttons (string values matched
    against /AP/N keys on annotations). Matches fields by full parent-chain
    name and also by parent /T for radio button groups.

    For IRS forms, use fill_irs_pdf() instead — it matches checkboxes by
    the annotation's own /T value, which works better with IRS XFA structures.

    Args:
        input_path: Path to blank PDF form
        output_path: Path to write filled PDF
        field_values: Dict of {field_name: string_value} for text fields
        checkbox_values: Dict of {field_name: value} for checkboxes/radios.
            - True/False: check/uncheck the box
            - str: set radio button to this value (matched against /AP/N keys)
    """
    reader = PdfReader(input_path)
    writer = PdfWriter()
    writer.append(reader)

    _remove_xfa(writer)

    # Fill text fields
    for page in writer.pages:
        writer.update_page_form_field_values(
            page, field_values, auto_regenerate=False
        )

    # Handle checkboxes and radio buttons
    if checkbox_values:
        for page in writer.pages:
            annots = page.get("/Annots")
            if not annots:
                continue
            for annot_ref in annots:
                annot = annot_ref.get_object()

                # Try matching by full parent-chain name
                field_name = _get_full_name(annot)
                if field_name in checkbox_values:
                    _set_check_value(annot, checkbox_values[field_name])

                # Also try matching by parent /T (for radio button groups)
                parent_ref = annot.get("/Parent")
                if parent_ref:
                    pobj = parent_ref.get_object()
                    pname = str(pobj.get("/T", ""))
                    if pname in checkbox_values:
                        val = checkbox_values[pname]
                        if isinstance(val, str):
                            # Radio button — match against /AP/N keys
                            ap = annot.get("/AP", {})
                            n_keys = list(ap.get("/N", {}).keys()) if "/N" in ap else []
                            if val in n_keys:
                                annot.update({
                                    NameObject("/V"): NameObject(val),
                                    NameObject("/AS"): NameObject(val),
                                })
                                pobj.update({
                                    NameObject("/V"): NameObject(val),
                                })
                            else:
                                annot.update({
                                    NameObject("/AS"): NameObject("/Off"),
                                })
                        else:
                            _set_check_value(annot, val)

    _set_need_appearances(writer)
    writer.write(output_path)
    print(f"  Written: {output_path}")


def fill_irs_pdf(input_path, output_path, field_values,
                 checkbox_values=None, radio_values=None):
    """Fill IRS PDF forms, matching checkboxes by /T value directly.

    IRS forms have deeply nested XFA parent chains that produce paths like
    "topmostSubform[0].Page1[0].c1_3[0]" which won't match short keys like
    "c1_3[0]". This function matches by the annotation's own /T value instead.

    Args:
        input_path: Path to blank IRS PDF form
        output_path: Path to write filled PDF
        field_values: Dict of {field_name: string_value} — keys MUST include
            the [0] suffix (use add_suffix() to add it)
        checkbox_values: Dict of {field_t_value: bool} — keys are the /T value
            on the annotation (e.g., "c1_3[0]" not the full path)
        radio_values: Dict of {t_prefix: ap_n_value} for IRS radio-button-style
            exclGroups. Multiple annotations share a /T prefix (e.g. "c1_3")
            with suffixes like [0], [1], [2]. Each has different /AP/N keys.
            The annotation whose /AP/N contains the target value gets selected;
            all others in the group get set to /Off.
            Example: {"c1_3": "/1"} selects "Single" filing status.
    """
    reader = PdfReader(input_path)
    writer = PdfWriter()
    writer.append(reader)

    _remove_xfa(writer)

    # Fill text fields
    for page in writer.pages:
        writer.update_page_form_field_values(
            page, field_values, auto_regenerate=False
        )

    # Handle simple checkboxes — match by /T value directly
    if checkbox_values:
        for page in writer.pages:
            annots = page.get("/Annots")
            if not annots:
                continue
            for annot_ref in annots:
                annot = annot_ref.get_object()
                t = str(annot.get("/T", ""))
                if t in checkbox_values:
                    _set_check_value(annot, checkbox_values[t])

    # Handle radio buttons — match by /T prefix and /AP/N value
    if radio_values:
        for page in writer.pages:
            annots = page.get("/Annots")
            if not annots:
                continue
            for annot_ref in annots:
                annot = annot_ref.get_object()
                t = str(annot.get("/T", ""))
                for prefix, target in radio_values.items():
                    if t.startswith(prefix + "[") or t == prefix:
                        ap = annot.get("/AP", {})
                        n_keys = list(ap.get("/N", {}).keys()) if "/N" in ap else []
                        if target in n_keys:
                            annot.update({
                                NameObject("/V"): NameObject(target),
                                NameObject("/AS"): NameObject(target),
                            })
                        else:
                            annot.update({
                                NameObject("/AS"): NameObject("/Off"),
                            })
                        break

    _set_need_appearances(writer)
    writer.write(output_path)
    print(f"  Written: {output_path}")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _remove_xfa(writer):
    """Remove /XFA from /AcroForm to force AcroForm rendering."""
    if "/AcroForm" in writer._root_object:
        acroform = writer._root_object["/AcroForm"]
        if isinstance(acroform, DictionaryObject) and "/XFA" in acroform:
            del acroform["/XFA"]


def _set_need_appearances(writer):
    """Set NeedAppearances so PDF viewer regenerates field appearances."""
    if "/AcroForm" in writer._root_object:
        writer._root_object["/AcroForm"].update({
            NameObject("/NeedAppearances"): BooleanObject(True)
        })


def _set_check_value(annot, val):
    """Set a checkbox annotation to checked (True) or unchecked (False)."""
    if val:
        annot.update({
            NameObject("/V"): NameObject("/1"),
            NameObject("/AS"): NameObject("/1"),
        })
    else:
        annot.update({
            NameObject("/V"): NameObject("/Off"),
            NameObject("/AS"): NameObject("/Off"),
        })


def _get_full_name(annot, max_depth=100):
    """Get full field name by walking the /Parent chain."""
    parts = []
    obj = annot
    for _ in range(max_depth):
        t = obj.get("/T", "")
        if t:
            parts.insert(0, str(t))
        parent = obj.get("/Parent")
        if parent:
            obj = parent.get_object()
        else:
            break
    return ".".join(parts)
