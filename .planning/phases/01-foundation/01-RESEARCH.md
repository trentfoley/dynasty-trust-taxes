# Phase 1: Foundation - Research

**Researched:** 2026-03-08
**Domain:** pypdf AcroForm filling, IRS Form 1041 field catalog, 2025 trust tax data
**Confidence:** HIGH

## Summary

Phase 1 creates three static artifacts that Phase 2 (the Claude skill) depends on. All three are now fully specified by direct investigation of the actual PDF and official IRS sources. The core infrastructure is already present: pypdf 6.7.5 is installed in the miniconda3 environment and works correctly against `forms/f1041.pdf`. The blank form is a hybrid AcroForm+XFA PDF-1.7 with 184 total fields (116 text + 57 checkboxes on 3 pages), and pypdf's `update_page_form_field_values` fills it successfully.

The critical finding is that IRS Form 1041 uses XFA-style hierarchical field names like `topmostSubform[0].Page1[0].DateNameAddress_ReadOrder[0].f1_1[0]`. These are the keys that `get_fields()` returns and that `fill_pdf.py` must use. The field names have no tooltips (TU is empty for all fields), so semantic mapping requires side-by-side reading of the blank form and the filed return. Checkbox On-state values are `'1'` or `'2'` — NOT `'Yes'`/`'Off'`.

The 2025 trust tax brackets are verified from two independent sources that agree with IRS-confirmed thresholds. All bracket values needed for `config/2025.json` are known.

**Primary recommendation:** Use pypdf's `PdfWriter.update_page_form_field_values(page=None, fields={...}, auto_regenerate=True)` with the full hierarchical field key names. Write `fill_pdf.py` as a thin argparse script around this pattern. Derive semantic mapping by reading the printed form line labels against the ordered field sequence.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Approach pivot**
- Primary implementation is a Claude skill, not a Python codebase
- Python exists only for `fill_pdf.py` — the one thing Claude can't do natively (write bytes to a PDF file)
- No pytest, no dataclasses, no Python modules beyond the filler script

**Config schema (config/2025.json)**
- Format: Named thresholds, not array of tuples — brackets expressed as named rate tiers (e.g., `"10_pct_max": 3150`) for readability and direct reference by name
- Trust metadata: Full trust identity in the config — trust name, EIN, trustee name, trustee address — so Claude can fill header fields without looking them up each run
- File paths: All default file paths in config — CSV input, blank form PDF, output directory
- All bracket math in config: Ordinary income brackets, capital gains brackets, NIIT threshold, trust exemption ($100), and QD&CG worksheet thresholds — no rate values hardcoded anywhere in skill or script

**Field catalog (config/2025_fields.json)**
- Structure: Grouped by form section — `form_1041_page1`, `schedule_d`, `schedule_g`, `form_8960` top-level keys; each maps semantic names to AcroForm field IDs
- Semantic mapping in Phase 1: Foundation does the full mapping work, not just raw field name dump. Cryptic pypdf IDs are mapped to readable semantic names before Phase 2 starts
- Mapping method: Claude reads `filed_returns/2024 1041.pdf` and `forms/f1041.pdf` side-by-side to identify which AcroForm field IDs correspond to which form line numbers

**fill_pdf.py interface**
- Input: `python fill_pdf.py --fields <json_file> --form <blank_pdf>`
- Error behavior: Fail hard — exit non-zero if any field name in the JSON is not found in the AcroForm. No silent skips
- Field types: Handles both text fields and checkbox fields. Checkbox values use `"Yes"` / `"Off"` convention (NOTE: see research finding below — actual On-state values are `'1'`/`'2'`, not `'Yes'`. fill_pdf.py must map convention to actual values)
- NeedAppearances: Set automatically so filled fields are visible in any PDF viewer

**Python environment**
- Minimal — `fill_pdf.py` only needs `pypdf`
- Claude's discretion on whether to use `requirements.txt` or `pyproject.toml`

