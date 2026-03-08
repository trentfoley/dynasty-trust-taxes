# Phase 2: Core Skill - Research

**Researched:** 2026-03-08
**Domain:** Claude skill implementation — CSV parsing, IRS tax computation (Schedule D, G, Form 8960), AcroForm PDF filling
**Confidence:** HIGH

## Summary

Phase 2 builds a single Claude slash command (`/fill-1041`) that reads the brokerage CSV, computes all required tax schedules, and produces filled print-ready PDFs. All infrastructure from Phase 1 is in place and verified: `fill_pdf.py` works, `config/2025.json` has all bracket values, and `config/2025_fields.json` has the complete semantic-to-AcroForm field mapping for Form 1041 (3 pages including Schedule B and Schedule G).

The brokerage CSV contains exactly 2 transactions in the 1099-B section (NOT 296 individual lots). The description "296.00 VANGUARD" means 296.00 shares sold as a single aggregated lot with "Various" acquisition dates, and "1.35 VANGUARD" is the short-term fractional lot. This is the complete set of 1099-B data. The CONTEXT.md reference to "296 transactions" reflects the share count, not individual transaction rows.

Schedule B (Form 1041) is embedded in `f1041.pdf` on Page 2 (fields f2_1 through f2_22) — it is NOT a separate PDF download. This resolves the "Claude's Discretion" question about Schedule B. Schedule D and Form 8960 ARE separate PDFs that need to be downloaded and their AcroForm fields cataloged. The skill also needs a blank Form 8949 PDF.

**Primary recommendation:** Implement the skill as a single Python script (`fill_1041.py`) invoked from a Claude slash command file (`.claude/commands/fill-1041.md`). The Python script handles all CSV parsing, computation, and fill_pdf.py orchestration. The slash command file provides the invocation interface with `--dry-run` support via a shell argument passed through.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Skill invocation**
- Skill command: `/fill-1041` with optional `--dry-run` flag and optional year argument
- Default file paths come from `config/YEAR.json`; all overridable via flags (SKILL-04)
- Brief header at start of every run showing: CSV input path, blank form path, output directory

**Output scope — filled PDFs**
- Fill ALL forms required to be attached with the Form 1041 filing for this trust, not just Form 1041 itself
- Known required forms: Form 1041 (page 1), Schedule D (Form 1041), Schedule G (Form 1041), Form 8960, Form 8949
- If other attachment forms are required (e.g., Schedule B per CALC-07), include those too
- Blank IRS forms for attachments (e.g., Form 8949) are downloaded from IRS.gov and stored in `forms/`
- Each filled form written to `output/` as a separate PDF (e.g., `output/2025_1041_filled.pdf`, `output/2025_8949_filled.pdf`)

**Mismatch validation (SKILL-03)**
- Validate computed totals against CSV source before writing any file
- Tolerance: round-to-dollar — flag if difference >= $1.00; allow <$1.00 rounding differences
- Validated totals: ordinary dividends (1099-DIV Box 1a), qualified dividends (Box 1b), interest (1099-INT Box 1), net short-term gain, net long-term gain
- On mismatch: halt, show expected vs computed diff, require explicit user confirmation ("yes") to proceed
- Even on halt, display what the field values would be (acts as implicit dry-run output)

**Execution feedback (normal mode)**
- Step-by-step progress lines as each stage completes:
  - `Parsed CSV` — after extracting all 1099 sections
  - `Computed Schedule D` — after netting gains/losses
  - `Computed Schedule G` — after QD&CG worksheet
  - `Computed Form 8960` — after NIIT calculation
  - `Validation passed` (or halt on mismatch)
  - `PDF written: output/2025_1041_filled.pdf` — per form
- Final summary after all PDFs written: gross income, taxable income, Schedule G tax, NIIT, total tax due, output file paths
- On failure: show which steps completed then the specific error for the failing step

**Dry-run output format (SKILL-02)**
- Invoked with `--dry-run` flag; no files written
- Output structure:
  1. Computation steps with intermediate values (gross income, taxable income, bracket lookups, etc.)
  2. Field-value mapping grouped by form section: [Form 1041 Page 1], [Schedule D], [Schedule G], [Form 8960], [Form 8949]
- Validation runs in dry-run too — same mismatch check before displaying output
- Useful as a pre-flight check before the real run

**Schedule D / Form 8949 detail**
- 2 1099-B transactions in the 2025 CSV (one long-term "various" lot of 296.00 shares, one short-term lot of 1.35 shares)
- NOTE: CONTEXT.md says "296 transactions" but the CSV/XML shows only 2 rows — "296.00" is the share count, not transaction count. Research confirmed this is a summary file.
- Internal computation: process each transaction individually for accuracy
- Dry-run display: one row per acquisition-date lot (group transactions with same acquisition date) showing: acquisition date, proceeds, cost basis, gain/loss, short/long-term flag
- Wash sale disallowed amounts: add back to cost basis per IRS Form 8949 Box 1g instructions
- Verify all transactions are "covered" (known basis); flag any uncovered transactions as a warning
- Form 8949 rows organized as CALC-01 specifies: Box A (short-term covered), Box D (long-term covered)

