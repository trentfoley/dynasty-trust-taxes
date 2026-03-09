"""fill_1041.py — Form 1041 filler for Trent Foley Childrens 2021 Super Dynasty Trust.

Usage:
    python fill_1041.py [--year YYYY] [--csv PATH] [--output-dir PATH] [--dry-run]

Requires Python stdlib only (argparse, csv, json, subprocess, sys, pathlib).
Python executable: /c/ProgramData/miniconda3/python (NOT python3 -- Windows Store stub).
"""

import argparse
import csv
import json
import subprocess
import sys
import tempfile
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
# Computation functions
# ---------------------------------------------------------------------------

def compute_schedule_d(transactions):
    """Net short-term and long-term capital gains from 1099-B transactions.

    For each transaction: adjusted_cost = cost + wash_sale (IRS Form 8949 Box 1g).
    gain_loss = proceeds - adjusted_cost.
    Short-term: form8949_code == 'A'. Long-term: form8949_code == 'D'.

    Returns dict with st/lt proceeds, cost, wash_sale, net, net_combined, and rows.
    """
    st_proceeds = 0.0
    st_cost = 0.0
    st_wash_sale = 0.0
    lt_proceeds = 0.0
    lt_cost = 0.0
    lt_wash_sale = 0.0
    rows = []

    for txn in transactions:
        adjusted_cost = txn["cost"] + txn["wash_sale"]
        gain_loss = txn["proceeds"] - adjusted_cost
        row = dict(txn)
        row["gain_loss"] = gain_loss
        rows.append(row)

        if txn["form8949_code"] == "A":
            st_proceeds += txn["proceeds"]
            st_cost += txn["cost"]
            st_wash_sale += txn["wash_sale"]
        elif txn["form8949_code"] == "D":
            lt_proceeds += txn["proceeds"]
            lt_cost += txn["cost"]
            lt_wash_sale += txn["wash_sale"]

    st_net = st_proceeds - (st_cost + st_wash_sale)
    lt_net = lt_proceeds - (lt_cost + lt_wash_sale)
    net_combined = st_net + lt_net

    return {
        "st_proceeds": st_proceeds,
        "st_cost": st_cost,
        "st_wash_sale": st_wash_sale,
        "st_net": round(st_net, 2),
        "lt_proceeds": lt_proceeds,
        "lt_cost": lt_cost,
        "lt_wash_sale": lt_wash_sale,
        "lt_net": round(lt_net, 2),
        "net_combined": round(net_combined, 2),
        "rows": rows,
    }


def compute_form_1041_page1(csv_data, sched_d, cfg):
    """Compute all Form 1041 Page 1 values.

    Note: total_income uses ordinary dividends (qualified dividends is a subset
    already included in ordinary dividends — do not double-count).
    """
    exemption = cfg.get("trust_exemption", cfg.get("trust", {}).get("exemption", 100))
    interest = csv_data["int_box1"]
    ordinary_dividends = csv_data["div_1a"]
    qualified_dividends = csv_data["div_1b"]
    capital_gain_loss = sched_d["net_combined"]
    total_income = round(interest + ordinary_dividends + capital_gain_loss, 2)
    taxable_income = round(total_income - exemption, 2)

    return {
        "interest_income": interest,
        "ordinary_dividends": ordinary_dividends,
        "qualified_dividends": qualified_dividends,
        "capital_gain_loss": capital_gain_loss,
        "total_income": total_income,
        "exemption": float(exemption),
        "taxable_income": taxable_income,
    }


def compute_schedule_b(page1):
    """Compute Schedule B field values for a non-distributing trust.

    All distribution fields are $0. Income distribution deduction is $0.
    Distributable net income equals total income (adjusted total income).
    Accounting income (Line 8, complex trust only) equals total income per 2024 precedent.
    """
    return {
        "adjusted_total_income": page1["total_income"],
        "accounting_income": page1["total_income"],
        "income_required_to_be_distributed": 0.0,
        "other_amounts_distributed": 0.0,
        "total_distributions": 0.0,
        "distributable_net_income": page1["total_income"],
        "income_distribution_deduction": 0.0,
    }


def compute_schedule_g(taxable_income, qual_div, lt_net_gain, cfg):
    """Compute Schedule G Line 1a tax via QD&CG worksheet.

    All bracket values come from cfg — never hardcoded.
    Returns dict with preferential/ordinary breakdown, bucket amounts, and tax totals.
    """
    brackets = cfg["ordinary_income_brackets"]
    qdcg = cfg["qdcg_worksheet"]

    b10 = brackets["10_pct_max"]    # 3150
    b24 = brackets["24_pct_max"]    # 11450
    b35 = brackets["35_pct_max"]    # 15650

    zero_max = qdcg["0_pct_max"]              # 3250
    twenty_thresh = qdcg["20_pct_threshold"]   # 15900

    preferential_income = qual_div + lt_net_gain
    ordinary_income = max(0.0, taxable_income - preferential_income)

    # Ordinary income tax (trust brackets)
    if ordinary_income <= b10:
        ordinary_tax = ordinary_income * 0.10
    elif ordinary_income <= b24:
        ordinary_tax = b10 * 0.10 + (ordinary_income - b10) * 0.24
    elif ordinary_income <= b35:
        ordinary_tax = b10 * 0.10 + (b24 - b10) * 0.24 + (ordinary_income - b24) * 0.35
    else:
        ordinary_tax = b10 * 0.10 + (b24 - b10) * 0.24 + (b35 - b24) * 0.35 + (ordinary_income - b35) * 0.37

    # Capital gains / qualified dividends tax — ordinary income fills lower brackets first
    zero_bucket = max(0.0, min(zero_max, taxable_income) - ordinary_income)
    fifteen_bucket = max(0.0, min(twenty_thresh, taxable_income) - ordinary_income - zero_bucket)
    twenty_bucket = max(0.0, preferential_income - zero_bucket - fifteen_bucket)

    cap_gains_tax = zero_bucket * 0.00 + fifteen_bucket * 0.15 + twenty_bucket * 0.20

    tax_on_taxable_income = round(ordinary_tax + cap_gains_tax, 2)

    return {
        "preferential_income": round(preferential_income, 2),
        "ordinary_income": round(ordinary_income, 2),
        "ordinary_tax": round(ordinary_tax, 2),
        "zero_bucket": round(zero_bucket, 2),
        "fifteen_bucket": round(fifteen_bucket, 2),
        "twenty_bucket": round(twenty_bucket, 2),
        "cap_gains_tax": round(cap_gains_tax, 2),
        "tax_on_taxable_income": tax_on_taxable_income,
        "total_tax": tax_on_taxable_income,  # Line 9 — no other additions for this trust
    }


