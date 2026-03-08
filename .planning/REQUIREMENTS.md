# Requirements: Dynasty Trust Tax Form Filler

**Defined:** 2026-03-08
**Core Value:** Given a brokerage year-end CSV and a blank Form 1041 PDF, produce a complete, filled, print-ready Form 1041 in one command.

## v1 Requirements

### Input Parsing

- [ ] **PARSE-01**: Tool parses 1099-DIV section from brokerage CSV — extracts ordinary dividends (Box 1a) and qualified dividends (Box 1b) as Decimal values
- [ ] **PARSE-02**: Tool parses 1099-INT section from brokerage CSV — extracts interest income (Box 1) as Decimal value
- [ ] **PARSE-03**: Tool parses 1099-B section from brokerage CSV — extracts each capital transaction row with: description, date acquired, date sold, proceeds, cost basis, wash sale loss disallowed, short/long-term flag, and Form 8949 code
- [ ] **PARSE-04**: All dollar amounts are parsed as `decimal.Decimal` directly from CSV string values — no float intermediaries at any point

### Tax Computation

- [ ] **CALC-01**: Tool computes Form 8949 rows — assigns Box A (short-term covered) or Box D (long-term covered) based on transaction flags and calculates gain/loss per transaction
- [ ] **CALC-02**: Tool computes Schedule D — net short-term capital gain/loss (Part I) and net long-term capital gain/loss (Part II) from Form 8949 rows
- [ ] **CALC-03**: Tool computes taxable income — gross income minus $100 complex trust exemption (Line 20)
- [ ] **CALC-04**: Tool computes Schedule G tax using the Qualified Dividends and Capital Gains Tax Worksheet — required because trust has both qualified dividends and net long-term capital gains
- [ ] **CALC-05**: Tool computes Form 8960 Net Investment Income Tax — 3.8% of lesser of (net investment income, AGI minus $15,650 threshold)
- [ ] **CALC-06**: All tax bracket thresholds and rates are stored in `config/YEAR.json` — no bracket values hardcoded in Python source
- [ ] **CALC-07**: Schedule B is computed (zero distribution deduction) and included in output — required on complex trust returns even when $0

### PDF Output

- [ ] **PDF-01**: Tool discovers AcroForm field names from blank `forms/f1041.pdf` via pypdf `get_fields()` — field names stored in `config/YEAR_fields.json`
- [ ] **PDF-02**: Tool fills all Form 1041 page 1 fields that were populated on the 2024 reference return — income lines, deduction lines, exemption, taxable income, tax due
- [ ] **PDF-03**: Tool fills Schedule D (Form 1041) fields — short-term and long-term transaction detail and summary lines
- [ ] **PDF-04**: Tool fills Schedule G fields — tax computation lines
- [ ] **PDF-05**: Tool fills Form 8960 fields — net investment income and NIIT amount
- [ ] **PDF-06**: Output PDF has `NeedAppearances` flag set so filled fields are visible when printed in any PDF viewer (not just Adobe Acrobat)
- [ ] **PDF-07**: Filled PDF is written to `output/YEAR_1041_filled.pdf`

### CLI / Orchestration

- [ ] **CLI-01**: Tool runs via single command `python fill_1041.py --year 2025` from the project root
- [ ] **CLI-02**: Tool supports `--dry-run` flag — prints all computed field values to stdout without writing any PDF
- [ ] **CLI-03**: Tool validates that computed income totals match CSV source data before proceeding to PDF fill — exits with clear error if mismatch
- [ ] **CLI-04**: All file paths (CSV input, blank form, output PDF) are configurable via command-line arguments with sensible defaults

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
| GUI / web interface | CLI is sufficient for annual use |
| AMT (Schedule I) | Trust has no preference items |
| Accumulation distribution throwback (Schedule J) | Trust created after 3/1/1984 |
| Foreign tax credit | No foreign tax paid in brokerage data |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PARSE-01 | Phase 2 | Pending |
| PARSE-02 | Phase 2 | Pending |
| PARSE-03 | Phase 2 | Pending |
| PARSE-04 | Phase 2 | Pending |
| CALC-01 | Phase 3 | Pending |
| CALC-02 | Phase 3 | Pending |
| CALC-03 | Phase 3 | Pending |
| CALC-04 | Phase 3 | Pending |
| CALC-05 | Phase 3 | Pending |
| CALC-06 | Phase 1 | Pending |
| CALC-07 | Phase 3 | Pending |
| PDF-01 | Phase 4 | Pending |
| PDF-02 | Phase 4 | Pending |
| PDF-03 | Phase 4 | Pending |
| PDF-04 | Phase 4 | Pending |
| PDF-05 | Phase 4 | Pending |
| PDF-06 | Phase 4 | Pending |
| PDF-07 | Phase 4 | Pending |
| CLI-01 | Phase 5 | Pending |
| CLI-02 | Phase 5 | Pending |
| CLI-03 | Phase 5 | Pending |
| CLI-04 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-08*
*Last updated: 2026-03-08 after initial definition*