### Claude's Discretion
- Exact Schedule G QD&CG worksheet step-by-step implementation details
- How to download and store blank IRS forms for attachments (manual pre-step vs skill-automated)
- Schedule B (Form 1041) handling — RESOLVED by research: Schedule B is embedded in f1041.pdf (Page 2), not a separate download
- Whether to produce a single merged PDF or separate files per form — RESOLVED by locked decision: separate files per form

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PARSE-01 | Skill parses 1099-DIV section from brokerage CSV — extracts ordinary dividends (Box 1a) and qualified dividends (Box 1b) | CSV structure confirmed: section header "Form 1099DIV", then box rows with quoted fields. Values: Box 1a = $903.82 total, Box 1b = $903.82 qualified |
| PARSE-02 | Skill parses 1099-INT section from brokerage CSV — extracts interest income (Box 1) | CSV structure confirmed: section header "Form 1099INT", Box 1 = $0.12 |
| PARSE-03 | Skill parses 1099-B section from brokerage CSV — extracts each capital transaction row with: description, date acquired, date sold, proceeds, cost basis, wash sale loss disallowed, and short/long-term flag | CSV structure confirmed: section header "Form 1099 B", 23-column header row, then data rows. Exactly 2 transactions: long-term (Box D, "Various" acq date, 296.00 shares, proceeds=$226,514.41, basis=$122,404.65) and short-term (Box A, 1.35 shares, proceeds=$1,030.79, basis=$903.82) |
| CALC-01 | Skill computes Form 8949 rows — assigns Box A (short-term covered) or Box D (long-term covered) based on transaction flags and calculates gain/loss per transaction | Column 2 ("Short-Term gain loss Long-term gain or loss Ordinary") and Column 8 ("Form 8949 Code") identify the box. Both transactions are "Covered" (column 5 = "Covered"). Box A: ST gain = $126.97. Box D: LT gain = $104,109.76 |
| CALC-02 | Skill computes Schedule D — net short-term capital gain/loss (Part I) and net long-term capital gain/loss (Part II) from Form 8949 rows | Part I net ST = $126.97 (single Box A transaction). Part II net LT = $104,109.76 (single Box D transaction). Net combined = $104,236.73 |
| CALC-03 | Skill computes taxable income — gross income minus $100 complex trust exemption (Line 20) | Gross income = $903.82 + $0.12 + $104,109.76 + $126.97 = $105,140.67. Taxable = $105,040.67 |
| CALC-04 | Skill computes Schedule G tax using the Qualified Dividends and Capital Gains Tax Worksheet | QD&CG worksheet applies because trust has both qualified dividends ($903.82) and net LT capital gains ($104,109.76). Ordinary taxable income = $27.09 (taxable minus preferential income). Schedule G tax = ~$19,722.93. Full worksheet steps documented in Architecture Patterns section |
| CALC-05 | Skill computes Form 8960 NIIT — 3.8% of lesser of (net investment income, AGI minus $15,650 threshold) | NII = $105,140.67 (all income is investment income). AGI for trust = taxable income = $105,040.67. AGI excess = $89,390.67. NIIT base = $89,390.67. NIIT = $3,396.85 |
| CALC-07 | Schedule B is computed (zero distribution deduction) and included in output — required on complex trust returns even when $0 | Schedule B is on Page 2 of f1041.pdf (fields f2_1 through f2_22). Trust accumulates all income, so all distribution-related lines are $0. Adjusted total income flows from Page 1 Line 17 |
| PDF-02 | Skill fills all Form 1041 page 1 fields that were populated on the 2024 reference return | config/2025_fields.json has all page 1 fields: form_1041_page1 section with 60 text fields + 27 checkboxes. Fields to populate: trust_name, ein, entity_type_complex_trust, interest_income, ordinary_dividends, qualified_dividends_estate_or_trust, capital_gain_loss, total_income, exemption, deductions_total_lines18_21, taxable_income, total_tax_from_schedule_g, tax_due, sign_ein_fiduciary |
| PDF-03 | Skill fills Schedule D (Form 1041) fields — short-term and long-term transaction detail and summary lines | Schedule D is a separate PDF. Must download from IRS, enumerate fields with pypdf, add to config/2025_fields.json. Field IDs currently null (with _note) in the catalog |
| PDF-04 | Skill fills Schedule G fields — tax computation lines | Schedule G is embedded in f1041.pdf (Page 2/3). Fields already cataloged: tax_on_taxable_income (f2_23), niit_form_8960_line21 (f2_35), total_tax (f2_41). Only lines with values are filled |
| PDF-05 | Skill fills Form 8960 fields — net investment income and NIIT amount | Form 8960 is a separate PDF. Must download from IRS, enumerate fields, add to config. Catalog currently has null field IDs with semantic _notes |
| PDF-06 | Output PDF has NeedAppearances flag set — handled by fill_pdf.py | fill_pdf.py already handles this via auto_regenerate=True. No action required in skill |
| PDF-07 | Filled PDF written to output/YEAR_1041_filled.pdf | fill_pdf.py --output argument handles this. Skill passes the computed output path from config |
| SKILL-01 | Skill is invocable via a single Claude skill command `/fill-1041` with optional year argument | Claude slash commands live in .claude/commands/. Need to create .claude/commands/fill-1041.md |
| SKILL-02 | Skill supports dry-run mode — outputs all computed field values without calling fill_pdf.py | Python script checks --dry-run flag before calling subprocess for fill_pdf.py |
| SKILL-03 | Skill validates computed income totals against CSV source data and surfaces any mismatch | Comparison logic: re-sum raw CSV values vs computed values; tolerance $1.00 |
| SKILL-04 | All file paths use sensible defaults from config/YEAR.json and can be overridden | argparse with defaults loaded from config JSON |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python (miniconda3) | 3.13.5 | Primary skill implementation language | Already installed; fill_pdf.py already uses it; no new dependency needed |
| csv (stdlib) | stdlib | Parse brokerage CSV file | Built-in; handles the quoted-field CSV format exactly |
| json (stdlib) | stdlib | Load config/2025.json and config/2025_fields.json | Built-in; all config is JSON |
| argparse (stdlib) | stdlib | CLI flags: --dry-run, --year, path overrides | Built-in; established pattern in fill_pdf.py |
| subprocess (stdlib) | stdlib | Call fill_pdf.py for each form | Built-in; decoupled — skill doesn't import pypdf directly |
| pypdf | 6.7.5 | Needed for Phase 2 to enumerate field IDs from new form PDFs (Schedule D, Form 8960, Form 8949) | Already installed; same API as Phase 1 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| decimal (stdlib) | stdlib | Round-to-dollar mismatch validation | Use when comparing CSV raw values vs computed values to avoid float precision issues |
| sys (stdlib) | stdlib | Exit on validation failure, stderr output | Always |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Separate fill_1041.py called from slash command | Inline Python in slash command .md file | Inline Python is harder to test and maintain; separate script is the clean pattern |
| subprocess to call fill_pdf.py | Import pypdf directly in skill | Keeps the skill decoupled from pypdf internals; fill_pdf.py is the tested, maintained PDF artifact |