### Claude's Discretion
- Whether to use `requirements.txt` or `pyproject.toml` for the Python environment declaration

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CALC-06 | All tax bracket thresholds and rates are stored in `config/YEAR.json` — no bracket values hardcoded in any skill or script | 2025 brackets fully verified from IRS sources; exact values documented in Standard Stack section below |
| PDF-01 | AcroForm field names discovered from blank `forms/f1041.pdf` via `pypdf PdfReader.get_fields()` and stored in `config/YEAR_fields.json` | PDF confirmed AcroForm (hybrid XFA+AcroForm); get_fields() returns 184 fields; hierarchical naming pattern documented |
| PDF-FILLER | `fill_pdf.py` accepts `--fields <json>` and `--form <blank_pdf>` and writes a filled PDF with `NeedAppearances` set | pypdf 6.7.5 verified to fill and write this PDF; `update_page_form_field_values` with `auto_regenerate=True` sets NeedAppearances automatically; argparse pattern documented |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pypdf | 6.7.5 | AcroForm field discovery and PDF filling | Already installed in miniconda3; pure Python; `get_fields()` + `update_page_form_field_values()` confirmed working on `forms/f1041.pdf` |
| Python (miniconda3) | 3.13.5 | Runtime for fill_pdf.py | Already present at `/c/ProgramData/miniconda3/python`; stdlib argparse + json suffice |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| argparse | stdlib | CLI interface for fill_pdf.py | Always — provides `--fields`, `--form`, `--output`, `--help` |
| json | stdlib | Read field-value JSON input | Always — field values passed as JSON file |
| sys | stdlib | exit(1) on validation errors | Always — hard-fail behavior required |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pypdf | pdfrw | pdfrw has fewer active maintainers; pypdf 6.x has `update_page_form_field_values` which handles multi-page and NeedAppearances in one call |
| pypdf | reportlab | reportlab builds PDFs from scratch; cannot fill existing AcroForms |
| pypdf | pdfforms / fillpdf | thin wrappers around pypdf; add dependency without adding value |

**Python executable:** `/c/ProgramData/miniconda3/python` (not `python3` which maps to Windows Store stub)

**Installation (already done):**
```bash
# pypdf 6.7.5 already installed; if needed:
/c/ProgramData/miniconda3/python -m pip install pypdf
```

**requirements.txt (recommended over pyproject.toml for a single-script tool):**
```
pypdf>=6.7.5
```

---

## Architecture Patterns

### Recommended Project Structure
```
dynasty-trust-taxes/
├── config/
│   ├── 2025.json          # tax brackets + trust metadata + file paths (CALC-06)
│   └── 2025_fields.json   # semantic name -> AcroForm field ID mapping (PDF-01)
├── forms/
│   └── f1041.pdf          # blank IRS AcroForm (already present)
├── filed_returns/         # reference return for semantic mapping (already present)
├── fill_pdf.py            # thin PDF filler script (PDF-FILLER)
├── requirements.txt       # pypdf>=6.7.5
└── output/                # filled PDFs written here (created by fill_pdf.py if absent)
```

### Pattern 1: fill_pdf.py — argparse + pypdf writer
**What:** Accept `--fields` (path to JSON of `{field_name: value}`) and `--form` (blank PDF path), write filled PDF to `output/YEAR_1041_filled.pdf`. Hard-fail on unknown field names.
**When to use:** Every time the skill needs to produce a PDF.

```python
# Verified against pypdf 6.7.5 source and f1041.pdf
import argparse, json, sys
from pypdf import PdfReader, PdfWriter

def main():
    ap = argparse.ArgumentParser(description="Fill IRS Form 1041 AcroForm PDF")
    ap.add_argument("--fields", required=True, help="JSON file: {field_name: value}")
    ap.add_argument("--form",   required=True, help="Blank AcroForm PDF path")
    ap.add_argument("--output", default="output/2025_1041_filled.pdf",
                    help="Output PDF path")
    args = ap.parse_args()

    with open(args.fields) as f:
        field_values = json.load(f)

    reader = PdfReader(args.form)
    known_fields = set(reader.get_fields().keys())

    # Hard-fail on unknown fields
    unknown = [k for k in field_values if k not in known_fields]
    if unknown:
        for u in unknown:
            print(f"ERROR: field not found in AcroForm: {u!r}", file=sys.stderr)
        sys.exit(1)

    writer = PdfWriter()
    writer.clone_reader_document_root(reader)

    # page=None fills all pages; auto_regenerate=True sets NeedAppearances
    writer.update_page_form_field_values(
        page=None,
        fields=field_values,
        auto_regenerate=True,
    )

    import os
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "wb") as f:
        writer.write(f)

    print(f"Filled PDF written to: {args.output}")

if __name__ == "__main__":
    main()
```

