# Roadmap: Dynasty Trust Tax Form Filler

## Overview

A five-phase pipeline build: foundation and config first, then CSV parsing, then tax computation, then PDF filling, then CLI orchestration. Each phase delivers one independently testable component. No phase can be reordered — the calculator cannot run without the parser, the filler cannot run without correct computed values. The result is a single command that reads a brokerage CSV and produces a print-ready Form 1041 PDF.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation** - Project skeleton, data models, and parameterized tax bracket config
- [ ] **Phase 2: CSV Parser** - Section-aware brokerage CSV parsing to typed income data
- [ ] **Phase 3: Tax Calculator** - Pure-function computation of all 1041 schedules and worksheets
- [ ] **Phase 4: PDF Filler** - AcroForm field discovery and filled print-ready output PDF
- [ ] **Phase 5: CLI Orchestrator** - Single-command wiring, dry-run, and validation

## Phase Details

### Phase 1: Foundation
**Goal**: Project structure is established and all data contracts are defined so every downstream module can be written and tested
**Depends on**: Nothing (first phase)
**Requirements**: CALC-06
**Success Criteria** (what must be TRUE):
  1. `python -m pytest` runs and exits 0 against an empty test suite (project skeleton is valid)
  2. `models.py` defines `BrokerageData` and `TaxReturn` dataclasses importable by any module with no circular imports
  3. `config/2025.json` exists and contains 2025 ordinary income brackets, capital gains brackets, NIIT threshold, and trust metadata — no bracket values appear anywhere in Python source files
  4. Running `python -c "from models import BrokerageData, TaxReturn"` succeeds without error
**Plans**: TBD

### Phase 2: CSV Parser
**Goal**: The brokerage CSV is fully parsed into typed Decimal income values that match the known 2025 actuals, gating all tax computation
**Depends on**: Phase 1
**Requirements**: PARSE-01, PARSE-02, PARSE-03, PARSE-04
**Success Criteria** (what must be TRUE):
  1. `parser.py` extracts ordinary dividends = $903.82 and qualified dividends = $903.82 from the 2025 CSV
  2. `parser.py` extracts interest income = $0.12 from the 2025 CSV
  3. `parser.py` extracts all 1099-B rows including description, dates, proceeds, cost basis, wash sale adjustment, and short/long-term flag — with net long-term gain summing to ~$104,109.76 and net short-term gain to ~$126.97
  4. All extracted dollar values are `decimal.Decimal` instances — `type(result.ordinary_dividends) is Decimal` passes in tests
  5. `pytest tests/test_parser.py` passes with assertions against all four known 2025 income values
**Plans**: TBD

### Phase 3: Tax Calculator
**Goal**: All tax schedules are computed correctly using the right IRS worksheets, validated against the reference return, before any PDF is touched
**Depends on**: Phase 2
**Requirements**: CALC-01, CALC-02, CALC-03, CALC-04, CALC-05, CALC-07
**Success Criteria** (what must be TRUE):
  1. `calculator.py` produces Form 8949 rows with correct Box A (short-term) and Box D (long-term) assignments and per-transaction gain/loss matching the 2025 CSV transactions
  2. Schedule D net short-term gain and net long-term gain match the values on the 2024 reference return (adjusted for 2025 data)
  3. Schedule G tax is computed via the Qualified Dividends and Capital Gains Tax Worksheet (not the simple rate table) — the worksheet is selected conditionally and documented in code with IRS instruction citation
  4. Form 8960 NIIT equals 3.8% applied to the lesser of net investment income and (AGI minus $15,650)
  5. `pytest tests/test_calculator.py` passes with all schedule totals asserted against known-correct expected values derived from the Schedule G Calculator.xlsx reference
**Plans**: TBD

### Phase 4: PDF Filler
**Goal**: A print-ready PDF is produced with all Form 1041, Schedule D, Form 8949, and Form 8960 fields visibly filled in any PDF viewer
**Depends on**: Phase 3
**Requirements**: PDF-01, PDF-02, PDF-03, PDF-04, PDF-05, PDF-06, PDF-07
**Success Criteria** (what must be TRUE):
  1. `config/2025_fields.json` contains actual AcroForm field names discovered from `forms/f1041.pdf` via `pypdf PdfReader.get_fields()` — no placeholder names remain
  2. `output/2025_1041_filled.pdf` is written and all filled fields are visible when opened in a non-Acrobat PDF viewer (e.g., a browser PDF renderer)
  3. Every field populated on the 2024 reference return has a corresponding filled value in the 2025 output PDF
  4. Printing the output PDF to any printer produces legible field values — NeedAppearances flag is confirmed set in the AcroForm dictionary
**Plans**: TBD

### Phase 5: CLI Orchestrator
**Goal**: The entire pipeline runs in a single command with configurable paths, dry-run output, and income validation that prevents a wrong return from being filed
**Depends on**: Phase 4
**Requirements**: CLI-01, CLI-02, CLI-03, CLI-04
**Success Criteria** (what must be TRUE):
  1. `python fill_1041.py --year 2025` runs end-to-end from the project root and writes `output/2025_1041_filled.pdf` without error
  2. `python fill_1041.py --year 2025 --dry-run` prints all computed field values to stdout and writes no files
  3. When CSV income totals do not match computed totals, the tool exits with a non-zero status and a human-readable error message identifying the mismatch before writing any PDF
  4. All file paths (CSV input, blank form PDF, output PDF) can be overridden via command-line arguments and the tool uses those overrides correctly
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 0/TBD | Not started | - |
| 2. CSV Parser | 0/TBD | Not started | - |
| 3. Tax Calculator | 0/TBD | Not started | - |
| 4. PDF Filler | 0/TBD | Not started | - |
| 5. CLI Orchestrator | 0/TBD | Not started | - |

---
*Created: 2026-03-08*