**Python executable:** `/c/ProgramData/miniconda3/python` (not `python3` — Windows Store stub on this machine)

---

## Architecture Patterns

### Recommended Project Structure
```
dynasty-trust-taxes/
├── .claude/
│   └── commands/
│       └── fill-1041.md          # Claude slash command definition
├── fill_1041.py                  # Core skill implementation (new)
├── fill_pdf.py                   # PDF filler (Phase 1 artifact, unchanged)
├── config/
│   ├── 2025.json                 # Tax brackets, trust metadata, paths
│   └── 2025_fields.json          # Semantic field catalog (updated to add Schedule D, 8960, 8949 IDs)
├── forms/
│   ├── f1041.pdf                 # Form 1041 (Phase 1)
│   ├── f1041sd.pdf               # Schedule D (Form 1041) — download from IRS
│   ├── f8960.pdf                 # Form 8960 — download from IRS
│   └── f8949.pdf                 # Form 8949 — download from IRS
├── 2025/
│   └── XXXX-X123.CSV             # Brokerage data (input)
└── output/
    ├── 2025_1041_filled.pdf
    ├── 2025_sched_d_filled.pdf
    ├── 2025_sched_g_filled.pdf   (part of f1041.pdf pages 2-3)
    ├── 2025_8960_filled.pdf
    └── 2025_8949_filled.pdf
```

**Note on Schedule G:** Schedule G is pages 2-3 of `f1041.pdf`. It is NOT a separate PDF. When `fill_pdf.py` fills `f1041.pdf`, it fills all 3 pages including Schedule B and Schedule G in one call.

### Pattern 1: Claude Slash Command (.claude/commands/fill-1041.md)
**What:** Slash command definition that invokes the Python skill script
**When to use:** Always — this is the user-facing entry point

```markdown
---
description: Fill Form 1041 and all required attachments from brokerage CSV
---

Run the Form 1041 skill:

```bash
/c/ProgramData/miniconda3/python fill_1041.py $ARGUMENTS
```

All arguments are passed through. Supported flags:
- `--dry-run` — print computed values without writing files
- `--year YYYY` — use config/YYYY.json (default: 2025)
- `--csv PATH` — override CSV input path
- `--output-dir PATH` — override output directory
```

### Pattern 2: fill_1041.py — Top-Level Structure
**What:** The main skill script that orchestrates CSV parsing, computation, and PDF writing

```python
# fill_1041.py — Core skill: parse CSV, compute tax schedules, fill PDFs

import argparse, csv, json, subprocess, sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

def parse_args():
    # Load config first for defaults
    # --year, --csv, --output-dir, --dry-run, --config

def load_config(year):
    # json.load(open(f"config/{year}.json"))

def load_fields(year):
    # json.load(open(f"config/{year}_fields.json"))

def parse_csv(csv_path):
    # Returns: {div_1a, div_1b, int_box1, transactions: [...]}
    # Each transaction: {description, date_acquired, date_sold,
    #   proceeds, cost, wash_sale_disallowed, term, form8949_code}

def compute_schedule_d(transactions):
    # Returns: {st_proceeds, st_cost, st_net, lt_proceeds, lt_cost, lt_net, net_combined}

def compute_form_1041_page1(csv_data, sched_d):
    # Returns all Page 1 field values

def compute_schedule_b(page1_values):
    # Returns Schedule B field values (zero distribution deduction)

def compute_schedule_g(taxable_income, qual_div, lt_net_gain, cfg):
    # Uses QD&CG worksheet (see Architecture Pattern 3 below)
    # Returns: {tax_on_taxable_income, total_tax, ...}

def compute_form_8960(csv_data, taxable_income, cfg):
    # Returns: {nii, agi_excess, niit_base, niit_amount}

def validate(csv_data, computed, tolerance=1.00):
    # Compare raw CSV values vs computed values
    # Halts on mismatch >= $1.00

def build_field_maps(computed, fields):
    # Returns dict per form: {field_id: value}

def call_fill_pdf(fields_json_path, form_path, output_path):
    # subprocess.run([python_exe, "fill_pdf.py", "--fields", ..., "--form", ..., "--output", ...])

def main():
    # 1. Print header (CSV path, blank form path, output dir)
    # 2. Parse CSV; print "Parsed CSV"
    # 3. Compute Schedule D; print "Computed Schedule D"
    # 4. Compute Schedule G; print "Computed Schedule G"
    # 5. Compute Form 8960; print "Computed Form 8960"
    # 6. Validate; print "Validation passed" or halt
    # 7. If --dry-run: print all field values grouped by form, exit
    # 8. For each form: write temp JSON, call fill_pdf.py, print "PDF written: path"
    # 9. Print final summary
```

