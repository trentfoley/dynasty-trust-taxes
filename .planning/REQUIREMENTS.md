# Requirements: Dynasty Trust Tax Form Filler

**Defined:** 2026-03-08
**Core Value:** Given a brokerage year-end CSV and a blank Form 1041 PDF, produce a complete, filled, print-ready Form 1041 in one Claude skill invocation.

## v1 Requirements

### Input Parsing

- [x] **PARSE-01**: Skill parses 1099-DIV section from brokerage CSV — extracts ordinary dividends (Box 1a) and qualified dividends (Box 1b)
- [x] **PARSE-02**: Skill parses 1099-INT section from brokerage CSV — extracts interest income (Box 1)
- [x] **PARSE-03**: Skill parses 1099-B section from brokerage CSV — extracts each capital transaction row with: description, date acquired, date sold, proceeds, cost basis, wash sale loss disallowed, and short/long-term flag

### Tax Computation

- [x] **CALC-01**: Skill computes Form 8949 rows — assigns Box A (short-term covered) or Box D (long-term covered) based on transaction flags and calculates gain/loss per transaction
- [x] **CALC-02**: Skill computes Schedule D — net short-term capital gain/loss (Part I) and net long-term capital gain/loss (Part II) from Form 8949 rows
- [x] **CALC-03**: Skill computes taxable income — gross income minus $100 complex trust exemption (Line 20)
- [x] **CALC-04**: Skill computes Schedule G tax using the Qualified Dividends and Capital Gains Tax Worksheet — required because trust has both qualified dividends and net long-term capital gains
- [x] **CALC-05**: Skill computes Form 8960 Net Investment Income Tax — 3.8% of lesser of (net investment income, AGI minus $15,650 threshold)
- [x] **CALC-06**: All tax bracket thresholds and rates are stored in `config/YEAR.json` — no bracket values hardcoded in any skill or script
- [x] **CALC-07**: Schedule B is computed (zero distribution deduction) and included in output — required on complex trust returns even when $0

### PDF Infrastructure (Phase 1)

- [x] **PDF-01**: AcroForm field names are discovered from blank `forms/f1041.pdf` via `pypdf PdfReader.get_fields()` and stored in `config/YEAR_fields.json`
- [x] **PDF-FILLER**: `fill_pdf.py` accepts `--fields <json>` and `--form <blank_pdf>` and writes a filled PDF with `NeedAppearances` set — this script is the only maintained Python artifact

### PDF Output (Phase 2)

- [x] **PDF-02**: Skill fills all Form 1041 page 1 fields that were populated on the 2024 reference return — income lines, deduction lines, exemption, taxable income, tax due
- [x] **PDF-03**: Skill fills Schedule D (Form 1041) fields — short-term and long-term transaction detail and summary lines
- [x] **PDF-04**: Skill fills Schedule G fields — tax computation lines
- [x] **PDF-05**: Skill fills Form 8960 fields — net investment income and NIIT amount
- [x] **PDF-06**: Output PDF has `NeedAppearances` flag set (handled by fill_pdf.py) so filled fields are visible in any PDF viewer
- [x] **PDF-07**: Filled PDF is written to `output/YEAR_1041_filled.pdf`

### Skill Invocation

- [x] **SKILL-01**: Skill is invocable via a single Claude skill command (e.g., `/fill-1041`) with optional year argument — defaults to current year config
- [x] **SKILL-02**: Skill supports dry-run mode — outputs all computed field values without calling `fill_pdf.py` or writing any file
- [x] **SKILL-03**: Skill validates computed income totals against CSV source data and surfaces any mismatch before producing PDF output
- [x] **SKILL-04**: All file paths (CSV input, blank form PDF, output PDF) use sensible defaults from `config/YEAR.json` and can be overridden

## v1.1 Bug Fixes (Phase 3)

- [x] **FIX-01**: Form 8960 Line 19a uses Form 1041 Line 17 (gross income), not Line 23 (taxable income)
- [x] **FIX-02**: Schedule B Line 6 is populated with the negative capital gain; Line 7 (DNI) is computed correctly
- [x] **FIX-03**: Line 14 attorney/accountant fees are config-driven via `deductions.attorney_accountant_fees` in `config/YEAR.json`

## v1.2 Multi-Trust Support (Phase 4)

### Multi-Trust CLI & Config

