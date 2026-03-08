# Architecture Research

**Domain:** Single-trust annual tax preparation CLI tool (Python)
**Researched:** 2026-03-08
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI / Orchestrator                       │
│  main.py --year 2025 --csv 2025/XXXX-X123.CSV                   │
│           --form forms/f1041.pdf --out output/1041_2025.pdf     │
└───────────┬─────────────────────────────────────────────────────┘
            │ calls in sequence
            ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. CSV Parser          2. Tax Calculator    3. PDF Filler       │
│  ┌───────────────┐      ┌──────────────┐    ┌──────────────┐    │
│  │ parse_csv()   │  →   │ compute_1041 │ →  │ fill_pdf()   │    │
│  │ parse_xml()   │      │ compute_sched│    │              │    │
│  │ (fallback)    │      │ _d(), _g()   │    │              │    │
│  └───────────────┘      └──────────────┘    └──────────────┘    │
│        returns                returns              writes        │
│    BrokerageData            TaxReturn            output PDF     │
└─────────────────────────────────────────────────────────────────┘
            │                     │                    │
            ▼                     ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Config Layer                               │
│  config/2025.json  (tax brackets, field mappings, trust info)   │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Boundary |
|-----------|----------------|----------|
| CLI / Orchestrator | Accept `--year`, `--csv`, `--form`, `--out` args; call components in order; surface errors with context | Owns nothing except wiring |
| CSV Parser | Read the multi-section brokerage CSV; return a structured `BrokerageData` dataclass; fall back to XML if CSV parse fails | Input is raw file path; output is pure Python data, no tax logic |
| Tax Calculator | Apply IRS logic to `BrokerageData`; compute Schedule D, Schedule G, and Form 1041 line values; return `TaxReturn` dataclass | No file I/O; no PDF knowledge; purely functional |
| PDF Filler | Enumerate AcroForm fields from blank IRS PDF; map `TaxReturn` fields using year config; write filled output PDF | No tax logic; no CSV knowledge; accepts `TaxReturn` + field mapping dict |
| Config Layer | Year-keyed JSON files with trust metadata, tax bracket tables, AcroForm field name mappings | Static data; never computed at runtime |

## Recommended Project Structure

```
dynasty-trust-taxes/
├── main.py                   # CLI entry point and orchestrator
├── parser.py                 # CSV (and XML fallback) parser
├── calculator.py             # Tax computation logic (Schedule D, G, 1041)
├── filler.py                 # PDF AcroForm field filler
├── models.py                 # BrokerageData, TaxReturn dataclasses
├── config/
│   ├── 2025.json             # Tax year config: brackets, field map, trust info
│   └── 2024.json             # (retained for reference / re-run)
├── forms/
│   └── f1041.pdf             # Blank IRS AcroForm PDF (replaced each year)
├── 2025/
│   ├── XXXX-X123.CSV         # Brokerage input (primary)
│   ├── XXXX-X123.XML         # Brokerage input (fallback)
│   └── *.PDF                 # Brokerage PDF (reference only)
├── filed_returns/            # Completed PDFs kept for reference
├── output/                   # Generated PDFs land here (gitignored)
└── tests/
    ├── test_parser.py
    ├── test_calculator.py
    └── test_filler.py
```

### Structure Rationale

- **Flat module layout (not src/):** Four modules at root is appropriate for a tool this size; sub-packages add indirection with no benefit.
- **config/YEAR.json:** Separates the two things that change annually (tax brackets and AcroForm field names) from code that never changes.
- **models.py separate from logic:** Both `parser.py` and `calculator.py` import the same dataclasses; separating them avoids circular imports.
- **output/ gitignored:** Generated PDFs contain PII and should not be committed.

## Key Data Structures

### BrokerageData (output of parser.py)

```python
@dataclass
class DividendData:
    ordinary_dividends: Decimal       # 1099-DIV box 1a
    qualified_dividends: Decimal      # 1099-DIV box 1b
    federal_tax_withheld: Decimal     # 1099-DIV box 4

@dataclass
class InterestData:
    interest_income: Decimal          # 1099-INT box 1
    federal_tax_withheld: Decimal     # 1099-INT box 4

@dataclass
class Sale:
    description: str                  # "296.00 VANGUARD INFORMATION TECHNOLOGY ETF"
    date_acquired: str                # "Various"
    date_sold: str                    # "12/24/2025"
    proceeds: Decimal                 # 226514.41
    cost_basis: Decimal               # 122404.65
    wash_sale_disallowed: Decimal     # 0.00
    gain_loss_type: str               # "Long term" | "Short term"
    form_8949_code: str               # "D" | "A"

@dataclass
class BrokerageData:
    tax_year: int
    account: str
    dividends: DividendData
    interest: InterestData
    sales: list[Sale]
```