### Pattern 3: QD&CG Worksheet (Schedule G CALC-04)
**What:** IRS Qualified Dividends and Capital Gains Tax Worksheet — required when trust has qualified dividends AND net long-term capital gains
**When to use:** Always for this trust (both conditions are met in 2025 data)

The worksheet computes tax by separating income subject to preferential rates from ordinary income:

```
Given:
  taxable_income       = gross_income - exemption ($100)
  preferential_income  = qualified_dividends + net_lt_capital_gains
  ordinary_income      = max(0, taxable_income - preferential_income)

Step 1: Tax on ordinary income using trust ordinary brackets:
  if ordinary_income <= 3150:     tax = ordinary_income * 0.10
  elif ordinary_income <= 11450:  tax = 315 + (ordinary_income - 3150) * 0.24
  elif ordinary_income <= 15650:  tax = 2307 + (ordinary_income - 11450) * 0.35
  else:                           tax = 3777 + (ordinary_income - 15650) * 0.37

Step 2: Preferential income tax using capital gains brackets:
  zero_bucket   = min(qdcg_worksheet.0_pct_max, taxable_income, preferential_income)
  fifteen_bucket = min(qdcg_worksheet.20_pct_threshold, taxable_income, preferential_income)
                   - zero_bucket
  twenty_bucket  = max(0, preferential_income - qdcg_worksheet.20_pct_threshold)

  cap_gains_tax = zero_bucket * 0.00 + fifteen_bucket * 0.15 + twenty_bucket * 0.20

Step 3: Total Schedule G Line 1a tax = ordinary_tax + cap_gains_tax

2025 expected values (from CSV data):
  taxable_income       = $105,040.67
  preferential_income  = $105,013.58 (qualified divs $903.82 + LT gain $104,109.76)
  ordinary_income      = $27.09
  ordinary_tax         = $2.71 (10% bracket)
  zero_bucket          = $3,250.00
  fifteen_bucket       = $12,650.00 (up to $15,900)
  twenty_bucket        = $89,113.58 (over $15,900)
  cap_gains_tax        = $0 + $1,897.50 + $17,822.72 = $19,720.22
  Schedule G Line 1a   = $2.71 + $19,720.22 = $19,722.93
```

All bracket values come from `config/2025.json` — never hardcoded in the script.

### Pattern 4: CSV Parsing State Machine
**What:** Parse the CSV by detecting section header rows and switching parse modes

The CSV structure uses section headers ("Form 1099DIV", "Form 1099INT", "Form 1099 B") as sentinel rows. After each header, the next row is a column header, followed by data rows until the next blank line or section header.

```python
def parse_csv(csv_path):
    section = None
    col_headers = None
    result = {'div_1a': 0, 'div_1b': 0, 'int_box1': 0, 'transactions': []}

    with open(csv_path, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if not any(row):  # blank row
                section = None
                col_headers = None
                continue

            first = row[0].strip('"').strip()

            if first in ('Form 1099DIV', 'Form 1099INT', 'Form 1099 B'):
                section = first
                col_headers = None  # next non-blank row is column header
                continue

            if section == 'Form 1099DIV':
                # Rows: box, description, amount, total, details
                box = row[0].strip('"').strip()
                if box == '1a':
                    result['div_1a'] = parse_dollar(row[3])
                elif box == '1b':
                    result['div_1b'] = parse_dollar(row[2])

            elif section == 'Form 1099INT':
                box = row[0].strip('"').strip()
                if box == '1':
                    result['int_box1'] = parse_dollar(row[3])

            elif section == 'Form 1099 B':
                if col_headers is None:
                    col_headers = row  # skip column header row
                    continue
                # Parse transaction row (23 columns)
                result['transactions'].append({
                    'description':        row[0].strip('"'),
                    'date_acquired':      row[1].strip('"'),  # "Various" or date
                    'date_sold':          row[2].strip('"'),
                    'proceeds':           parse_dollar(row[3]),
                    'cost':               parse_dollar(row[4]),
                    'wash_sale':          parse_dollar(row[6]),
                    'term':               row[7].strip('"').lower(),  # "Long term" or "Short term"
                    'form8949_code':      row[8].strip('"'),  # "D" or "A"
                    'covered':            row[11].strip('"').lower() == 'covered',
                })

    return result

def parse_dollar(s):
    # Strip "$", ",", quotes; return float
    return float(s.strip('"').replace('$', '').replace(',', '') or '0')
```