### Pattern 2: config/2025.json schema
**What:** Named rate tiers, trust metadata, file paths — all in one file.

```json
{
  "tax_year": 2025,
  "trust": {
    "name": "Trent Foley Childrens 2021 Super Dynasty Trust",
    "ein": "XX-XXXXXXX",
    "trustee_name": "...",
    "trustee_address": "..."
  },
  "paths": {
    "csv_input": "2025/XXXX-X123.CSV",
    "blank_form": "forms/f1041.pdf",
    "output_dir": "output"
  },
  "ordinary_income_brackets": {
    "10_pct_max": 3150,
    "24_pct_max": 11450,
    "35_pct_max": 15650,
    "37_pct_rate": 0.37
  },
  "capital_gains_brackets": {
    "0_pct_max": 3250,
    "15_pct_max": 15900,
    "20_pct_threshold": 15900
  },
  "niit": {
    "rate": 0.038,
    "threshold": 15650
  },
  "trust_exemption": 100
}
```

### Pattern 3: config/2025_fields.json schema
**What:** Semantic name to full AcroForm path mapping, grouped by section.

```json
{
  "form_1041_page1": {
    "trust_name":    "topmostSubform[0].Page1[0].DateNameAddress_ReadOrder[0].f1_1[0]",
    "interest_income": "topmostSubform[0].Page1[0].f1_15[0]",
    "ordinary_dividends": "topmostSubform[0].Page1[0].f1_16[0]"
  },
  "schedule_b": {
    "adjusted_total_income": "topmostSubform[0].Page2[0].f2_1[0]"
  },
  "schedule_g": {
    "tax_on_taxable_income": "topmostSubform[0].Page3[0].f3_1[0]"
  }
}
```

### Anti-Patterns to Avoid
- **Short field names only:** `update_page_form_field_values` requires the full hierarchical key (e.g., `topmostSubform[0].Page1[0].f1_15[0]`), not the short name (`f1_15[0]`). Using short names silently fails — no field gets filled.
- **Writing field values directly via PdfWriter._objects:** Bypass approach breaks NeedAppearances and is fragile across pypdf versions. Use `update_page_form_field_values`.
- **Using python3 as executable on Windows:** `python3` resolves to the Windows Store stub and exits 49 (not-found). Use `/c/ProgramData/miniconda3/python` or document the shebang explicitly.
- **Storing bracket values in fill_pdf.py:** The filler must know nothing about tax math. All numbers belong in config.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF form filling | Custom PDF byte manipulation | pypdf `update_page_form_field_values` | AcroForm widget annotation structure has dozens of edge cases; pypdf handles text, checkbox, radio, list fields correctly |
| NeedAppearances | Manual AcroForm dict surgery | `auto_regenerate=True` parameter | pypdf calls `set_need_appearances_writer(True)` which correctly updates the AcroForm dictionary entry |
| Multi-page filling | Loop over pages manually | `page=None` (fills all pages) | One call handles all 3 pages of Form 1041 correctly |
| Checkbox on-state detection | Hardcode "Yes" | Read `/_States_` from field dict | On-state varies by field: this form uses `'1'` and `'2'`, not `'Yes'` |

**Key insight:** The IRS PDF has a hybrid AcroForm+XFA structure. pypdf's `get_fields()` traverses the AcroForm tree (not XFA), and `update_page_form_field_values` writes to AcroForm annotations. This works for filling purposes even though XFA is present.

---

## Common Pitfalls

### Pitfall 1: Short field name vs full hierarchical key
**What goes wrong:** `update_page_form_field_values` is called with `{"f1_15[0]": "12345"}` but the field is never filled — no error is raised.
**Why it happens:** pypdf matches by the field's `/T` entry (short name within its parent), but `get_fields()` returns fully-qualified dotted paths as keys. The update loop iterates annotations and resolves qualified names, so you must pass the full qualified name.
**How to avoid:** Always use the full key returned by `get_fields()`, e.g., `topmostSubform[0].Page1[0].f1_15[0]`.
**Warning signs:** Filled PDF opens but all fields are blank.