- [x] **MULTI-01**: `fill_1041.py` accepts a required `--trust` flag (choices: trent, chris) that selects the per-trust config file `config/{year}_{trust}.json`
- [x] **MULTI-02**: Per-trust config files exist (`config/2025_trent.json`, `config/2025_chris.json`) with trust-specific identity, address, fees, and paths; brackets/thresholds duplicated (same tax year)
- [x] **MULTI-03**: Chris's 1099-DIV data is available as a manually-created CSV (`2025_chris/dividends.csv`) compatible with the existing `parse_csv()` state machine

### Tax Computation Fix

- [x] **MULTI-04**: `compute_schedule_g()` caps preferential income at taxable income, producing correct tax when qualified dividends exceed taxable income (Chris: $779.35, not $824.41)

### Conditional Form Generation

- [x] **MULTI-05**: Forms are generated conditionally — Schedule D and Form 8949 only when capital transactions exist; Form 8960 only when income exceeds NIIT threshold; Form 1041 always generated
- [x] **MULTI-06**: Output PDFs are organized in per-trust subdirectories (`output/trent/`, `output/chris/`) with filenames retaining the full trust name pattern
- [x] **MULTI-07**: Trent's tax computation and output are unchanged after the multi-trust refactor (regression: total tax = $23,120.87)

## v2 Requirements

### Enhanced Validation

- **VAL-01**: Cross-check computed tax against Schedule G Excel calculator outputs for the same inputs
- **VAL-02**: Compare filled PDF field values against prior year return to flag unexpected changes

### XML Parsing

- **XML-01**: Parse `XXXX-X123.XML` as alternative input source when CSV is not available

## Out of Scope

| Feature | Reason |
|---------|--------|
| Schedule K-1 / beneficiary distributions | Trust accumulates all income — no distributions |
| State tax returns | Federal Form 1041 only |
| E-filing | Output is print-and-mail only |
| GUI / web interface | Skill invocation is sufficient for annual use |
| AMT (Schedule I) | Trust has no preference items |
| Accumulation distribution throwback (Schedule J) | Trust created after 3/1/1984 |
| Foreign tax credit | No foreign tax paid in brokerage data |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CALC-06 | Phase 1 | Complete |
| PDF-01 | Phase 1 | Complete |
| PDF-FILLER | Phase 1 | Complete |
| PARSE-01 | Phase 2 | Complete |
| PARSE-02 | Phase 2 | Complete |
| PARSE-03 | Phase 2 | Complete |
| CALC-01 | Phase 2 | Complete |
| CALC-02 | Phase 2 | Complete |
| CALC-03 | Phase 2 | Complete |
| CALC-04 | Phase 2 | Complete |
| CALC-05 | Phase 2 | Complete |
| CALC-07 | Phase 2 | Complete |
| PDF-02 | Phase 2 | Complete |
| PDF-03 | Phase 2 | Complete |
| PDF-04 | Phase 2 | Complete |
| PDF-05 | Phase 2 | Complete |
| PDF-06 | Phase 2 | Complete |
| PDF-07 | Phase 2 | Complete |
| SKILL-01 | Phase 2 | Complete |
| SKILL-02 | Phase 2 | Complete |
| SKILL-03 | Phase 2 | Complete |
| SKILL-04 | Phase 2 | Complete |
| FIX-01 | Phase 3 | Complete |
| FIX-02 | Phase 3 | Complete |
| FIX-03 | Phase 3 | Complete |
| MULTI-01 | Phase 4 | Planned |
| MULTI-02 | Phase 4 | Planned |
| MULTI-03 | Phase 4 | Planned |
| MULTI-04 | Phase 4 | Planned |
| MULTI-05 | Phase 4 | Planned |
| MULTI-06 | Phase 4 | Planned |
| MULTI-07 | Phase 4 | Planned |

**Coverage:**
- v1 requirements: 22 total, v1.1 fixes: 3 total, v1.2 multi-trust: 7 total
- Mapped to phases: 32
- Unmapped: 0

---
*Requirements defined: 2026-03-08*
*Last updated: 2026-03-08 — revised for Claude skill approach; 5-phase Python pipeline replaced with 2-phase skill build*
*Updated: 2026-03-14 — added v1.2 multi-trust requirements (MULTI-01 through MULTI-07) for Phase 4*