### Pattern 5: Validation Logic (SKILL-03)
**What:** Compare computed values against CSV raw values before writing any file

```python
def validate(csv_data, computed, tolerance=1.00):
    checks = [
        ('ordinary_dividends', csv_data['div_1a'],  computed['div_1a']),
        ('qualified_dividends', csv_data['div_1b'],  computed['div_1b']),
        ('interest_income',     csv_data['int_box1'], computed['int_box1']),
        ('net_short_term_gain', csv_data['st_gain'],  computed['st_gain']),
        ('net_long_term_gain',  csv_data['lt_gain'],  computed['lt_gain']),
    ]
    mismatches = []
    for name, expected, actual in checks:
        diff = abs(expected - actual)
        if diff >= tolerance:
            mismatches.append(f'  {name}: expected {expected:.2f}, got {actual:.2f}, diff {diff:.2f}')
    return mismatches  # empty = passed
```

### Pattern 6: Form PDF Downloads (Prerequisite)
**What:** Before Phase 2 implementation, blank PDFs for Schedule D, Form 8960, and Form 8949 must be downloaded and their AcroForm fields enumerated

IRS PDF URLs for 2025 tax year forms:
- Schedule D (Form 1041): https://www.irs.gov/pub/irs-pdf/f1041sd.pdf
- Form 8960: https://www.irs.gov/pub/irs-pdf/f8960.pdf
- Form 8949: https://www.irs.gov/pub/irs-pdf/f8949.pdf

After downloading to `forms/`, enumerate fields:
```python
from pypdf import PdfReader
reader = PdfReader("forms/f1041sd.pdf")
for name, field in reader.get_fields().items():
    print(name, field.get('/FT'))
```

Then extend `config/2025_fields.json` with `schedule_d_form`, `form_8960_form`, and `form_8949_form` sections containing the real field IDs.

### Anti-Patterns to Avoid
- **Parsing CSV with fixed column indices without checking column headers first:** The 1099-B section has 23 columns; always confirm by reading the header row before indexing data rows.
- **Computing tax at runtime from hardcoded bracket numbers:** All bracket lookups must use `config/2025.json` keys by name (e.g., `cfg['ordinary_income_brackets']['10_pct_max']`).
- **Filling all forms into one PDF call:** Each form is a separate blank PDF; call `fill_pdf.py` once per form with the appropriate `--form` and `--output` arguments.
- **Assuming Schedule D and Form 8960 field IDs match the null placeholders in 2025_fields.json:** Those are intentionally null — Phase 2 must enumerate real field IDs from the downloaded PDFs first.
- **Using python3 on this Windows machine:** The executable is `/c/ProgramData/miniconda3/python` (no "3"). `python3` resolves to the Windows Store stub (exit 49).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF form filling | Custom PDF bytes | `fill_pdf.py` (Phase 1 artifact) | Already built, tested, and handles checkbox translation |
| CSV parsing | Custom string splitting | `csv.reader` stdlib | Handles quoted fields, escaping, empty values correctly |
| Dollar value parsing | Custom regex | Strip `$`, `,`, quotes then `float()` | Simple pattern; all values in this CSV are simple dollar amounts |
| Tax bracket lookup | Hardcoded if/else constants | Load brackets from `config/2025.json` by key | Config-driven is the established pattern; brackets are per CALC-06 |
| Form 8960 line 21 | Separate PDF computation | Compute inline, write value to Schedule G field `f2_35[0]` | The NIIT result must appear in Schedule G (f1041.pdf). Also fill Form 8960 separately for completeness. |

---

## Common Pitfalls

### Pitfall 1: "296 transactions" vs 2 transactions
**What goes wrong:** Implementation tries to parse 296 individual lot rows from the CSV and finds only 2 rows.
**Why it happens:** CONTEXT.md says "296 1099-B transactions" but the CSV shows "296.00 VANGUARD" — the 296 is the share count, not transaction count. Schwab aggregates all lots into one row with "Various" acquisition date.
**How to avoid:** The CSV has exactly 2 1099-B rows. Process them as-is. The dry-run display for "one row per acquisition-date lot" is trivially satisfied since each row already represents one lot.
**Warning signs:** EOF or empty transaction list after parsing.

### Pitfall 2: "Various" date acquired — Form 8949 treatment
**What goes wrong:** Form 8949 Box D row has "Various" in column (b) Date Acquired. A naive date parser will fail.
**Why it happens:** Schwab reports multiple acquisition lots sold together as "Various."
**How to avoid:** Treat "Various" as a valid string value for the date-acquired field on Form 8949. IRS explicitly allows "Various" on Form 8949 column (b) when multiple lots are sold. Store and display as the literal string "Various".

### Pitfall 3: Qualified dividends vs ordinary dividends field placement
**What goes wrong:** Qualified dividends ($903.82) appears to equal ordinary dividends ($903.82), and both are filled on the same line.
**Why it happens:** The trust received only qualified dividends (Box 1b = Box 1a). Form 1041 has two qualified dividend fields: `qualified_dividends_beneficiaries` (f1_18) for the allocable-to-beneficiaries portion and `qualified_dividends_estate_or_trust` (f1_19) for the trust-retained portion. For a non-distributing accumulation trust, all qualified dividends go to f1_19.
**How to avoid:** Fill `qualified_dividends_estate_or_trust` (f1_19) with the qualified dividend amount; leave `qualified_dividends_beneficiaries` (f1_18) as $0 or blank.