### Pitfall 2: Checkbox value mismatch
**What goes wrong:** Checkbox field set to `"Yes"` but renders unchecked in the PDF viewer.
**Why it happens:** The On state for checkboxes in `forms/f1041.pdf` is `'1'` or `'2'` (from `/_States_`), not `'Yes'`. pypdf only sets the value; if the value doesn't match an AP state key, the viewer shows nothing.
**How to avoid:** `fill_pdf.py` must translate the user-facing `"Yes"`/`"Off"` convention to the actual state values. During Phase 1, the field catalog task should document the On-state value for each checkbox.
**Warning signs:** Checkboxes appear unchecked in any PDF viewer despite being in the field map.

### Pitfall 3: Python executable path
**What goes wrong:** `python fill_pdf.py --help` exits with code 49 (Windows Store not-found stub).
**Why it happens:** On this Windows machine, `python3` maps to the Windows Store app stub; the real interpreter is at `/c/ProgramData/miniconda3/python`.
**How to avoid:** Use `python` (which resolves to miniconda3 via PATH) or use the full path. Document this in `README` or in `CLAUDE.md`.
**Warning signs:** Exit code 49 or "Python was not found; run without arguments to install from Microsoft Store."

### Pitfall 4: Filed return is scanned (not AcroForm)
**What goes wrong:** Attempting `PdfReader('filed_returns/...').get_fields()` returns None or empty — there are no field values to extract for semantic mapping.
**Why it happens:** The 2024 filed return was confirmed to have no AcroForm fields — it is a 3-page PDF but `get_fields()` returns nothing. It may be a scanned or flattened PDF.
**How to avoid:** Semantic mapping must be done by reading the visual form structure (via `extract_text()`) of the blank form and matching line labels to field sequential order, NOT by reading values from the filed return. The filed return is useful for reference only as a visual guide.
**Warning signs:** `get_fields()` returns empty dict on the filed return.

### Pitfall 5: Assuming NeedAppearances is already set
**What goes wrong:** Filled PDF fields are invisible when opened in certain PDF viewers (Apple Preview, older Acrobat).
**Why it happens:** The blank `forms/f1041.pdf` does NOT have `NeedAppearances` set (confirmed: returns `None`). Without it, viewers use the existing appearance stream (which is blank/none for unfilled fields).
**How to avoid:** Always pass `auto_regenerate=True` to `update_page_form_field_values`. This calls `set_need_appearances_writer(True)` internally.
**Warning signs:** Fields show in Adobe Acrobat but not in Preview; or vice versa.

---

## Code Examples

### Discovering all AcroForm fields
```python
# Source: verified against pypdf 6.7.5 on forms/f1041.pdf
from pypdf import PdfReader

reader = PdfReader("forms/f1041.pdf")
fields = reader.get_fields()

for name, field in fields.items():
    ft = field.get("/FT")
    if ft == "/Tx":
        print(f"TEXT:     {name}")
    elif ft == "/Btn":
        states = field.get("/_States_", [])
        on_state = [s for s in states if s != "/Off"]
        print(f"CHECKBOX: {name}  on_state={on_state}")
```

### Getting checkbox On-state values
```python
# Source: verified against forms/f1041.pdf — On states are '1' or '2', NOT 'Yes'
from pypdf import PdfReader

reader = PdfReader("forms/f1041.pdf")
fields = reader.get_fields()

for name, field in fields.items():
    if field.get("/FT") == "/Btn":
        states = field.get("/_States_", [])
        on_values = [s.lstrip("/") for s in states if s != "/Off"]
        print(f"{name}: on_value={on_values}")
        # Output example: on_value=['1']  or  on_value=['2']
```

### Full fill_pdf.py pattern (reference)
See Architecture Patterns section above.

---

## PDF Field Inventory Summary

Confirmed by running `get_fields()` against `forms/f1041.pdf` (pypdf 6.7.5):

