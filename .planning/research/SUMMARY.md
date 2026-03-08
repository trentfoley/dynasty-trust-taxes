# Project Research Summary

**Project:** Dynasty Trust Taxes — IRS Form 1041 Automated Filler
**Domain:** Python CLI tool — brokerage CSV ingestion, trust tax computation, IRS AcroForm PDF filling
**Researched:** 2026-03-08
**Confidence:** HIGH

## Executive Summary

This project automates the annual preparation of IRS Form 1041 for the TRENT FOLEY CHILDRENS 2021 SUPER DYNASTY TR — a complex accumulation trust with brokerage investment income only. The trust's 2025 income (~$105,140 total: $104,237 capital gains, $903.82 dividends, $0.12 interest) places it firmly in the top ordinary income bracket (37%) and capital gains bracket (20%), with NIIT applying to substantially all income. Expert practice for this class of tool is a four-module Python CLI: a section-aware CSV parser feeding a pure-function tax calculator feeding a config-driven PDF filler, all wired by a thin orchestrator. The entire tool runs offline, has no external dependencies beyond pypdf, and produces print-ready IRS AcroForm PDFs in a single command.

The recommended approach uses Python 3.13 + pypdf 6.7.5 + stdlib decimal/csv/xml — all pure Python, no compilation, no admin rights required on Windows. Tax bracket tables and AcroForm field name mappings are externalized to year-keyed JSON config files, making the tool reusable each year with only a config update and a new blank IRS form PDF. The architecture's strict component separation (models → parser → calculator → filler) makes each stage independently testable, which is essential given the legal consequences of tax computation errors.

The primary risk profile consists of three categories: tax law errors (wrong worksheet selected for preferential capital gains rates, bracket tables confused or hardcoded), data precision errors (float arithmetic instead of Decimal), and PDF rendering errors (fields visible in Acrobat but blank when printed). All three categories are well-understood and entirely preventable by following documented patterns. The reference return from 2024 provides a concrete validation target for all computed values.

## Key Findings

### Recommended Stack

The stack is intentionally minimal. pypdf 6.7.5 (released March 2, 2026) is the only third-party dependency required for production use — it handles both AcroForm field name discovery and field filling. Python's stdlib covers all other needs: `decimal` for monetary arithmetic, `csv.DictReader` for parsing, `xml.etree.ElementTree` as a fallback XML parser. uv replaces pip + venv for dependency management and lockfile reproducibility. pytest covers unit testing of tax logic. No native libraries, no compilation, no admin rights, no external services.

**Core technologies:**
- Python 3.13.x: Runtime — current stable release, ships all required stdlib modules
- pypdf 6.7.5: AcroForm field discovery and PDF filling — actively maintained, pure Python, Windows-compatible
- decimal (stdlib): All monetary arithmetic — IRS rounding requires exact decimal, never float
- csv (stdlib): Brokerage CSV parsing — DictReader handles the multi-section Schwab format with section-aware scanning
- uv 0.5+: Virtualenv and lockfile management — ensures year-over-year reproducibility

**Avoid unconditionally:** PyPDF2/3/4 (deprecated), pdfrw (unmaintained, removed from Debian), float for any dollar amount.

### Expected Features

Every feature in v1 is required for a legally complete filing — there is no partial return. The MVP is the complete 2025 return. All income types (interest, ordinary dividends, qualified dividends, short-term capital gain, long-term capital gain) must be parsed, computed through their correct tax treatments, and written to four IRS AcroForms: Form 1041, Schedule D, Form 8949, and Form 8960.

**Must have (table stakes — required to file):**
- Parse 1099-DIV (Box 1a, 1b), 1099-INT (Box 1), 1099-B from brokerage CSV — all income inputs
- Form 8949: one short-term row (code A, $126.97 gain) and one long-term row (code D, $104,109.76 gain)
- Schedule D: net short-term gain (Line 7), net long-term gain (Line 16), all retained by trust (Lines 17-19)
- Schedule B: all lines $0 — required even for an accumulation trust making no distributions
- Form 1041 income section (Lines 1, 2a, 2b, 4, 9) and deduction/taxable income section (Lines 16-23)
- Schedule D Tax Worksheet: mandatory for trust with LTCG + qualified dividends (not the simple rate table)
- Form 8960 (NIIT): 3.8% on net investment income; AGI far exceeds $15,650 trust threshold
- Schedule G (Lines 1a, 2a, 9): total tax computation feeding Form 1041 Lines 24-27
- Parameterized tax brackets and AcroForm field names by year (config/YEAR.json)
- Combined print-ready output PDF