### Pitfall 4: Schedule B zero-distribution complexity
**What goes wrong:** Schedule B has 15 computation fields (f2_8 through f2_22) but most are $0 for this trust. Filling only the non-zero fields may trigger hard-fail in fill_pdf.py if field IDs are wrong.
**Why it happens:** Schedule B fields start at `f2_8` (adjusted_total_income) in the catalog. For a non-distributing trust: income_required_to_be_distributed = $0, other_amounts_distributed = $0, total_distributions = $0. The distributable_net_income and income_distribution_deduction are also $0.
**How to avoid:** Fill all Schedule B fields explicitly, using $0 for fields that are zero. Do not skip zero-value fields — the PDF viewer expects consistent population.

### Pitfall 5: Schedule G Line 5 source
**What goes wrong:** NIIT from Form 8960 is filled in the wrong field or at the wrong amount.
**Why it happens:** Schedule G Line 5 references Form 8960 Line 21, which is the **trust** NIIT line — NOT individual Line 11. The field ID in f1041.pdf is `f2_35[0]` (`niit_form_8960_line21`). This was documented in Phase 1 and must be used exactly.
**How to avoid:** Use the semantic name `niit_form_8960_line21` which maps to `f2_35[0]` in `config/2025_fields.json`.

### Pitfall 6: NIIT AGI basis for trusts
**What goes wrong:** NIIT computed incorrectly because AGI for trusts is not the same as for individuals.
**Why it happens:** For trusts and estates, Form 8960 Line 9b is "undistributed net investment income" — essentially the taxable income (since this trust distributes nothing). The threshold on Line 9c is $15,650 (from config). Line 9d = Line 9b minus Line 9c. Line 10 = lesser of Line 8 (total NII) and Line 9d.
**How to avoid:** For this trust: taxable_income = $105,040.67; AGI_excess = $105,040.67 - $15,650 = $89,390.67; NII = $105,140.67; NIIT_base = min($105,140.67, $89,390.67) = $89,390.67; NIIT = $89,390.67 × 3.8% = $3,396.85.

### Pitfall 7: Form 1041 Page 1 tax field vs total
**What goes wrong:** `total_tax_from_schedule_g` (f1_43) on Page 1 is filled with just the Schedule G Line 9 tax, but `tax_due` (f1_48) must account for payments and credits.
**Why it happens:** Page 1 Line 24 (f1_43) is the total from Schedule G. Line 28 (f1_48) is tax after subtracting payments. For this trust with no prior payments: tax_due = total_tax_from_schedule_g.
**How to avoid:** Keep the computation chain clean: Schedule G total_tax → Page 1 f1_43 → after subtracting total_payments (0) → tax_due (f1_48).

---

## Code Examples

### CSV parsing — dollar value normalization
```python
# Source: analysis of 2025/XXXX-X123.CSV
def parse_dollar(s):
    """Parse dollar values like '$903.82', '0.12', or '' to float."""
    cleaned = s.strip('"').replace('$', '').replace(',', '').strip()
    return float(cleaned) if cleaned else 0.0
```

### NIIT computation
```python
# Source: config/2025.json niit section
def compute_niit(total_nii, taxable_income, cfg):
    """Compute Form 8960 NIIT for a trust/estate."""
    threshold = cfg['niit']['threshold']         # 15650
    rate = cfg['niit']['rate']                   # 0.038
    agi_excess = max(0.0, taxable_income - threshold)
    niit_base = min(total_nii, agi_excess)
    return round(niit_base * rate, 2)
```

### Schedule G via QD&CG worksheet
```python
# Source: IRS Form 1041 Schedule G instructions; config/2025.json
def compute_schedule_g(taxable_income, qual_div, lt_net_gain, cfg):
    """Compute Schedule G Line 1a tax via QD&CG worksheet."""
    brackets = cfg['ordinary_income_brackets']
    qdcg = cfg['qdcg_worksheet']

    preferential = qual_div + lt_net_gain
    ordinary = max(0.0, taxable_income - preferential)

    # Ordinary income tax
    b10 = brackets['10_pct_max']       # 3150
    b24 = brackets['24_pct_max']       # 11450
    b35 = brackets['35_pct_max']       # 15650
    if ordinary <= b10:
        ord_tax = ordinary * 0.10
    elif ordinary <= b24:
        ord_tax = b10 * 0.10 + (ordinary - b10) * 0.24
    elif ordinary <= b35:
        ord_tax = b10 * 0.10 + (b24 - b10) * 0.24 + (ordinary - b24) * 0.35
    else:
        ord_tax = b10 * 0.10 + (b24 - b10) * 0.24 + (b35 - b24) * 0.35 + (ordinary - b35) * 0.37

    # Capital gains / QD tax
    zero_max = qdcg['0_pct_max']               # 3250
    twenty_thresh = qdcg['20_pct_threshold']   # 15900

    zero_bucket    = min(zero_max, taxable_income, preferential)
    fifteen_bucket = max(0.0, min(twenty_thresh, taxable_income, preferential) - zero_bucket)
    twenty_bucket  = max(0.0, preferential - twenty_thresh)

    cap_tax = zero_bucket * 0.00 + fifteen_bucket * 0.15 + twenty_bucket * 0.20

    return round(ord_tax + cap_tax, 2)
```

