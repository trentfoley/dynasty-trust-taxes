"""fill_1041.py — Form 1041 filler for Trent Foley Childrens 2021 Super Dynasty Trust.

Usage:
    python fill_1041.py [--year YYYY] [--csv PATH] [--output-dir PATH] [--dry-run]

Requires Python stdlib only (argparse, csv, json, subprocess, sys, pathlib).
Python executable: /c/ProgramData/miniconda3/python (NOT python3 -- Windows Store stub).
"""

import argparse
import csv
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def load_config(year=2025):
    """Load config/{year}.json. Hard-fails with clear message if missing."""
    path = Path("config") / f"{year}.json"
    if not path.exists():
        print(f"ERROR: Config file not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def load_fields(year=2025):
    """Load config/{year}_fields.json. Hard-fails if missing."""
    path = Path("config") / f"{year}_fields.json"
    if not path.exists():
        print(f"ERROR: Fields catalog not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args(cfg):
    """Build argparse using config defaults. Returns parsed namespace."""
    paths = cfg.get("paths", {})
    parser = argparse.ArgumentParser(
        description="Fill Form 1041 and attachments from brokerage CSV."
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2025,
        metavar="YYYY",
        help="Tax year (default: 2025)",
    )
    parser.add_argument(
        "--csv",
        default=paths.get("csv_input", "2025/XXXX-X123.CSV"),
        metavar="PATH",
        help="Path to brokerage CSV (default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir",
        default=paths.get("output_dir", "output"),
        metavar="PATH",
        help="Output directory for filled PDFs (default: %(default)s)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and compute without writing any files",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Dollar parsing
# ---------------------------------------------------------------------------

def parse_dollar(s):
    """Strip quotes, $, commas; return float. Returns 0.0 for empty strings."""
    s = s.strip().strip('"').strip("'").replace("$", "").replace(",", "").strip()
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


# ---------------------------------------------------------------------------
# CSV parser
# ---------------------------------------------------------------------------

def parse_csv(csv_path):
    """State-machine CSV parser.

    Returns dict with keys:
        div_1a (float)     — ordinary dividends (1099-DIV Box 1a)
        div_1b (float)     — qualified dividends (1099-DIV Box 1b)
        int_box1 (float)   — interest (1099-INT Box 1)
        transactions (list of dict)  — 1099-B rows

    Each transaction dict:
        description (str)
        date_acquired (str)    — may be "Various"
        date_sold (str)
        proceeds (float)
        cost (float)
        wash_sale (float)
        term (str)             — lowercased: "long term" or "short term"
        form8949_code (str)    — "D" or "A"
        covered (bool)
    """
    result = {
        "div_1a": 0.0,
        "div_1b": 0.0,
        "int_box1": 0.0,
        "transactions": [],
    }

    section = None       # "DIV" | "INT" | "B" | None
    b_col_headers_count = 0   # 1099-B has two header rows to skip

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for raw_row in reader:
            # Strip outer quotes from every cell
            row = [cell.strip().strip('"').strip() for cell in raw_row]

            # Skip completely blank rows and reset section
            if not any(row):
                section = None
                continue

            # Detect section headers
            first = row[0].strip('"').strip()
            if first == "Form 1099DIV":
                section = "DIV"
                continue
            if first == "Form 1099INT":
                section = "INT"
                continue
            if first == "Form 1099 B":
                section = "B"
                b_col_headers_count = 0
                continue

            # Skip column-header rows (Box, Description, Amount, Total, Details...)
            if first in ("Box", "Description", "1a", "1b", "1c") and section in ("DIV", "INT"):
                # Box/column header row — only skip if it's the header for the section itself
                if first == "Box":
                    continue

            # --- 1099-DIV ---
            if section == "DIV":
                box = first
                if box == "1a":
                    # Total is in col[3]; strip and parse
                    total_val = row[3] if len(row) > 3 else ""
                    result["div_1a"] = parse_dollar(total_val)
                elif box == "1b":
                    # Amount is in col[2]
                    amt_val = row[2] if len(row) > 2 else ""
                    result["div_1b"] = parse_dollar(amt_val)

            # --- 1099-INT ---
            elif section == "INT":
                box = first
                if box == "1":
                    # Total is in col[3]
                    total_val = row[3] if len(row) > 3 else ""
                    result["int_box1"] = parse_dollar(total_val)

            # --- 1099-B ---
            elif section == "B":
                # Two header rows after section header: field-number row and column-name row
                if b_col_headers_count < 2:
                    b_col_headers_count += 1
                    continue

                # Data rows
                if len(row) < 12:
                    continue

                description = row[0]
                date_acquired = row[1]
                date_sold = row[2]
                proceeds = parse_dollar(row[3])
                cost = parse_dollar(row[4])
                wash_sale = parse_dollar(row[6])
                term = row[7].lower()
                form8949_code = row[8].strip('"').strip()
                covered = row[11].strip('"').strip().lower() == "covered"

                result["transactions"].append({
                    "description": description,
                    "date_acquired": date_acquired,
                    "date_sold": date_sold,
                    "proceeds": proceeds,
                    "cost": cost,
                    "wash_sale": wash_sale,
                    "term": term,
                    "form8949_code": form8949_code,
                    "covered": covered,
                })

    return result


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def print_header(args, cfg):
    """Print 4-line run header."""
    paths = cfg.get("paths", {})
    blank_form = paths.get("blank_form", "forms/f1041.pdf")
    mode = "DRY RUN" if args.dry_run else "LIVE"
    print(f"CSV input:    {args.csv}")
    print(f"Blank form:   {blank_form}")
    print(f"Output dir:   {args.output_dir}")
    print(f"Mode:         {mode}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # 1. Load config (year=2025 default for initial load to get paths)
    cfg = load_config(year=2025)

    # 2. Load fields catalog
    fields = load_fields(year=2025)

    # 3. Parse args using loaded config for defaults
    args = parse_args(cfg)

    # Reload config/fields if a different year was specified
    if args.year != 2025:
        cfg = load_config(year=args.year)
        fields = load_fields(year=args.year)

    # 4. Print header
    print_header(args, cfg)

    # 5. Parse CSV
    parsed = parse_csv(args.csv)
    print("Parsed CSV")

    # 6. Dry-run: print parsed values and exit
    if args.dry_run:
        div_1a = parsed["div_1a"]
        div_1b = parsed["div_1b"]
        int_box1 = parsed["int_box1"]
        transactions = parsed["transactions"]

        print()
        print("--- Parsed Values ---")
        print(f"Ordinary dividends (1099-DIV Box 1a):  ${div_1a:.2f}")
        print(f"Qualified dividends (1099-DIV Box 1b): ${div_1b:.2f}")
        print(f"Interest income (1099-INT Box 1):       ${int_box1:.2f}")
        print(f"1099-B transactions: {len(transactions)}")
        for txn in transactions:
            gain = txn["proceeds"] - txn["cost"] + txn["wash_sale"]
            print(
                f"  [{txn['term']}] acq={txn['date_acquired']} sold={txn['date_sold']}"
                f"  proceeds=${txn['proceeds']:.2f} cost=${txn['cost']:.2f}"
                f"  wash_sale=${txn['wash_sale']:.2f} gain=${gain:.2f}"
                f"  code={txn['form8949_code']}"
            )
        sys.exit(0)

    # 7. Live mode (not yet implemented)
    print("Live mode not yet implemented", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