**Should have (add after v1 validation):**
- Stdout trace of all intermediate computed values before PDF fill — enables manual spot-check
- Prior-return field parity check — warn if 2024 filed return fields are absent from 2025 output
- Zero-validation for unsupported income types (Section 1250/1202, collectibles, foreign tax) — raise error if non-zero

**Defer (v2+):**
- Multiple brokerage account support — single account only for now
- Automated bracket/threshold updates from IRS published data — annual manual config update is acceptable

**Anti-features (do not build):**
- Schedule K-1 (no distributions), state returns, e-filing, AMT (Schedule I), Schedule J, charitable deduction (Schedule A), interactive UI, PDF form recreation

### Architecture Approach

The tool uses a strict four-module pipeline with a thin CLI orchestrator. Each module has a single responsibility and communicates only through typed dataclasses defined in `models.py`. The calculator is a pure function with no file I/O — tax logic is entirely decoupled from CSV parsing and PDF writing, making it unit-testable in isolation. Year-variable data (tax brackets, AcroForm field names, trust metadata) lives exclusively in `config/YEAR.json`, never hardcoded in Python. The flat module layout (not src/) is appropriate for this tool's size.

**Major components:**
1. `models.py` — `BrokerageData`, `TaxReturn`, and sub-dataclasses; imported by all other modules; no logic
2. `parser.py` — Section-aware CSV reader that locates 1099-DIV/INT/B sections by keyword sentinel, not row number; returns `BrokerageData`; XML fallback via stdlib ElementTree
3. `calculator.py` — Pure functions: `compute_schedule_d()`, `compute_schedule_g()`, `compute_return()`; accepts `BrokerageData` + config dict; returns `TaxReturn`; no file I/O
4. `filler.py` — Generic AcroForm filler; accepts `TaxReturn` + field map dict; uses pypdf `PdfWriter.update_page_form_field_values(auto_regenerate=False)`; sets NeedAppearances flag
5. `main.py` — CLI orchestrator; argparse (`--year`, `--csv`, `--form`, `--out`, `--dry-run`); calls components in sequence; surfaces errors with context
6. `config/YEAR.json` — Tax brackets, NIIT threshold, qualified dividends brackets, AcroForm field name mappings, trust metadata; one file per tax year

### Critical Pitfalls

1. **Wrong tax worksheet selected** — When a trust has LTCG and/or qualified dividends, the Schedule D Tax Worksheet is required, not the simple rate table and not the Qualified Dividends Tax Worksheet. Applying 37% to income eligible for 20% overstates tax materially. Implement explicit conditional worksheet selection with IRS source documented in code; unit test against the reference return.

2. **Float arithmetic for dollar amounts** — `float` cannot represent $0.10 exactly; errors accumulate and bracket boundary comparisons can flip. Use `decimal.Decimal` initialized from strings at parse time, throughout all computation. Never `Decimal(float_value)`. Set `decimal.getcontext().prec = 28` at module startup.

3. **PDF fields print blank (NeedAppearances bug)** — Fields appear filled in Acrobat but are invisible when printed or viewed in other readers. Set `auto_regenerate=False` in pypdf's `update_page_form_field_values()` and explicitly set `/NeedAppearances` in the AcroForm dictionary. Always validate output by printing to a non-Acrobat viewer, not just by opening in Acrobat.

4. **AcroForm field names not discovered from actual PDF** — IRS field names are machine-generated (`f1_01[0]`), not semantic, and can change year to year. Enumerate actual field names with `pypdf PdfReader.get_fields()` against each year's blank IRS PDF before writing any fill logic. Store in `config/YEAR.json`. Add a `--dump-fields` CLI flag for annual remapping.