### Subprocess call to fill_pdf.py
```python
# Source: fill_pdf.py interface (Phase 1)
import subprocess, json, tempfile, os

def fill_form(field_values, form_path, output_path):
    """Write field_values to a temp JSON file and call fill_pdf.py."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                     delete=False, encoding='utf-8') as f:
        json.dump(field_values, f, indent=2)
        tmp_path = f.name
    try:
        result = subprocess.run(
            ['/c/ProgramData/miniconda3/python', 'fill_pdf.py',
             '--fields', tmp_path,
             '--form', form_path,
             '--output', output_path],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"fill_pdf.py failed:\n{result.stderr}")
        print(f"PDF written: {output_path}")
    finally:
        os.unlink(tmp_path)
```

---

## Known Tax Values for 2025 Return

These values are computed from the actual CSV data and will serve as ground truth for validation:

| Item | Value | Source |
|------|-------|--------|
| Ordinary dividends (1099-DIV Box 1a) | $903.82 | CSV "Total" column, box 1a |
| Qualified dividends (1099-DIV Box 1b) | $903.82 | CSV "Amount" column, box 1b |
| Interest income (1099-INT Box 1) | $0.12 | CSV "Total" column, box 1 |
| Short-term proceeds | $1,030.79 | CSV 1099-B row 2 |
| Short-term cost basis | $903.82 | CSV 1099-B row 2 |
| Short-term net gain | $126.97 | Computed |
| Long-term proceeds | $226,514.41 | CSV 1099-B row 1 |
| Long-term cost basis | $122,404.65 | CSV 1099-B row 1 |
| Long-term net gain | $104,109.76 | Computed |
| Gross income | $105,140.67 | Sum of all income |
| Trust exemption | $100.00 | config/2025.json trust_exemption |
| Taxable income | $105,040.67 | Gross - $100 |
| Schedule G Line 1a tax (QD&CG method) | ~$19,722.93 | QD&CG worksheet |
| NIIT (Form 8960 Line 21) | ~$3,396.85 | 3.8% of $89,390.67 |
| Total tax | ~$23,119.77 | Schedule G + NIIT |

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Python module with classes/dataclasses | Single-file script with functions | Phase 1 decision | No pytest, no module structure — all logic in fill_1041.py |
| Separate Python pipeline (5 scripts) | Single Claude skill + fill_pdf.py | Phase 1 pivot | Simpler; Claude handles the logic, Python only writes files |
| Excel Schedule G calculator | QD&CG worksheet in code | Phase 2 | Automated; the Excel file in the repo is a reference/cross-check only |

---

## Open Questions

1. **Schedule D, Form 8960, Form 8949 AcroForm field names**
   - What we know: These forms are separate PDFs from f1041.pdf. Their field IDs are null placeholders in config/2025_fields.json.
   - What's unclear: Whether the 2025 IRS PDFs use AcroForm (fillable) or XFA-only format.
   - Recommendation: Wave 0 task must download all three PDFs, run `pypdf PdfReader.get_fields()` against each, and extend `config/2025_fields.json` with real field IDs. This is a blocking prerequisite before filling those forms.

2. **Schedule B: which fields to populate**
   - What we know: Schedule B (Page 2, f2_8 through f2_22) is embedded in f1041.pdf. For a non-distributing trust: distributions = $0, income_distribution_deduction = $0.
   - What's unclear: Whether to fill zero-value fields with "0" or leave blank. IRS instructions say Schedule B must be included even when distribution deduction is $0.
   - Recommendation: Fill all Schedule B fields explicitly — use "0" for zero-amount fields, not blank. This matches how the 2024 filed return would appear.

3. **Slash command argument passthrough**
   - What we know: Claude slash commands in `.claude/commands/` can run shell commands. The `$ARGUMENTS` variable passes user-typed arguments.
   - What's unclear: Whether argument passthrough from slash command to Python script works with `--dry-run` and path override flags without shell quoting issues.
   - Recommendation: Keep the command line simple; test with `--dry-run` first. Document any quoting requirements in the command file.

4. **Form 1041 Page 1 Line 9 (total deductions)**
   - What we know: With no deductions beyond the $100 exemption, total_deductions and adjusted_total_income should equal gross income.
   - What's unclear: Whether any fiduciary fee or other deduction should be claimed.
   - Recommendation: Fill as-is from CSV data: no deductions other than exemption. If user has fiduciary fees, they will need to add them manually to config.

---

## Validation Architecture