def compute_schedule_d_part5(taxable_income, qual_div, lt_net, net_combined, cfg):
    """Compute Schedule D Part V: Tax Computation Using Maximum Capital Gains Rates.

    Complete when both line 18a and line 19, column (2), are gains and neither
    line 18b nor 18c exceeds zero. Result (line 45) must equal Schedule G line 1a.
    All bracket thresholds come from cfg.
    """
    brackets = cfg["ordinary_income_brackets"]
    qdcg = cfg["qdcg_worksheet"]
    b10 = brackets["10_pct_max"]
    b24 = brackets["24_pct_max"]
    b35 = brackets["35_pct_max"]
    zero_max = qdcg["0_pct_max"]
    twenty_thresh = qdcg["20_pct_threshold"]

    def _tax(income):
        if income <= 0:
            return 0.0
        elif income <= b10:
            return income * 0.10
        elif income <= b24:
            return b10 * 0.10 + (income - b10) * 0.24
        elif income <= b35:
            return b10 * 0.10 + (b24 - b10) * 0.24 + (income - b24) * 0.35
        else:
            return b10 * 0.10 + (b24 - b10) * 0.24 + (b35 - b24) * 0.35 + (income - b35) * 0.37

    l21 = taxable_income
    l22 = min(lt_net, net_combined)          # smaller of 18a col(2) or 19 col(2)
    l23 = qual_div                            # Form 1041 line 2b(2)
    l24 = l22 + l23
    l25 = 0.0                                 # Form 4952 line 4g — not applicable
    l26 = max(0.0, l24 - l25)
    l27 = max(0.0, l21 - l26)               # ordinary income
    l28 = min(l21, zero_max)
    l29 = min(l27, l28)
    l30 = max(0.0, l28 - l29)               # amount taxed at 0%
    l31 = min(l21, l26)
    l32 = l26 - l30
    l33 = min(l21, twenty_thresh)
    l34 = l27 + l30
    l35 = max(0.0, l33 - l34)
    l36 = min(l32, l35)                      # amount taxed at 15%
    l37 = round(l36 * 0.15, 2)
    l38 = l31
    l39 = l30 + l36
    l40 = max(0.0, l38 - l39)               # amount taxed at 20%
    l41 = round(l40 * 0.20, 2)
    l42 = round(_tax(l27), 2)               # ordinary income tax
    l43 = round(l37 + l41 + l42, 2)
    l44 = round(_tax(l21), 2)               # tax if all taxable income were ordinary
    l45 = round(min(l43, l44), 2)

    return {
        "line21": round(l21, 2), "line22": round(l22, 2), "line23": round(l23, 2),
        "line24": round(l24, 2), "line25": round(l25, 2), "line26": round(l26, 2),
        "line27": round(l27, 2), "line28": round(l28, 2), "line29": round(l29, 2),
        "line30": round(l30, 2), "line31": round(l31, 2), "line32": round(l32, 2),
        "line33": round(l33, 2), "line34": round(l34, 2), "line35": round(l35, 2),
        "line36": round(l36, 2), "line37": l37,            "line38": round(l38, 2),
        "line39": round(l39, 2), "line40": round(l40, 2), "line41": l41,
        "line42": l42,           "line43": l43,            "line44": l44,
        "line45": l45,
    }


def compute_form_8960(csv_data, page1, sched_d, cfg):
    """Compute Form 8960 Net Investment Income Tax (NIIT).

    For trusts: AGI basis is undistributed net income = taxable_income.
    NIIT = 3.8% of lesser of (total NII, taxable_income - threshold).
    """
    niit_cfg = cfg["niit"]
    threshold = niit_cfg["threshold"]   # 15650
    rate = niit_cfg["rate"]             # 0.038

    interest = csv_data["int_box1"]
    ordinary_dividends = csv_data["div_1a"]
    net_gain = sched_d["net_combined"]
    total_nii = round(interest + ordinary_dividends + net_gain, 2)

    agi_undistributed_nii = page1["taxable_income"]
    agi_minus_threshold = round(max(0.0, agi_undistributed_nii - threshold), 2)
    lesser_of_nii_or_agi_excess = round(min(total_nii, agi_minus_threshold), 2)
    niit_amount = round(lesser_of_nii_or_agi_excess * rate, 2)

    return {
        "interest_income": interest,
        "ordinary_dividends": ordinary_dividends,
        "net_gain_from_dispositions": net_gain,
        "total_nii": total_nii,
        "agi_undistributed_nii": agi_undistributed_nii,
        "niit_threshold": float(threshold),
        "agi_minus_threshold": agi_minus_threshold,
        "lesser_of_nii_or_agi_excess": lesser_of_nii_or_agi_excess,
        "niit_amount": niit_amount,
    }