5. **CSV parsed by row number instead of section keyword** — The Schwab CSV has multiple sections with different column counts; `pandas.read_csv()` on the full file fails. Parse by scanning for section header sentinels ("Form 1099DIV", "Form 1099B", "Description") and parse each section independently. Assert parsed totals match the brokerage's own summary row.

6. **Wash sale adjustments omitted from cost basis** — 1099-B includes a wash sale disallowed amount column that adjusts reported cost basis. Ignoring it produces incorrect Schedule D net gain. Always read and apply the wash sale adjustment column even when its value is $0.

7. **Wrong bracket thresholds used** — Ordinary income thresholds ($3,150 / $11,450 / $15,650) and capital gains thresholds ($3,250 / $15,900) are different and both change annually. Store as separate named arrays in config; source from IRS Rev. Proc. each year, not from prior code.

## Implications for Roadmap

Based on the strict dependency chain established by ARCHITECTURE.md and the feature ordering required by IRS instructions, the following phase structure is recommended. The chain is non-negotiable: Form 8949 feeds Schedule D, Schedule D feeds Form 1041 Line 4, Form 8960 feeds Schedule G — no phase can be reordered without breaking downstream computation.

### Phase 1: Foundation — Models and Config

**Rationale:** Everything else imports from `models.py`. Until `BrokerageData` and `TaxReturn` dataclasses are defined, neither the parser nor the calculator can be written or tested. The config skeleton (trust metadata + tax brackets) can be established now even though AcroForm field names are placeholders until Phase 4.
**Delivers:** `models.py` with all dataclasses; `config/2025.json` with trust metadata, 2025 ordinary income brackets, qualified dividends/LTCG brackets, and NIIT threshold. Project skeleton with uv, pytest, directory structure.
**Addresses:** Parameterized tax brackets (FEATURES.md P1), year-keyed config (ARCHITECTURE.md Config Layer)
**Avoids:** Hardcoded bracket values and field names in Python (Pitfalls 4 and 7)

### Phase 2: Input — CSV Parser

**Rationale:** The calculator can only be validated against real income data once the parser correctly extracts it from the Schwab CSV. Parser correctness gates all subsequent computation confidence.
**Delivers:** `parser.py` with section-aware keyword detection for 1099-DIV, 1099-INT, 1099-B sections; Decimal-from-string field reading; wash sale adjustment column handling; total assertion against brokerage summary rows; `tests/test_parser.py` validating 2025 known values (ordinary dividends $903.82, interest $0.12, LT gain $104,109.76, ST gain $126.97)
**Addresses:** CSV parsing (FEATURES.md P1), section-aware parsing (ARCHITECTURE.md Pattern 4)
**Avoids:** Row-number CSV parsing (Pitfall 5), float arithmetic (Pitfall 2), wash sale omission (Pitfall 6)

### Phase 3: Compute — Tax Calculator

**Rationale:** This is the highest-risk phase — all legal correctness lives here. It must be built before the PDF filler because incorrect values written to a PDF are worse than no PDF at all. The pure-function design means it can be fully validated against the 2024 reference return without any PDF involvement.
**Delivers:** `calculator.py` with `compute_schedule_d()`, `compute_8949()`, `compute_schedule_b()`, `compute_8960()`, `compute_qualified_dividends_tax_worksheet()`, `compute_schedule_g()`, `compute_return()`; `tests/test_calculator.py` validating all computed values against the 1041 Schedule G Calculator.xlsx reference for 2025 numbers; stdout intermediate value trace (Form 1041 lines, Schedule D totals, Schedule G totals, NIIT)
**Addresses:** All computation features (FEATURES.md P1): Form 8949, Schedule D, Schedule B, Schedule G, Form 8960, Qualified Dividends Tax Worksheet, parameterized brackets
**Avoids:** Wrong worksheet selection (Pitfall 1), float arithmetic (Pitfall 2), wrong bracket thresholds (Pitfall 7)

### Phase 4: Output — PDF Filler

