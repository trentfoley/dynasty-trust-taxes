# Requirements: Dynasty Trust Tax Form Filler

**Defined:** 2026-03-08
**Core Value:** Given a brokerage year-end CSV and a blank Form 1041 PDF, produce a complete, filled, print-ready Form 1041 in one Claude skill invocation.

## v1 Requirements

### Input Parsing

- [ ] **PARSE-01**: Skill parses 1099-DIV section from brokerage CSV — extracts ordinary dividends (Box 1a) and qualified dividends (Box 1b)
- [ ] **PARSE-02**: Skill parses 1099-INT section from brokerage CSV — extracts interest income (Box 1)
- [ ] **PARSE-03**: Skill parses 1099-B section from brokerage CSV — extracts each capital transaction row with: description, date acquired, date sold, proceeds, cost basis, wash sale loss disallowed, and short/long-term flag

### Tax Computation

- [ ] **CALC-01**: Skill computes Form 8949 rows — assigns Box A (short-term covered) or Box D (long-term covered) based on transaction flags and calculates gain/loss per transaction
- [ ] **CALC-02**: Skill computes Schedule D — net short-term capital gain/loss (Part I) and net long-term capital gain/loss (Part II) from Form 8949 rows
- [ ] **CALC-03**: Skill computes taxable income — gross income minus $100 complex trust exemption (Line 20)
- [ ] **CALC-04**: Skill computes Schedule G tax using the Qualified Dividends and Capital Gains Tax Worksheet — required because trust has both qualified dividends and net long-term capital gains
- [ ] **CALC-05**: Skill computes Form 8960 Net Investment Income Tax — 3.8% of lesser of (net investment income, AGI minus $15,650 threshold)
- [x] **CALC-06**: All tax bracket thresholds and rates are stored in `config/YEAR.json` — no bracket values hardcoded in any skill or script
- [ ] **CALC-07**: Schedule B is computed (zero distribution deduction) and included in output — required on complex trust returns even when $0

### PDF Infrastructure (Phase 1)

- [ ] **PDF-01**: AcroForm field names are discovered from blank `forms/f1041.pdf` via `pypdf PdfReader.get_fields()` and stored in `config/YEAR_fields.json`
- [x] **PDF-FILLER**: `fill_pdf.py` accepts `--fields <json>` and `--form <blank_pdf>` and writes a filled PDF with `NeedAppearances` set — this script is the only maintained Python artifact

### PDF Output (Phase 2)

- [ ] **PDF-02**: Skill fills all Form 1041 page 1 fields that were populated on the 2024 reference return — income lines, deduction lines, exemption, taxable income, tax due
- [ ] **PDF-03**: Skill fills Schedule D (Form 1041) fields — short-term and long-term transaction detail and summary lines
- [ ] **PDF-04**: Skill fills Schedule G fields — tax computation lines
- [ ] **PDF-05**: Skill fills Form 8960 fields — net investment income and NIIT amount
- [ ] **PDF-06**: Output PDF has `NeedAppearances` flag set (handled by fill_pdf.py) so filled fields are visible in any PDF viewer
- [ ] **PDF-07**: Filled PDF is written to `output/YEAR_1041_filled.pdf`

### Skill Invocation

- [ ] **SKILL-01**: Skill is invocable via a single Claude skill command (e.g., `/fill-1041`) with optional year argument — defaults to current year config
- [ ] **SKILL-02**: Skill supports dry-run mode — outputs all computed field values without calling `fill_pdf.py` or writing any file
- [ ] **SKILL-03**: Skill validates computed income totals against CSV source data and surfaces any mismatch before producing PDF output
- [ ] **SKILL-04**: All file paths (CSV input, blank form PDF, output PDF) use sensible defaults from `config/YEAR.json` and can be overridden

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
| PDF-01 | Phase 1 | Pending |
| PDF-FILLER | Phase 1 | Complete |
| PARSE-01 | Phase 2 | Pending |
| PARSE-02 | Phase 2 | Pending |
| PARSE-03 | Phase 2 | Pending |
| CALC-01 | Phase 2 | Pending |
| CALC-02 | Phase 2 | Pending |
| CALC-03 | Phase 2 | Pending |
| CALC-04 | Phase 2 | Pending |
| CALC-05 | Phase 2 | Pending |
| CALC-07 | Phase 2 | Pending |
| PDF-02 | Phase 2 | Pending |
| PDF-03 | Phase 2 | Pending |
| PDF-04 | Phase 2 | Pending |
| PDF-05 | Phase 2 | Pending |
| PDF-06 | Phase 2 | Pending |
| PDF-07 | Phase 2 | Pending |
| SKILL-01 | Phase 2 | Pending |
| SKILL-02 | Phase 2 | Pending |
| SKILL-03 | Phase 2 | Pending |
| SKILL-04 | Phase 2 | Pending |

**Coverage:**
- v1 requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-08*
*Last updated: 2026-03-08 — revised for Claude skill approach; 5-phase Python pipeline replaced with 2-phase skill build*