### TaxReturn (output of calculator.py)

```python
@dataclass
class ScheduleD:
    short_term_proceeds: Decimal
    short_term_basis: Decimal
    short_term_gain_loss: Decimal     # net
    long_term_proceeds: Decimal
    long_term_basis: Decimal
    long_term_gain_loss: Decimal      # net
    total_capital_gain: Decimal       # flows to Form 1041 line 4

@dataclass
class ScheduleG:
    taxable_income: Decimal
    income_tax: Decimal               # from tax rate schedule
    tax_on_qualified_div_and_ltcg: Decimal  # from QDCGT worksheet

@dataclass
class TaxReturn:
    tax_year: int
    # Form 1041 page 1 lines
    interest_income: Decimal          # line 1
    ordinary_dividends: Decimal       # line 2a
    qualified_dividends: Decimal      # line 2b
    total_income: Decimal             # line 9
    total_deductions: Decimal         # line 15
    taxable_income: Decimal           # line 22
    # Schedules
    schedule_d: ScheduleD
    schedule_g: ScheduleG
    # Trust metadata (for header fields)
    trust_name: str
    ein: str
    trustee_name: str
```

### Year Config (config/2025.json)

```json
{
  "tax_year": 2025,
  "trust": {
    "name": "TRENT FOLEY CHILDRENS 2021 SUPER DYNASTY TR",
    "ein": "XX-XXXXXXX",
    "trustee_name": "TRENT FOLEY",
    "address": "...",
    "state": "XX",
    "zip": "XXXXX",
    "fiduciary_type": "trustee"
  },
  "tax_brackets": [
    {"over": 0,      "not_over": 3150,  "rate": 0.10, "base": 0},
    {"over": 3150,   "not_over": 11450, "rate": 0.24, "base": 315},
    {"over": 11450,  "not_over": 15200, "rate": 0.35, "base": 2307},
    {"over": 15200,  "not_over": null,  "rate": 0.37, "base": 3619.50}
  ],
  "qualified_div_ltcg_brackets": [
    {"over": 0,     "not_over": 3250,  "rate": 0.00},
    {"over": 3250,  "not_over": 15900, "rate": 0.15},
    {"over": 15900, "not_over": null,  "rate": 0.20}
  ],
  "field_map": {
    "trust_name":           "f1_01[0]",
    "ein":                  "f1_02[0]",
    "interest_income":      "f1_20[0]",
    "ordinary_dividends":   "f1_21[0]",
    "qualified_dividends":  "f1_22[0]",
    "total_capital_gain":   "f1_24[0]",
    "total_income":         "f1_29[0]",
    "taxable_income":       "f1_40[0]",
    "income_tax":           "f1_42[0]"
  }
}
```

Note: AcroForm field names (like `f1_01[0]`) must be discovered by running `pypdf`'s `reader.get_fields()` against the actual blank IRS PDF before the field map can be populated. This is a one-time setup step per tax year when IRS releases a new form.

## Architectural Patterns

### Pattern 1: Pure-Function Calculator

**What:** `calculator.py` exports functions that take `BrokerageData` + config dict and return `TaxReturn`. No side effects, no file access.

**When to use:** Always for tax logic — it enables unit testing with hardcoded inputs without touching the filesystem or PDF libraries.

**Trade-offs:** Requires all inputs passed explicitly (slightly more boilerplate), but produces fully deterministic, testable computation.

```python
def compute_return(data: BrokerageData, config: dict) -> TaxReturn:
    sched_d = compute_schedule_d(data.sales)
    sched_g = compute_schedule_g(
        taxable_income=...,
        qualified_div=data.dividends.qualified_dividends,
        ltcg=sched_d.long_term_gain_loss,
        config=config,
    )
    return TaxReturn(...)
```

### Pattern 2: Config-Driven Field Mapping

**What:** AcroForm field names and tax bracket tables live in `config/YEAR.json`, not hardcoded in Python. The filler reads the field map at runtime and applies it generically.

**When to use:** Required for year-over-year reusability — IRS may change AcroForm field names when releasing a new form version.

**Trade-offs:** Adding a new tax year requires editing a JSON file (acceptable) rather than editing Python (risky). The field map must be validated against the actual blank PDF before first use each year.

### Pattern 3: Decimal Arithmetic Throughout

**What:** Use Python's `decimal.Decimal` for all dollar amounts, never `float`.

**When to use:** Any monetary computation — tax calculations that lose cents due to floating-point rounding are incorrect returns.

**Trade-offs:** Slightly more verbose than float, requires explicit `Decimal("903.82")` construction from strings. Worth it unconditionally.