**Rationale:** PDF filling is the final pipeline stage and depends on both correct `TaxReturn` values (Phase 3) and actual AcroForm field names discovered from the real IRS PDFs. The field name discovery step is a one-time manual step per year that must precede writing any fill logic.
**Delivers:** AcroForm field name enumeration from f1041.pdf, f1041sd.pdf, f8949.pdf, f8960.pdf using `pypdf PdfReader.get_fields()`; `config/2025.json` field_map populated with actual field names; `filler.py` generic AcroForm filler with NeedAppearances flag set and `auto_regenerate=False`; `tests/test_filler.py` verifying field values in output PDF; combined print-ready output PDF; `--dump-fields` CLI flag for annual remapping
**Addresses:** All PDF output features (FEATURES.md P1): filled Form 1041, Schedule D, Form 8949, Form 8960, combined print-ready output; prior-return field parity check (FEATURES.md P2)
**Avoids:** PDF fields printing blank (Pitfall 3), field names not discovered from actual PDF (Pitfall 4)

### Phase 5: CLI Orchestrator and Validation

**Rationale:** The orchestrator is the last thing to build because it is simply wiring — it has no logic of its own. Validation against the complete prior return (2024 filed 1041) confirms end-to-end correctness before the 2025 return is filed.
**Delivers:** `main.py` with argparse (`--year`, `--csv`, `--form`, `--out`, `--dry-run`, `--dump-fields`); full pipeline integration test; end-to-end validation against 2024 reference return for field parity; zero-validation for unsupported income types (Section 1250/1202, collectibles, foreign tax)
**Addresses:** One-command operation (FEATURES.md differentiator), prior-return field parity check (FEATURES.md P2), zero-validation for unsupported income types (FEATURES.md P2)
**Avoids:** Monolithic script anti-pattern (ARCHITECTURE.md Anti-Pattern 3)

### Phase Ordering Rationale

- **Models before everything:** `models.py` is imported by parser, calculator, and filler; circular import risk if any module defines its own types
- **Parser before calculator:** Tax computation confidence depends on validated real-data inputs; cannot confirm Schedule D totals without correctly parsed 1099-B rows
- **Calculator before filler:** A wrong value written to a PDF produces a wrong tax return; all computation must be validated independently before touching PDF output
- **Field name discovery gates filler:** AcroForm field names cannot be guessed or assumed from prior years; this manual one-time step per year blocks the filler phase
- **Orchestrator last:** It is pure wiring; building it before components are individually validated adds debugging complexity without benefit

### Research Flags

Phases with well-documented patterns (skip research-phase):
- **Phase 1 (Foundation):** Standard Python dataclasses and JSON config — no novel patterns
- **Phase 2 (CSV Parser):** Section-aware parsing is documented in ARCHITECTURE.md with implementation code; brokerage format inspected directly from actual CSV file
- **Phase 5 (CLI Orchestrator):** argparse is stdlib; wiring is straightforward

Phases that may benefit from deeper research during planning:
- **Phase 3 (Tax Calculator) — Schedule D Tax Worksheet:** The conditional worksheet selection logic (Schedule D Tax Worksheet vs. Qualified Dividends Tax Worksheet) requires careful implementation against IRS instructions for Schedule D. Recommend reading IRS Instructions for Schedule D (Form 1041) 2025 in full before implementing `compute_qualified_dividends_tax_worksheet()`. The 2024 reference return provides a concrete validation target.
- **Phase 4 (PDF Filler) — IRS AcroForm field names:** Field name discovery must be done against the actual 2025 IRS PDF downloads (f1041.pdf, f1041sd.pdf, f8949.pdf, f8960.pdf) before implementation. STACK.md documents the XFA risk: if the 2025 Form 1041 uses XFA instead of AcroForms, the entire PDF filling approach changes. Verify AcroForm type before starting Phase 4.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | pypdf 6.7.5 verified against official docs (March 2, 2026 release); uv, pytest, stdlib — all official sources. No ambiguity. |
| Features | HIGH | IRS official instructions for Form 1041, Schedule D, Form 8949, Form 8960 (2025) are the primary source. Actual 2025 brokerage CSV values verified. |
| Architecture | HIGH | Architecture derived from direct inspection of the actual 2025/XXXX-X123.CSV format plus pypdf official documentation. Dataclass designs match actual income structure. |
| Pitfalls | HIGH | Tax law pitfalls verified against IRS official instructions. PDF pitfalls verified against pypdf official docs and GitHub issues. CSV pitfalls verified against multiple community sources and the actual brokerage file. |