def validate(csv_data, computed, tolerance=1.00):
    """Compare computed income totals against CSV raw values.

    Returns list of mismatch strings (empty = passed).
    tolerance: flag if abs(diff) >= tolerance (default $1.00).
    """
    checks = [
        ("ordinary_dividends", csv_data["div_1a"],  computed["div_1a"]),
        ("qualified_dividends", csv_data["div_1b"],  computed["div_1b"]),
        ("interest_income",     csv_data["int_box1"], computed["int_box1"]),
        ("net_short_term_gain", csv_data.get("st_gain", 0.0), computed["st_gain"]),
        ("net_long_term_gain",  csv_data.get("lt_gain", 0.0), computed["lt_gain"]),
    ]
    mismatches = []
    for name, expected, actual in checks:
        diff = abs(expected - actual)
        if diff >= tolerance:
            mismatches.append(
                f"  {name}: expected {expected:.2f}, got {actual:.2f}, diff {diff:.2f}"
            )
    return mismatches


def build_field_maps(computed, fields, cfg=None):
    """Map semantic computed values to AcroForm field IDs.

    Returns dict keyed by form name:
      form_1041, schedule_d, form_8960, form_8949

    Skips fields where field_id is None (null placeholders).
    For form_1041: merges page1, schedule_b, and schedule_g (all in f1041.pdf).
    cfg is optional; when provided it drives entity_type and other_information checkboxes.
    """

    def resolve(section_dict, semantic_name):
        """Look up a field entry; return field_id string or None."""
        entry = section_dict.get(semantic_name)
        if entry is None:
            return None
        if isinstance(entry, dict):
            return entry.get("field_id")
        return entry  # plain string field_id

    page1_fields = fields.get("form_1041_page1", {})
    sched_b_fields = fields.get("schedule_b", {})
    sched_g_fields = fields.get("schedule_g", {})
    sched_d_fields = fields.get("schedule_d", {})
    f8960_fields = fields.get("form_8960", {})
    f8949_fields = fields.get("form_8949", {})

    # ---- Form 1041 (f1041.pdf) — page1 + schedule_b + schedule_g ----
    form_1041_map = {}

    # Page 1 income fields
    p1_mappings = {
        "interest_income":             computed.get("interest_income"),
        "ordinary_dividends":          computed.get("ordinary_dividends"),
        "qualified_dividends_estate_or_trust": computed.get("qualified_dividends"),
        "capital_gain_loss":           computed.get("capital_gain_loss"),
        "total_income":                computed.get("total_income"),
        "exemption":                   computed.get("exemption"),
        "taxable_income":              computed.get("taxable_income"),
        "total_tax_from_schedule_g":   computed.get("total_tax"),
        "tax_due":                     computed.get("total_tax"),
    }
    for sem, val in p1_mappings.items():
        fid = resolve(page1_fields, sem)
        if fid and val is not None:
            form_1041_map[fid] = f"{val:.2f}"

    # Line 17: adjusted total income (= total income; no above-line deductions for this trust)
    fid = resolve(page1_fields, "adjusted_total_income")
    if fid:
        form_1041_map[fid] = f"{computed.get('total_income', 0.0):.2f}"

    # Line 22: total of Lines 18-21 (IDD + estate_tax_deduction + QBI + exemption)
    fid = resolve(page1_fields, "deductions_total_lines18_21")
    if fid:
        deductions_18_21 = round(
            computed.get("income_distribution_deduction", 0.0) + computed.get("exemption", 0.0), 2
        )
        form_1041_map[fid] = f"{deductions_18_21:.2f}"

    # Entity type checkbox (Page 1, Line A)
    if cfg:
        entity_type = cfg.get("entity_type", "")
        if entity_type:
            entry = page1_fields.get(f"entity_type_{entity_type}")
            if isinstance(entry, dict):
                fid = entry.get("field_id")
                if fid:
                    form_1041_map[fid] = "Yes"

    # Header fields (name, EIN, address, dates) from cfg
    if cfg:
        trust = cfg.get("trust", {})
        year = cfg.get("tax_year", 2025)
        year_2digit = str(year)[-2:]
        header_mappings = {
            "trust_name":            trust.get("name"),
            "ein":                   trust.get("ein"),
            "fiduciary_name_title":  trust.get("fiduciary_name_title"),
            "address_street":        trust.get("address_street"),
            "address_city":          trust.get("address_city"),
            "address_state":         trust.get("address_state"),
            "address_zip":           trust.get("address_zip"),
            "date_entity_created":   trust.get("date_entity_created"),
            "num_schedules_k1":      trust.get("num_schedules_k1"),
            "tax_year_end_year":     year_2digit,
        }
        for sem, val in header_mappings.items():
            fid = resolve(page1_fields, sem)
            if fid and val is not None:
                form_1041_map[fid] = str(val)

    # Schedule B fields (embedded in f1041.pdf Page 2)
    sched_b_mappings = {
        "adjusted_total_income":                computed.get("sched_b_adjusted_total_income"),
        "accounting_income":                    computed.get("sched_b_accounting_income"),
        "income_required_to_be_distributed":    computed.get("income_required_to_be_distributed"),
        "other_amounts_distributed":            computed.get("other_amounts_distributed"),
        "total_distributions":                  computed.get("total_distributions"),
        "distributable_net_income":             computed.get("distributable_net_income"),
        "income_distribution_deduction":        computed.get("income_distribution_deduction"),
    }
    for sem, val in sched_b_mappings.items():
        fid = resolve(sched_b_fields, sem)
        if fid and val is not None:
            form_1041_map[fid] = f"{val:.2f}"

    # Schedule G fields (embedded in f1041.pdf Pages 2-3)
    sched_g_mappings = {
        "tax_on_taxable_income": computed.get("tax_on_taxable_income"),  # Line 1a
        "total_tax_lines1a_1d":  computed.get("tax_on_taxable_income"),  # Line 1e (= 1a; no 1b-1d)
        "tax_after_credits":     computed.get("tax_on_taxable_income"),  # Line 3 (= 1e; no credits)
        "niit_form_8960_line21": computed.get("niit_amount"),            # Line 5
        "total_tax":             computed.get("total_tax"),              # Line 9
    }
    for sem, val in sched_g_mappings.items():
        fid = resolve(sched_g_fields, sem)
        if fid and val is not None:
            form_1041_map[fid] = f"{val:.2f}"

    # Other Information checkboxes (Page 3)
    if cfg:
        oi_answers = cfg.get("other_information", {})
        oi_fields = fields.get("other_information", {})

        yes_no_qs = [
            "q1_tax_exempt_income",
            "q2_contract_assignment",
            "q3_foreign_account",
            "q4_foreign_trust",
            "q5_qualified_residence_interest",
            "q9_beneficiaries_skip_persons",
            "q10_form8938_required",
            "q11a_965i_distribution",
            "q11b_beneficiary_agreement",
            "q12_965i_transfer",
            "q13_digital_assets",
        ]
        for q in yes_no_qs:
            answer = oi_answers.get(q, "")
            if answer in ("Yes", "No"):
                key = f"{q}_yes" if answer == "Yes" else f"{q}_no"
                entry = oi_fields.get(key)
                if isinstance(entry, dict):
                    fid = entry.get("field_id")
                    if fid:
                        form_1041_map[fid] = "Yes"  # fill_pdf.py translates "Yes" → on_state

        single_qs = ["q6_sec663b_election", "q7_sec643e3_election", "q8_estate_open_2years"]
        for q in single_qs:
            if oi_answers.get(q, False):
                entry = oi_fields.get(q)
                if isinstance(entry, dict):
                    fid = entry.get("field_id")
                    if fid:
                        form_1041_map[fid] = "Yes"

    # ---- Schedule D (f1041sd.pdf) ----
    schedule_d_map = {}
    sd_mappings = {
        # Part I — Line 1b: totals from Form 8949 Box A (short-term covered)
        "part1_line1b_proceeds":            computed.get("st_proceeds"),
        "part1_line1b_cost":                computed.get("st_cost"),
        "part1_line1b_wash_sale":           computed.get("st_wash_sale"),
        "part1_line1b_gain_loss":           computed.get("st_net"),
        "net_short_term_gain_loss":         computed.get("st_net"),      # Line 7
        # Part II — Line 8b: totals from Form 8949 Box D (long-term covered)
        "part2_line8b_proceeds":            computed.get("lt_proceeds"),
        "part2_line8b_cost":                computed.get("lt_cost"),
        "part2_line8b_wash_sale":           computed.get("lt_wash_sale"),
        "part2_line8b_gain_loss":           computed.get("lt_net"),
        "part2_line15_net_lt_capital_gain": computed.get("lt_net"),      # Line 16
        # Part III — accumulation trust: no beneficiary distributions, col2=col3=total
        "part3_line17_col2":                computed.get("st_net"),
        "part3_line17_col3":                computed.get("st_net"),
        "part3_line18a_col2":               computed.get("lt_net"),
        "part3_line18a_col3":               computed.get("lt_net"),
        "part3_line19_col2":                computed.get("net_combined"),
        "net_capital_gain":                 computed.get("net_combined"),  # Line 19 col3
    }
    for sem, val in sd_mappings.items():
        fid = resolve(sched_d_fields, sem)
        if fid and val is not None:
            schedule_d_map[fid] = f"{val:.2f}"

    # Header: name and EIN
    if cfg:
        trust = cfg.get("trust", {})
        for sem, val in [("trust_name", trust.get("name")), ("ein", trust.get("ein"))]:
            fid = resolve(sched_d_fields, sem)
            if fid and val is not None:
                schedule_d_map[fid] = str(val)

    # Part V: Tax Computation Using Maximum Capital Gains Rates
    part5 = computed.get("part5", {})
    if part5:
        for line_num in range(21, 46):
            sem = f"part5_line{line_num}"
            val = part5.get(f"line{line_num}")
            fid = resolve(sched_d_fields, sem)
            if fid and val is not None:
                schedule_d_map[fid] = f"{val:.2f}"

    # QOF question: always No for this accumulation trust
    qof_no_entry = sched_d_fields.get("qof_disposed_no")
    if isinstance(qof_no_entry, dict):
        fid = qof_no_entry.get("field_id")
        on_state = qof_no_entry.get("on_state", "/2")
        if fid:
            schedule_d_map[fid] = on_state

    # ---- Form 8960 (f8960.pdf) ----
    form_8960_map = {}

    # Header: name and EIN
    if cfg:
        trust = cfg.get("trust", {})
        for sem, val in [("name", trust.get("name")), ("ein", trust.get("ein"))]:
            fid = resolve(f8960_fields, sem)
            if fid and val is not None:
                form_8960_map[fid] = str(val)

    f8960_mappings = {
        # Part I — investment income items
        "interest_income":               computed.get("f8960_interest"),        # Line 1
        "ordinary_dividends":            computed.get("f8960_dividends"),       # Line 2
        "net_gain_loss_from_dispositions": computed.get("net_gain_from_dispositions"),  # Line 5a
        "net_gain_5d":                   computed.get("net_gain_from_dispositions"),    # Line 5d (=5a; 5b=5c=0)
        "total_net_investment_income":   computed.get("total_nii"),             # Line 8
        # Part III — trust (estate/trust section; individual lines 13-17 left blank)
        "line12_net_investment_income":  computed.get("total_nii"),             # Line 12 (=Line 8; no deductions)
        "trust_line18a_nii":             computed.get("total_nii"),             # Line 18a (undistributed NII)
        "trust_line18c_undist_nii":      computed.get("total_nii"),             # Line 18c (=18a; no distributions)
        "agi_undistributed_net_income":  computed.get("agi_undistributed_nii"), # Line 19a (trust AGI)
        "niit_threshold":                computed.get("niit_threshold"),        # Line 19b (threshold)
        "agi_minus_threshold":           computed.get("agi_minus_threshold"),   # Line 19c (AGI - threshold)
        "lesser_of_nii_or_agi_excess":   computed.get("lesser_of_nii_or_agi_excess"),  # Line 20
        "niit_amount":                   computed.get("niit_amount"),           # Line 21
    }
    for sem, val in f8960_mappings.items():
        fid = resolve(f8960_fields, sem)
        if fid and val is not None:
            form_8960_map[fid] = f"{val:.2f}"

    # ---- Form 8949 (f8949.pdf) ----
    form_8949_map = {}

    # Header: name and EIN on both pages
    if cfg:
        trust = cfg.get("trust", {})
        name = trust.get("name")
        ein = trust.get("ein")
        for sem, val in [("p1_name", name), ("p1_ssn", ein), ("p2_name", name), ("p2_ssn", ein)]:
            fid = resolve(f8949_fields, sem)
            if fid and val is not None:
                form_8949_map[fid] = str(val)

    # Short-term transaction (Box A) — fills Page 1 Row 1
    st_rows = [r for r in computed.get("rows", []) if r["form8949_code"] == "A"]
    lt_rows = [r for r in computed.get("rows", []) if r["form8949_code"] == "D"]

    # Check Box A (short-term covered) and Box D (long-term covered)
    if st_rows:
        entry = f8949_fields.get("box_a_short_term_covered")
        if isinstance(entry, dict):
            fid = entry.get("field_id")
            if fid:
                form_8949_map[fid] = "Yes"
    if lt_rows:
        entry = f8949_fields.get("box_d_long_term_covered")
        if isinstance(entry, dict):
            fid = entry.get("field_id")
            if fid:
                form_8949_map[fid] = "Yes"

    for i, txn in enumerate(st_rows[:11], start=1):
        prefix = f"p1_row{i}"
        row_map = {
            f"{prefix}_description":  (txn["description"], str),
            f"{prefix}_date_acquired": (txn["date_acquired"], str),
            f"{prefix}_date_sold":     (txn["date_sold"], str),
            f"{prefix}_proceeds":      (txn["proceeds"], lambda v: f"{v:.2f}"),
            f"{prefix}_cost":          (txn["cost"], lambda v: f"{v:.2f}"),
            # cols (f) and (g) intentionally left blank — no adjustments
            f"{prefix}_gain_loss":     (txn["gain_loss"], lambda v: f"{v:.2f}"),
        }
        for sem, (val, fmt) in row_map.items():
            fid = resolve(f8949_fields, sem)
            if fid:
                form_8949_map[fid] = fmt(val)

    for i, txn in enumerate(lt_rows[:11], start=1):
        prefix = f"p2_row{i}"
        row_map = {
            f"{prefix}_description":  (txn["description"], str),
            f"{prefix}_date_acquired": (txn["date_acquired"], str),
            f"{prefix}_date_sold":     (txn["date_sold"], str),
            f"{prefix}_proceeds":      (txn["proceeds"], lambda v: f"{v:.2f}"),
            f"{prefix}_cost":          (txn["cost"], lambda v: f"{v:.2f}"),
            # cols (f) and (g) intentionally left blank — no adjustments
            f"{prefix}_gain_loss":     (txn["gain_loss"], lambda v: f"{v:.2f}"),
        }
        for sem, (val, fmt) in row_map.items():
            fid = resolve(f8949_fields, sem)
            if fid:
                form_8949_map[fid] = fmt(val)

    # Page totals for Form 8949
    if st_rows:
        fid = resolve(f8949_fields, "p1_total_proceeds")
        if fid:
            form_8949_map[fid] = f"{computed.get('st_proceeds', 0.0):.2f}"
        fid = resolve(f8949_fields, "p1_total_cost")
        if fid:
            form_8949_map[fid] = f"{computed.get('st_cost', 0.0):.2f}"
        # col (g) totals intentionally left blank — no adjustments
        fid = resolve(f8949_fields, "p1_total_gain_loss")
        if fid:
            form_8949_map[fid] = f"{computed.get('st_net', 0.0):.2f}"

    if lt_rows:
        fid = resolve(f8949_fields, "p2_total_proceeds")
        if fid:
            form_8949_map[fid] = f"{computed.get('lt_proceeds', 0.0):.2f}"
        fid = resolve(f8949_fields, "p2_total_cost")
        if fid:
            form_8949_map[fid] = f"{computed.get('lt_cost', 0.0):.2f}"
        # col (g) totals intentionally left blank — no adjustments
        fid = resolve(f8949_fields, "p2_total_gain_loss")
        if fid:
            form_8949_map[fid] = f"{computed.get('lt_net', 0.0):.2f}"

    return {
        "form_1041": form_1041_map,
        "schedule_d": schedule_d_map,
        "form_8960": form_8960_map,
        "form_8949": form_8949_map,
    }


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