### Pattern 4: Section-Aware CSV Parsing

**What:** The Schwab CSV is not a standard rectangular table. It contains multiple labelled sections (1099-DIV, 1099-INT, 1099-B) separated by blank rows and section headers. The parser must locate each section by header sentinel, then parse that section's rows independently.

**When to use:** Required for this specific CSV format. Do not attempt `pandas.read_csv()` on the whole file — it will fail because column count changes between sections.

**Implementation approach:**
```python
# Scan lines until sentinel, then parse rows until next blank/sentinel
def _find_section(lines: list[str], sentinel: str) -> list[list[str]]:
    in_section = False
    rows = []
    for line in lines:
        if sentinel in line:
            in_section = True
            continue
        if in_section and line.strip() == "":
            break
        if in_section:
            rows.append(line)
    return rows
```

## Data Flow

### Full Pipeline

```
2025/XXXX-X123.CSV
        │
        ▼
  parser.parse_csv(path)
        │  reads sections: 1099-DIV, 1099-INT, 1099-B
        │  constructs Sale records from 1099-B rows
        ▼
  BrokerageData
        │
        ▼
  calculator.compute_return(data, config)
        │  compute_schedule_d: sum ST proceeds/basis → ST gain; LT proceeds/basis → LT gain
        │  compute_schedule_g: apply ordinary brackets to taxable income;
        │                      apply QDCGT worksheet for qualified div + LT gain
        ▼
  TaxReturn
        │
        ▼
  filler.fill_pdf(blank_pdf_path, tax_return, field_map, output_path)
        │  open blank PDF with pypdf PdfReader
        │  clone into PdfWriter
        │  call update_page_form_field_values(pages, field_dict, auto_regenerate=False)
        │  optionally flatten (convert fields to static text)
        ▼
  output/1041_2025.pdf   (print-ready)
```

### Error Flow

```
CLI
 ├── CSV parse error → print which section failed, suggest XML fallback, exit 1
 ├── Tax calc error  → print which line/schedule, show inputs, exit 1
 └── PDF fill error  → print which field name failed (helps debug field map), exit 1
```

## Build Order

The components have a strict dependency chain. Build in this order:

### Phase 1 — Foundation

1. **`models.py`** — Define `BrokerageData`, `TaxReturn`, and sub-dataclasses. No dependencies. Everything else imports from here.
2. **`config/2025.json` skeleton** — Trust metadata and tax brackets. AcroForm field names can be placeholder strings until Phase 3.

### Phase 2 — Input (CSV Parser)

3. **`parser.py`** — Section-aware CSV reader returning `BrokerageData`. Test with `2025/XXXX-X123.CSV`. Also implement XML fallback using `xml.etree.ElementTree` (standard library).
4. **`tests/test_parser.py`** — Validate 2025 data: ordinary dividends = $903.82, interest = $0.12, LT gain = $104,109.76, ST gain = $126.97.

### Phase 3 — Compute (Tax Calculator)

5. **`calculator.py`** — Schedule D, Schedule G, and Form 1041 line computations. Pure functions, fully testable without files.
6. **`tests/test_calculator.py`** — Validate against the `1041 Schedule G Calculator.xlsx` reference for 2025 numbers.

### Phase 4 — Output (PDF Filler)

7. **Field name discovery** — Run `pypdf reader.get_fields()` against `forms/f1041.pdf`; populate `config/2025.json` field_map with actual AcroForm names.
8. **`filler.py`** — Generic filler using pypdf `PdfWriter.update_page_form_field_values()`. Accepts any `TaxReturn` + field map.
9. **`tests/test_filler.py`** — Verify output PDF has expected field values; compare against `filed_returns/2024 1041 ...pdf` for structural parity.

### Phase 5 — CLI Orchestrator

10. **`main.py`** — Wire parser → calculator → filler with `argparse`. Add `--dry-run` flag that prints computed `TaxReturn` without writing PDF.

**Why this order:** Models must exist before anything can import them. Parser must work before calculator can be validated against real data. Calculator must produce correct numbers before filler is worth building. Field name discovery is a manual step that blocks the filler.

## Year-Over-Year Reusability

Each new tax year requires exactly three actions:

| Action | Who does it | Where |
|--------|-------------|-------|
| Drop new brokerage CSV into `YEAR/` folder | Trustee | `2025/` → `2026/` |
| Download new blank Form 1041 from IRS | Developer | `forms/f1041.pdf` (replace) |
| Create `config/YEAR.json` by copying prior year, updating tax brackets and AcroForm field names | Developer | `config/2026.json` |

Tax brackets are published by IRS each November. AcroForm field names typically stay stable year to year but must be verified with `reader.get_fields()` on the new blank form. The Python code itself should not need modification unless the form's structure changes dramatically.