**Overall confidence:** HIGH

### Gaps to Address

- **AcroForm field names for 2025 forms:** Field names in `config/2025.json` are placeholder examples only (e.g., `f1_01[0]`) and must be replaced with actual names discovered by running `pypdf PdfReader.get_fields()` against the four downloaded IRS PDF files. This is the only unknown that blocks implementation — it cannot be resolved until the 2025 IRS PDFs are in the `forms/` directory.
- **XFA vs. AcroForm verification:** STACK.md documents that some IRS PDFs use XFA forms (incompatible with pypdf). Must verify the 2025 Form 1041 is AcroForm on first run with `python -m pypdf show f1041.pdf --fields`. If XFA is detected, the PDF filling approach requires a substantially different tool (pdfjinja or XFA XML manipulation).
- **Schedule D Tax Worksheet vs. Qualified Dividends Tax Worksheet exact implementation:** The conditional selection rules are documented in PITFALLS.md, but the worksheet itself has ~22 lines of conditional arithmetic. Recommend a line-by-line implementation review against IRS instructions for Schedule D (Form 1041) 2025 during Phase 3 planning.
- **2025 IRS form PDF availability:** The 2025 Form 1041 blank PDFs may not yet be finalized by the IRS at the time of implementation (IRS typically publishes final forms in January of the filing year). If the forms are draft versions, field names may change before the final release.

## Sources

### Primary (HIGH confidence)
- IRS Instructions for Form 1041 and Schedules A, B, G, J, K-1 (2025) — https://www.irs.gov/instructions/i1041 — bracket thresholds, worksheet selection, Schedule G rules
- IRS Instructions for Schedule D (Form 1041) (2025) — https://www.irs.gov/instructions/i1041sd — Schedule D Tax Worksheet trigger conditions and line-by-line instructions
- IRS Instructions for Form 8949 (2025) — https://www.irs.gov/instructions/i8949 — short-term/long-term classification, Form 8949 codes A and D
- IRS Instructions for Form 8960 (2025) — https://www.irs.gov/instructions/i8960 — NIIT computation, trust threshold ($15,650)
- pypdf 6.7.5 documentation — https://pypdf.readthedocs.io/en/stable/user/forms.html — AcroForm field enumeration, PdfWriter.update_page_form_field_values, NeedAppearances
- pypdf 6.7.5 PyPI release page — https://pypi.org/project/pypdf/ — version verified March 2, 2026
- Python decimal module documentation — https://docs.python.org/3/library/decimal.html — ROUND_HALF_UP, Decimal initialization from strings
- uv documentation — https://docs.astral.sh/uv/ — Windows install, lockfile behavior
- 2025/XXXX-X123.CSV — direct inspection of actual brokerage CSV — confirmed section structure, column names, transaction values

### Secondary (MEDIUM confidence)
- pypdf Issue #355: Updated PDF fields don't show up when page is written — NeedAppearances root cause
- pypdf Issue #545: Filling forms with dots in field names — hierarchical field name gotchas
- West Health Data Science Blog: Exploring fillable forms with PDFrw — pdfrw NeedAppearances pattern (corroborates pypdf approach)
- 2025 Trust Tax Rates and Deductions — Ardent Trust — https://www.ardentrust.com/insights/trust-tax-rates-deductions — bracket values (corroborated by IRS instructions)

### Tertiary (MEDIUM confidence — needs annual reverification)
- IRS Revenue Procedure for 2025 tax year thresholds — bracket values sourced via IRS instructions; should be re-verified each year from IRS Rev. Proc. when config/YEAR.json is created for a new tax year

---
*Research completed: 2026-03-08*
*Ready for roadmap: yes*