def print_summary(page1, sched_g, form_8960, output_paths):
    """Print final summary block after live PDF writing (used in Plan 03)."""
    print()
    print("=== Summary ===")
    print(f"Gross income:   ${page1['total_income']:,.2f}")
    print(f"Taxable income: ${page1['taxable_income']:,.2f}")
    print(f"Schedule G tax: ${sched_g['tax_on_taxable_income']:,.2f}")
    print(f"NIIT:           ${form_8960['niit_amount']:,.2f}")
    total_tax = sched_g["tax_on_taxable_income"] + form_8960["niit_amount"]
    print(f"Total tax:      ${total_tax:,.2f}")
    print("Output files:")
    for path in output_paths:
        print(f"  {path}")


# ---------------------------------------------------------------------------
# PDF fill helper
# ---------------------------------------------------------------------------

def fill_form(field_values, form_path, output_path):
    """Write field_values to a temp JSON file and call fill_pdf.py via subprocess.

    Args:
        field_values: dict of {field_id: value} pairs
        form_path: path to the blank PDF form (str or Path)
        output_path: path for the filled output PDF (str or Path)

    Raises:
        RuntimeError: if fill_pdf.py exits non-zero, including stderr text
    """
    # Use sys.executable so subprocess inherits the same Python interpreter
    # (the hardcoded Unix-style path /c/ProgramData/miniconda3/python does not
    # work with Windows subprocess.run even though it is valid in bash).
    python_exe = sys.executable
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(field_values, f)
            tmp = f.name

        result = subprocess.run(
            [python_exe, "fill_pdf.py", "--fields", tmp, "--form", str(form_path), "--output", str(output_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"fill_pdf.py failed (exit {result.returncode}): {result.stderr.strip()}"
            )
        print(f"PDF written: {output_path}")
    finally:
        if tmp:
            try:
                Path(tmp).unlink()
            except OSError:
                pass


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
    csv_data = parse_csv(args.csv)
    print("Parsed CSV")

    # 6. Computation chain
    sched_d = compute_schedule_d(csv_data["transactions"])
    print("Computed Schedule D")

    page1 = compute_form_1041_page1(csv_data, sched_d, cfg)
    sched_b = compute_schedule_b(page1)

    sched_g = compute_schedule_g(
        page1["taxable_income"],
        csv_data["div_1b"],
        sched_d["lt_net"],
        cfg,
    )
    print("Computed Schedule G")

    sched_d_part5 = compute_schedule_d_part5(
        page1["taxable_income"],
        csv_data["div_1b"],
        sched_d["lt_net"],
        sched_d["net_combined"],
        cfg,
    )
    print("Computed Schedule D Part V")

    form_8960 = compute_form_8960(csv_data, page1, sched_d, cfg)
    print("Computed Form 8960")

    # 7. Validation — re-sum gains from raw CSV transactions for cross-check
    raw_st_gain = sum(
        (t["proceeds"] - t["cost"] - t["wash_sale"])
        for t in csv_data["transactions"] if t["form8949_code"] == "A"
    )
    raw_lt_gain = sum(
        (t["proceeds"] - t["cost"] - t["wash_sale"])
        for t in csv_data["transactions"] if t["form8949_code"] == "D"
    )
    # Build an augmented csv_data-like dict for validate() that includes gain values
    csv_with_gains = dict(csv_data)
    csv_with_gains["st_gain"] = raw_st_gain
    csv_with_gains["lt_gain"] = raw_lt_gain

    mismatches = validate(csv_with_gains, {
        "div_1a": page1["ordinary_dividends"],
        "div_1b": page1["qualified_dividends"],
        "int_box1": page1["interest_income"],
        "st_gain": sched_d["st_net"],
        "lt_gain": sched_d["lt_net"],
    })
    if mismatches:
        print("VALIDATION FAILED:")
        for m in mismatches:
            print(m)
        print("\nField values as computed (implicit dry-run):")
        # fall through to print field values even on mismatch
        # then prompt user for "yes" to proceed or halt
        answer = input("Proceed despite mismatch? (yes/no): ").strip().lower()
        if answer != "yes":
            sys.exit(1)
    else:
        print("Validation passed")

    # 8. Build merged computed dict and field maps (needed by both dry-run and live mode)
    computed = {**csv_data, **page1}
    computed.update({
        "sched_b_adjusted_total_income": sched_b["adjusted_total_income"],
        "sched_b_accounting_income": sched_b["accounting_income"],
        "income_required_to_be_distributed": sched_b["income_required_to_be_distributed"],
        "other_amounts_distributed": sched_b["other_amounts_distributed"],
        "total_distributions": sched_b["total_distributions"],
        "distributable_net_income": sched_b["distributable_net_income"],
        "income_distribution_deduction": sched_b["income_distribution_deduction"],
    })
    computed.update(sched_g)
    computed.update({
        "f8960_interest": form_8960["interest_income"],
        "f8960_dividends": form_8960["ordinary_dividends"],
        "net_gain_from_dispositions": form_8960["net_gain_from_dispositions"],
        "total_nii": form_8960["total_nii"],
        "agi_undistributed_nii": form_8960["agi_undistributed_nii"],
        "niit_threshold": form_8960["niit_threshold"],
        "agi_minus_threshold": form_8960["agi_minus_threshold"],
        "lesser_of_nii_or_agi_excess": form_8960["lesser_of_nii_or_agi_excess"],
        "niit_amount": form_8960["niit_amount"],
        "total_tax": sched_g["tax_on_taxable_income"] + form_8960["niit_amount"],
    })
    computed.update({
        "st_proceeds": sched_d["st_proceeds"],
        "st_cost": sched_d["st_cost"],
        "st_wash_sale": sched_d["st_wash_sale"],
        "st_net": sched_d["st_net"],
        "lt_proceeds": sched_d["lt_proceeds"],
        "lt_cost": sched_d["lt_cost"],
        "lt_wash_sale": sched_d["lt_wash_sale"],
        "lt_net": sched_d["lt_net"],
        "net_combined": sched_d["net_combined"],
        "rows": sched_d["rows"],
        "part5": sched_d_part5,
    })
    field_maps = build_field_maps(computed, fields, cfg)

    # 9. Output paths and form PDFs
    year = args.year
    output_dir = Path(args.output_dir)
    entity_name = cfg.get("trust", {}).get("name", "Trust")
    output_paths = {
        "form_1041":   output_dir / f"{year} 1041 {entity_name}.pdf",
        "schedule_d":  output_dir / f"{year} Schedule D {entity_name}.pdf",
        "form_8960":   output_dir / f"{year} 8960 {entity_name}.pdf",
        "form_8949":   output_dir / f"{year} 8949 {entity_name}.pdf",
    }
    form_pdfs = {
        "form_1041":  cfg["paths"]["blank_form"],   # forms/f1041.pdf
        "schedule_d": "forms/f1041sd.pdf",
        "form_8960":  "forms/f8960.pdf",
        "form_8949":  "forms/f8949.pdf",
    }

    # 10. Dry-run: print full computation steps + field-value mapping then exit
    if args.dry_run:
        _print_dry_run(csv_data, sched_d, page1, sched_b, sched_g, form_8960, fields, cfg)
        sys.exit(0)

    # 11. Live mode: write filled PDFs
    for form_key in ["form_1041", "schedule_d", "form_8960", "form_8949"]:
        fmap = field_maps[form_key]
        if not fmap:
            print(f"WARNING: No AcroForm fields for {form_key} -- skipping PDF output")
            continue
        fill_form(fmap, form_pdfs[form_key], output_paths[form_key])

    # 12. Print summary
    print_summary(page1, sched_g, form_8960, [str(p) for p in output_paths.values()])


def _print_dry_run(csv_data, sched_d, page1, sched_b, sched_g, form_8960, fields, cfg=None):
    """Print full dry-run output: computation steps + field-value mapping."""

    total_tax = sched_g["tax_on_taxable_income"] + form_8960["niit_amount"]

    print()
    print("=== Computation Steps ===")

    # 1099-DIV
    print("1099-DIV:")
    print(f"  Ordinary dividends (Box 1a):      ${csv_data['div_1a']:,.2f}")
    print(f"  Qualified dividends (Box 1b):     ${csv_data['div_1b']:,.2f}")

    # 1099-INT
    print("1099-INT:")
    print(f"  Interest income (Box 1):          ${csv_data['int_box1']:,.2f}")

    # 1099-B transactions
    txns = csv_data["transactions"]
    lt_txns = [t for t in txns if t["form8949_code"] == "D"]
    st_txns = [t for t in txns if t["form8949_code"] == "A"]
    print(f"1099-B ({len(txns)} transactions):")
    for txn in lt_txns:
        adj_cost = txn["cost"] + txn["wash_sale"]
        gain = txn["proceeds"] - adj_cost
        print(
            f"  [Box D - Long term]   {txn['date_acquired']} -> {txn['date_sold']}"
            f"   proceeds=${txn['proceeds']:,.2f}   cost=${txn['cost']:,.2f}"
            f"   gain=${gain:,.2f}"
        )
    for txn in st_txns:
        adj_cost = txn["cost"] + txn["wash_sale"]
        gain = txn["proceeds"] - adj_cost
        print(
            f"  [Box A - Short term]  {txn['date_acquired']} -> {txn['date_sold']}"
            f"   proceeds=${txn['proceeds']:,.2f}   cost=${txn['cost']:,.2f}"
            f"   gain=${gain:,.2f}"
        )

    # Schedule D
    print()
    print("Schedule D:")
    print(f"  Net short-term capital gain (Part I Line 7):   ${sched_d['st_net']:,.2f}")
    print(f"  Net long-term capital gain (Part II Line 15):  ${sched_d['lt_net']:,.2f}")
    print(f"  Net capital gain (Part III Line 19):           ${sched_d['net_combined']:,.2f}")

    # Form 1041 Page 1
    print()
    print("Form 1041 Page 1:")
    print(f"  Interest income (Line 1):         ${page1['interest_income']:,.2f}")
    print(f"  Ordinary dividends (Line 2):      ${page1['ordinary_dividends']:,.2f}")
    print(f"  Capital gain/loss (Line 4):       ${page1['capital_gain_loss']:,.2f}")
    print(f"  Total income (Line 9):            ${page1['total_income']:,.2f}")
    print(f"  Exemption (Line 20):              ${page1['exemption']:,.2f}")
    print(f"  Taxable income (Line 22):         ${page1['taxable_income']:,.2f}")

    # Schedule G
    print()
    print("Schedule G (QD&CG Worksheet):")
    print(f"  Preferential income:              ${sched_g['preferential_income']:,.2f}")
    print(f"  Ordinary income:                  ${sched_g['ordinary_income']:,.2f}")
    print(f"  Ordinary income tax:              ${sched_g['ordinary_tax']:,.2f}")
    print(f"  Cap gains (0% bucket):            ${sched_g['zero_bucket']:,.2f} x 0%   = $0.00")
    fifteen_tax = sched_g["fifteen_bucket"] * 0.15
    twenty_tax = sched_g["twenty_bucket"] * 0.20
    print(f"  Cap gains (15% bucket):           ${sched_g['fifteen_bucket']:,.2f} x 15% = ${fifteen_tax:,.2f}")
    print(f"  Cap gains (20% bucket):           ${sched_g['twenty_bucket']:,.2f} x 20% = ${twenty_tax:,.2f}")
    print(f"  Schedule G Line 1a tax:           ${sched_g['tax_on_taxable_income']:,.2f}")

    # Form 8960 (NIIT)
    print()
    print("Form 8960 (NIIT):")
    print(f"  Total NII (Line 8):               ${form_8960['total_nii']:,.2f}")
    print(f"  AGI / undistrib. NII (Line 9b):   ${form_8960['agi_undistributed_nii']:,.2f}")
    print(f"  NIIT threshold (Line 9c):         ${form_8960['niit_threshold']:,.2f}")
    print(f"  AGI minus threshold (Line 9d):    ${form_8960['agi_minus_threshold']:,.2f}")
    print(f"  NIIT base - lesser (Line 10):     ${form_8960['lesser_of_nii_or_agi_excess']:,.2f}")
    print(f"  NIIT (Line 21 = 3.8%):            ${form_8960['niit_amount']:,.2f}")

    # Summary
    print()
    print("Summary:")
    print(f"  Gross income:                     ${page1['total_income']:,.2f}")
    print(f"  Taxable income:                   ${page1['taxable_income']:,.2f}")
    print(f"  Schedule G tax:                   ${sched_g['tax_on_taxable_income']:,.2f}")
    print(f"  NIIT (Form 8960 Line 21):         ${form_8960['niit_amount']:,.2f}")
    print(f"  Total tax:                        ${total_tax:,.2f}")

    # Build merged computed dict for field mapping
    computed = {}
    computed.update(page1)
    computed.update({
        "sched_b_adjusted_total_income": sched_b["adjusted_total_income"],
        "sched_b_accounting_income": sched_b["accounting_income"],
        "income_required_to_be_distributed": sched_b["income_required_to_be_distributed"],
        "other_amounts_distributed": sched_b["other_amounts_distributed"],
        "total_distributions": sched_b["total_distributions"],
        "distributable_net_income": sched_b["distributable_net_income"],
        "income_distribution_deduction": sched_b["income_distribution_deduction"],
    })
    computed.update(sched_g)
    computed.update({
        "f8960_interest": form_8960["interest_income"],
        "f8960_dividends": form_8960["ordinary_dividends"],
        "net_gain_from_dispositions": form_8960["net_gain_from_dispositions"],
        "total_nii": form_8960["total_nii"],
        "agi_undistributed_nii": form_8960["agi_undistributed_nii"],
        "niit_threshold": form_8960["niit_threshold"],
        "agi_minus_threshold": form_8960["agi_minus_threshold"],
        "lesser_of_nii_or_agi_excess": form_8960["lesser_of_nii_or_agi_excess"],
        "niit_amount": form_8960["niit_amount"],
        "total_tax": total_tax,
    })
    # Schedule D fields for mapping
    computed.update({
        "st_proceeds": sched_d["st_proceeds"],
        "st_cost": sched_d["st_cost"],
        "st_wash_sale": sched_d["st_wash_sale"],
        "st_net": sched_d["st_net"],
        "lt_proceeds": sched_d["lt_proceeds"],
        "lt_cost": sched_d["lt_cost"],
        "lt_wash_sale": sched_d["lt_wash_sale"],
        "lt_net": sched_d["lt_net"],
        "net_combined": sched_d["net_combined"],
        "rows": sched_d["rows"],
    })

    field_maps = build_field_maps(computed, fields, cfg)

    print()
    print("=== Field-Value Mapping ===")

    print()
    print("[Form 1041 (f1041.pdf)]")
    if field_maps["form_1041"]:
        for fid, val in field_maps["form_1041"].items():
            print(f"  {fid}: {val}")
    else:
        print("  (no fields mapped)")

    print()
    print("[Schedule D (f1041sd.pdf)]")
    if field_maps["schedule_d"]:
        for fid, val in field_maps["schedule_d"].items():
            print(f"  {fid}: {val}")
    else:
        print("  (No AcroForm fields — XFA form, PDF fill skipped)")

    print()
    print("[Form 8960 (f8960.pdf)]")
    if field_maps["form_8960"]:
        for fid, val in field_maps["form_8960"].items():
            print(f"  {fid}: {val}")
    else:
        print("  (no fields mapped)")

    print()
    print("[Form 8949 (f8949.pdf)]")
    if field_maps["form_8949"]:
        for fid, val in field_maps["form_8949"].items():
            print(f"  {fid}: {val}")
    else:
        print("  (no fields mapped)")


if __name__ == "__main__":
    main()