| Page | Text Fields | Checkboxes | Notable Sections |
|------|------------|------------|-----------------|
| Page1[0] | 60 | 27 | DateNameAddress (f1_1–f1_11), LinesA-B checkboxes (c1_1–c1_9), LinesC-E, income/deduction lines (f1_15–f1_60) |
| Page2[0] | 42 | 0 | Schedule A, Schedule B, Schedule D (Ln1a_ReadOrder) |
| Page3[0] | 14 | 30 | Schedule G Part I + Part II, Other Information Yes/No boxes |
| **Total** | **116** | **57** | **184 total** |

Field naming convention: `topmostSubform[0].Page{N}[0].{section}[0].{id}[0]`

Leaf field IDs follow the pattern:
- Text fields: `f{page}_{seq}[0]` (e.g., `f1_15[0]`, `f2_23[0]`)
- Checkboxes: `c{page}_{seq}[0]` (e.g., `c1_1[0]`, `c3_1[0]`)

---

## 2025 Tax Data Reference

### Ordinary Income Tax Brackets (trusts and estates)
| Bracket | Max Taxable Income | Rate |
|---------|-------------------|------|
| 10% | $3,150 | 10% |
| 24% | $11,450 | 24% |
| 35% | $15,650 | 35% |
| 37% | Over $15,650 | 37% |

Source: ardentrust.com + smartasset.com (two independent sources agree). Consistent with IRS-confirmed NIIT threshold of $15,650 which aligns with the 37% bracket entry point.

### Capital Gains / Qualified Dividends Rates (trusts and estates)
| Rate | Income Range |
|------|-------------|
| 0% | $0 – $3,250 |
| 15% | $3,251 – $15,900 |
| 20% | Over $15,900 |

Source: Confirmed by IRS instructions search result (from i1041.pdf description): "For tax year 2025, the 20% maximum capital gains rate applies to estates and trusts with income above $15,900."

### NIIT Threshold
- **$15,650** — confirmed by IRS Topic 559 (irs.gov/taxtopics/tc559)
- Rate: 3.8% of lesser of (net investment income, AGI minus $15,650)

### Trust Exemption
- Complex trust: **$100** (from REQUIREMENTS.md CALC-03)

### QD&CG Worksheet Thresholds
The QD&CG worksheet (used in Schedule G) uses the same thresholds as capital gains rates above. The worksheet compares taxable income against the 0% threshold ($3,250) and the 20% threshold ($15,900) to determine blended tax.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PyPDF2 (archived) | pypdf (same maintainers, rebranded) | 2022 | pypdf is the active successor; same API patterns |
| `page=specific_page` for each page | `page=None` fills all pages | pypdf 4+ | One call fills all 3 Form 1041 pages |
| Manual `NeedAppearances` dict surgery | `auto_regenerate=True` param | pypdf 4+ | Built-in, no dict manipulation needed |

---

## Open Questions

1. **Checkbox translation layer in fill_pdf.py**
   - What we know: Checkbox On-state in this PDF is `'1'` or `'2'`, but the CONTEXT.md says fill_pdf.py should accept `"Yes"`/`"Off"` convention
   - What's unclear: Should fill_pdf.py translate `"Yes"` → `"1"` generically, or should it read `/_States_` at runtime to find the actual On-state value for each field?
   - Recommendation: Read `/_States_` at runtime — translate `"Yes"` to the first non-`/Off` state found. This is robust if future IRS forms use different state names.

2. **Semantic field mapping method (filed return is scanned)**
   - What we know: `filed_returns/2024 1041 Trent Foley Childrens 2021 Super Dynasty Trust.pdf` has no AcroForm fields — it's a flattened/scanned PDF. It cannot be used for programmatic value extraction.
   - What's unclear: How much semantic mapping can be done by reading form text vs. needing to visually compare PDFs?
   - Recommendation: Claude should extract text from `forms/f1041.pdf` (which has good text extraction) to read line labels, then map them to field IDs by position/sequence. The 1099 composite PDF in `2025/` can confirm data values for cross-check. Visual side-by-side comparison of the filed return remains useful for confirming which checkbox was checked.