`nyquist_validation` is `true` in `.planning/config.json`. Per CONTEXT.md locked decisions: "No pytest, no dataclasses, no Python modules beyond the filler script." Testing is manual / smoke-test based.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None — no pytest per locked decisions |
| Config file | none |
| Quick run command | `/c/ProgramData/miniconda3/python fill_1041.py --dry-run` |
| Full suite command | `/c/ProgramData/miniconda3/python fill_1041.py` (then open all output PDFs) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PARSE-01 | Ordinary dividends = $903.82, qualified = $903.82 | smoke | `python fill_1041.py --dry-run` — check DIV values in output | ❌ Wave 0 — create fill_1041.py |
| PARSE-02 | Interest = $0.12 | smoke | `python fill_1041.py --dry-run` — check INT value | ❌ Wave 0 |
| PARSE-03 | 2 transactions extracted, LT=$104,109.76, ST=$126.97 | smoke | `python fill_1041.py --dry-run` | ❌ Wave 0 |
| CALC-01 | Box A (short-term) and Box D (long-term) assigned correctly | smoke | dry-run output shows form8949 row assignment | ❌ Wave 0 |
| CALC-02 | Schedule D nets: ST=$126.97, LT=$104,109.76 | smoke | dry-run Schedule D section | ❌ Wave 0 |
| CALC-03 | Taxable income = $105,040.67 | smoke | dry-run Page 1 section | ❌ Wave 0 |
| CALC-04 | Schedule G tax ~$19,722.93 | smoke | dry-run Schedule G section | ❌ Wave 0 |
| CALC-05 | NIIT = $3,396.85 | smoke | dry-run Form 8960 section | ❌ Wave 0 |
| CALC-07 | Schedule B included with $0 distribution deduction | smoke | dry-run Schedule B section | ❌ Wave 0 |
| PDF-02 | Form 1041 Page 1 filled correctly | manual | Open output/2025_1041_filled.pdf in browser | ❌ Wave 0 |
| PDF-03 | Schedule D (Form 1041) filled correctly | manual | Open output/2025_sched_d_filled.pdf | ❌ Wave 0 (requires form download) |
| PDF-04 | Schedule G fields filled (Pages 2-3 of f1041.pdf) | manual | Open output/2025_1041_filled.pdf pages 2-3 | ❌ Wave 0 |
| PDF-05 | Form 8960 filled correctly | manual | Open output/2025_8960_filled.pdf | ❌ Wave 0 (requires form download) |
| PDF-06 | NeedAppearances set — handled by fill_pdf.py | auto | Already verified in Phase 1 | ✅ (fill_pdf.py) |
| PDF-07 | Output at output/2025_1041_filled.pdf | smoke | Check file exists after run | ❌ Wave 0 |
| SKILL-01 | /fill-1041 command exists and runs | smoke | `/fill-1041 --dry-run` from Claude chat | ❌ Wave 0 — create .claude/commands/fill-1041.md |
| SKILL-02 | --dry-run prints values, no files written | smoke | Run with --dry-run, check output/ unchanged | ❌ Wave 0 |
| SKILL-03 | Mismatch validation halts on >= $1 diff | smoke | Manually edit CSV to introduce $2 error, run | ❌ Wave 0 |
| SKILL-04 | Path overrides work | smoke | `--csv 2025/XXXX-X123.CSV --output-dir output` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `/c/ProgramData/miniconda3/python fill_1041.py --dry-run` (confirms no import errors and CSV parse works)
- **Per wave merge:** Full run (no `--dry-run`) + open all output PDFs in browser to verify visible fields
- **Phase gate:** All 5 output PDFs exist, dry-run shows correct computed values matching ground truth table above, visual inspection confirms all fields visible in PDF viewer

### Wave 0 Gaps
- [ ] `fill_1041.py` — covers PARSE-01/02/03, CALC-01/02/03/04/05/07, PDF-02/03/04/05/07, SKILL-01/02/03/04
- [ ] `.claude/commands/fill-1041.md` — covers SKILL-01
- [ ] `forms/f1041sd.pdf` — download from IRS; required for PDF-03
- [ ] `forms/f8960.pdf` — download from IRS; required for PDF-05
- [ ] `forms/f8949.pdf` — download from IRS; required for CALC-01
- [ ] Field catalog extensions in `config/2025_fields.json` — Schedule D, Form 8960, Form 8949 real field IDs (replaces null placeholders)

---

## Sources

### Primary (HIGH confidence)
- Direct inspection of `2025/XXXX-X123.CSV` and `2025/XXXX-X123.XML` — actual CSV structure, section headers, column layout, all values confirmed
- `config/2025.json` — bracket values and thresholds used in computation examples
- `config/2025_fields.json` — all AcroForm field IDs confirmed from Phase 1 execution
- `fill_pdf.py` — interface confirmed by reading source
- Phase 1 SUMMARY and VERIFICATION documents — confirmed what was built and tested

### Secondary (MEDIUM confidence)
- IRS Form 8960 instructions (general knowledge) — NIIT computation for trusts uses undistributed net income vs $15,650 threshold
- IRS Publication 550 / Form 1041 Schedule G instructions — QD&CG worksheet selection conditions for trusts

### Tertiary (LOW confidence)
- Computation of Schedule G tax ($19,722.93) and NIIT ($3,396.85) — computed from first principles using verified bracket values; not cross-checked against Excel calculator yet

---

## Metadata

**Confidence breakdown:**
- CSV structure: HIGH — directly read the actual file, confirmed both section formats
- Transaction count (2 rows, not 296): HIGH — directly confirmed in CSV and XML
- Tax computation logic: HIGH — bracket values from verified config; worksheet algorithm from IRS instructions
- Computed tax amounts: MEDIUM — first-principles computation; Excel calculator cross-check is pending (v2 requirement VAL-01)
- AcroForm field IDs for f1041.pdf: HIGH — all verified in Phase 1 via live fill test
- AcroForm field IDs for separate forms (Schedule D, Form 8960, Form 8949): NOT YET KNOWN — Wave 0 task required

**Research date:** 2026-03-08
**Valid until:** 2026-12-31 (CSV structure and tax brackets are fixed for 2025 tax year; IRS form PDFs are fixed for this year)
