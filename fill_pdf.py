"""
fill_pdf.py — Thin AcroForm PDF filler using pypdf.

Usage:
    python fill_pdf.py --fields <json_file> --form <blank_pdf> [--output <path>]

Arguments:
    --fields  Path to a JSON file mapping AcroForm field names to values.
              Use "Yes" for checkboxes to be checked, "Off" to leave unchecked.
    --form    Path to the blank AcroForm PDF to fill.
    --output  Path for the filled output PDF.
              Default: output/2025_1041_filled.pdf

The script translates "Yes" checkbox values to the actual On-state value read
from the /_States_ array at runtime (not a hardcoded mapping). This handles PDFs
that use '1', '2', or other strings as their On-state value.

Hard-fail behavior: if any field name in the JSON is not found in the PDF's
AcroForm, the script prints an error to stderr and exits with code 1.
"""

import argparse
import json
import os
import sys

from pypdf import PdfReader, PdfWriter


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fill an AcroForm PDF with field values from a JSON file."
    )
    parser.add_argument(
        "--fields",
        required=True,
        metavar="<json_file>",
        help="Path to JSON file with field name/value pairs.",
    )
    parser.add_argument(
        "--form",
        required=True,
        metavar="<blank_pdf>",
        help="Path to the blank AcroForm PDF.",
    )
    parser.add_argument(
        "--output",
        default="output/2025_1041_filled.pdf",
        metavar="<path>",
        help="Output path for the filled PDF (default: output/2025_1041_filled.pdf).",
    )
    return parser.parse_args()


def get_on_state(field):
    """Return the On-state string for a checkbox field by reading /_States_.

    Looks for the first state that is not '/Off' and strips the leading '/'.
    Falls back to '1' if /_States_ is absent or has no non-Off state.
    """
    states = field.get("/_States_", [])
    for state in states:
        if state != "/Off":
            return state.lstrip("/")
    return "1"


def main():
    args = parse_args()

    # Load field values from JSON
    try:
        with open(args.fields, "r", encoding="utf-8") as fh:
            field_values = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: could not load fields JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    # Open the blank form
    try:
        reader = PdfReader(args.form)
    except Exception as exc:
        print(f"ERROR: could not open form PDF: {exc}", file=sys.stderr)
        sys.exit(1)

    known_fields = reader.get_fields() or {}

    # Hard-fail validation: collect ALL unknown field names before exiting
    unknown = [key for key in field_values if key not in known_fields]
    if unknown:
        for key in unknown:
            print(f"ERROR: field not found in AcroForm: '{key}'", file=sys.stderr)
        sys.exit(1)

    # Checkbox translation: replace "Yes" with the actual On-state value from /_States_
    translated = {}
    for field_name, value in field_values.items():
        if value == "Yes":
            pdf_field = known_fields[field_name]
            on_state = get_on_state(pdf_field)
            translated[field_name] = on_state
        else:
            translated[field_name] = value

    # Clone reader into writer and fill all pages in one call
    writer = PdfWriter()
    writer.clone_reader_document_root(reader)
    writer.update_page_form_field_values(
        page=None, fields=translated, auto_regenerate=True
    )

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    os.makedirs(output_dir or ".", exist_ok=True)

    # Write filled PDF
    with open(args.output, "wb") as fh:
        writer.write(fh)

    print(f"Filled PDF written to: {args.output}")


if __name__ == "__main__":
    main()