3. **Output path default**
   - What we know: CONTEXT.md says output goes to `output/YEAR_1041_filled.pdf`; config has output_dir
   - What's unclear: Whether fill_pdf.py should derive the filename from config or accept `--output` argument
   - Recommendation: Accept `--output` argument with a sensible default. The skill writes the temp JSON and passes `--output` explicitly, so the default is a fallback for manual use.

---

## Validation Architecture

`nyquist_validation` is `true` in `.planning/config.json`. However, per CONTEXT.md locked decisions: "No pytest, no dataclasses, no Python modules beyond the filler script." There is no test framework for this phase.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None — testing is manual (per locked decisions: no pytest) |
| Config file | none |
| Quick run command | `python fill_pdf.py --help` |
| Full suite command | `python fill_pdf.py --fields test_fields.json --form forms/f1041.pdf` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CALC-06 | `config/2025.json` exists and contains all bracket values with no hardcoded values in scripts | manual | inspect file + grep scripts for hardcoded numbers | ❌ Wave 0 — create config/2025.json |
| PDF-01 | `config/2025_fields.json` exists with real field names from get_fields() | smoke | `python -c "import json; d=json.load(open('config/2025_fields.json')); print(len(d))"` | ❌ Wave 0 — create config/2025_fields.json |
| PDF-FILLER | `python fill_pdf.py --help` succeeds; fill run produces visible-field PDF | smoke | `python fill_pdf.py --help` then fill with test JSON | ❌ Wave 0 — create fill_pdf.py |

### Sampling Rate
- **Per task:** `python fill_pdf.py --help` (confirms no import errors)
- **Per wave merge:** `python fill_pdf.py --fields <test_json> --form forms/f1041.pdf --output output/test_filled.pdf` then open in PDF viewer to confirm visible fields
- **Phase gate:** All three files exist, `--help` passes, test fill produces a readable PDF

### Wave 0 Gaps
- [ ] `config/2025.json` — covers CALC-06
- [ ] `config/2025_fields.json` — covers PDF-01
- [ ] `fill_pdf.py` — covers PDF-FILLER
- [ ] `requirements.txt` — `pypdf>=6.7.5`
- [ ] `output/` directory — created by fill_pdf.py at runtime with `os.makedirs(..., exist_ok=True)`

---

## Sources

### Primary (HIGH confidence)
- Direct pypdf 6.7.5 execution against `forms/f1041.pdf` — field names, types, On-state values, fill behavior all verified by running Python in the project directory
- `pypdf.PdfWriter.update_page_form_field_values` source code — signature, `page=None` behavior, NeedAppearances via `auto_regenerate` — read via `inspect.getsource`
- IRS irs.gov/taxtopics/tc559 — 2025 NIIT threshold $15,650 confirmed

### Secondary (MEDIUM confidence)
- ardentrust.com/insights/trust-tax-rates-deductions — 2025 ordinary income brackets ($3,150 / $11,450 / $15,650) — consistent with NIIT threshold from IRS primary source
- smartasset.com/taxes/trust-tax-rates — identical brackets — cross-validates ardentrust
- IRS instructions search results confirming 2025 capital gains thresholds ($3,250 / $15,900 / 20% over $15,900)

### Tertiary (LOW confidence)
- ustaxcalculators.com — brackets differ from above ($2,850 / $10,450 / $15,200) — likely 2024 data. Excluded from recommendations.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pypdf 6.7.5 directly verified against the actual PDF; all API behavior confirmed by source inspection
- PDF field inventory: HIGH — executed `get_fields()` directly; all 184 fields enumerated with types and On-state values
- 2025 tax brackets: MEDIUM — two independent non-IRS sources agree, consistent with IRS-confirmed NIIT threshold; official IRS PDFs were not machine-readable via WebFetch
- Architecture patterns: HIGH — derived directly from verified pypdf behavior on this specific PDF
- Pitfalls: HIGH — all discovered by direct execution (checkbox On-state, Python path, filed return format)

**Research date:** 2026-03-08
**Valid until:** 2026-12-31 (tax brackets are fixed for 2025 tax year; pypdf API is stable; PDF structure is fixed until IRS releases a new form version)