## Anti-Patterns

### Anti-Pattern 1: Hardcoded Field Names in Python

**What people do:** Write `fields["f1_20[0]"] = str(interest_income)` directly in `filler.py`.

**Why it's wrong:** IRS releases a new blank Form 1041 PDF every year. AcroForm field names can change (or the form gains/loses pages). Hardcoded names require code edits every year and create fragile coupling.

**Do this instead:** Field names live exclusively in `config/YEAR.json`. The filler is a generic mapping engine: `{tax_return_attr: field_name}`.

### Anti-Pattern 2: Float Arithmetic for Tax Amounts

**What people do:** `gain = 226514.41 - 122404.65  # float subtraction`.

**Why it's wrong:** IEEE 754 float representation accumulates rounding error. Tax returns must match IRS-expected values to the cent. A $0.01 rounding error on any line is a filing discrepancy.

**Do this instead:** Parse all CSV amounts as `Decimal` from string immediately at parse time. Never convert through float.

### Anti-Pattern 3: Monolithic Script

**What people do:** Write everything in one `main.py` — CSV reading, tax math, and PDF writing interleaved.

**Why it's wrong:** Impossible to unit test tax logic without a real PDF and real CSV. Debugging a wrong Schedule G value requires running the full pipeline. Each component is untestable in isolation.

**Do this instead:** Four separate modules with clear interfaces. The orchestrator in `main.py` calls each in sequence.

### Anti-Pattern 4: Using pandas.read_csv() on the Schwab CSV Directly

**What people do:** `df = pandas.read_csv("XXXX-X123.CSV")` expecting a rectangular DataFrame.

**Why it's wrong:** The Schwab CSV has multiple sections with different column counts separated by blank lines and section headers. `read_csv()` on the whole file produces garbled or errored output.

**Do this instead:** Read the file as raw lines with Python's `csv.reader`, detect section sentinels ("Form 1099DIV", "Form 1099INT", "Form 1099 B"), and parse each section independently. No pandas needed at all — the dataset is tiny (3 sections, 2 sale rows).

### Anti-Pattern 5: Flattening the PDF Immediately

**What people do:** Call `flatten=True` on first write, making fields uneditable.

**Why it's wrong:** If a field value is wrong, you cannot re-open the PDF and correct one field — you must regenerate from scratch. For a tax return where manual review is required before printing, editable fields are valuable.

**Do this instead:** Leave AcroForm fields editable in the output PDF. Only flatten if explicitly requested (e.g., a `--flatten` CLI flag). The trustee can open the filled PDF in Acrobat, verify all fields visually, and print.

## Integration Points

### External Services

None. Tool runs entirely offline per requirements.

### Internal Boundaries

| Boundary | Communication | Contract |
|----------|---------------|----------|
| parser → calculator | `BrokerageData` dataclass (via `models.py`) | Parser never performs tax logic; calculator never touches raw CSV |
| calculator → filler | `TaxReturn` dataclass (via `models.py`) | Calculator never knows field names; filler never knows tax rules |
| config → calculator | Dict loaded from JSON (`config[tax_year]`) | Calculator receives brackets as data, not hardcoded constants |
| config → filler | `field_map` dict from same JSON | Filler receives mapping as data, not hardcoded field names |
| CLI → all | Function calls with typed arguments | No global state; all data flows through return values |

## Scaling Considerations

This tool is a single-user annual CLI. Scaling is not a concern. Relevant "load" considerations:

| Concern | Reality | Approach |
|---------|---------|----------|
| Multiple accounts | Currently one account | Parser could accept multiple CSVs; TaxReturn would aggregate |
| Multi-page Form 1041 | Schedule D is a separate page | `update_page_form_field_values` accepts `None` for all pages; handle multi-page in filler |
| Performance | 2 sale rows, runs in under 1 second | No optimization needed |

## Sources

- [pypdf AcroForm documentation](https://pypdf.readthedocs.io/en/stable/user/forms.html) — HIGH confidence
- [IRS Form 1041 instructions 2025](https://www.irs.gov/instructions/i1041) — HIGH confidence (official IRS)
- [IRS Schedule D (Form 1041) 2025](https://www.irs.gov/pub/irs-pdf/f1041sd.pdf) — HIGH confidence (official IRS)
- [pypdf PdfWriter class reference](https://pypdf.readthedocs.io/en/stable/modules/PdfWriter.html) — HIGH confidence
- CSV format: inspected directly from `2025/XXXX-X123.CSV` — HIGH confidence (primary source)

---
*Architecture research for: Python Form 1041 trust tax preparation CLI*
*Researched: 2026-03-08*
