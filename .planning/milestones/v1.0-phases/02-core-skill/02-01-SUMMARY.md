---
phase: 02-core-skill
plan: "01"
subsystem: tax-forms
tags: [pypdf, acroform, irs-forms, csv-parsing, argparse]

requires:
  - phase: 01-foundation
    provides: fill_pdf.py CLI, config/2025.json brackets/paths, forms/f1041.pdf with cataloged fields

provides:
  - Three IRS AcroForm PDFs in forms/ (f1041sd.pdf 108 fields, f8960.pdf 41 fields, f8949.pdf 229 fields)
  - config/2025_fields.json with real field IDs for schedule_d, form_8960, and new form_8949 section
  - fill_1041.py skeleton with argparse CLI, CSV parser, and --dry-run mode

affects:
  - 02-02 (computation engine reads fields catalog and calls fill_pdf.py for all three forms)
  - 02-03 (PDF fill phase uses form_8949 field IDs and row-by-row transaction data)

tech-stack:
  added: [pypdf (PdfReader.get_fields for field enumeration)]
  patterns:
    - State-machine CSV parser with section detection and header-row skipping
    - Config-driven arg defaults (config/2025.json paths section feeds argparse defaults)
    - Two-header-row skip for 1099-B section (field-number row + column-name row)

key-files:
  created:
    - forms/f1041sd.pdf
    - forms/f8960.pdf
    - forms/f8949.pdf
    - fill_1041.py
  modified:
    - config/2025_fields.json

key-decisions:
  - "1099-B section has two header rows to skip before data rows: field-number row (1a/1b/1c...) and column-name row (Description of property/Date acquired...)"
  - "schedule_d field mapping: short_term_proceeds=f1_19, net_short_term_gain_loss=f1_22, long_term_proceeds=f1_39, net_long_term_gain_loss=f1_42, net_capital_gain=Part3/Line19/f2_15"
  - "form_8960 field mapping: interest=f1_3, dividends=f1_4, net_gain_dispositions=f1_9, total_NII=f1_14, undistributed_NI=f1_16, threshold=f1_17, agi_minus_threshold=f1_18, lesser=f1_19, niit_amount=f1_35"
  - "form_8949 row pattern: each row is 8 cols (description/date_acq/date_sold/proceeds/cost/code/wash_sale/gain_loss); 11 rows per page; Page1=Part I short-term, Page2=Part II long-term"

patterns-established:
  - "CSV parser: state machine with section = None | DIV | INT | B; blank rows reset section"
  - "parse_dollar(): strip outer quotes then $, comma; return 0.0 for empty"

requirements-completed: [PARSE-01, PARSE-02, PARSE-03, CALC-01, SKILL-04]

duration: 5min
completed: 2026-03-08
---

# Phase 2 Plan 01: IRS PDF Download, Field Catalog Extension, and CSV Parser Summary

**Three IRS AcroForm PDFs downloaded and cataloged (108/41/229 fields), config/2025_fields.json extended with real field IDs for Schedule D, Form 8960, and Form 8949, and fill_1041.py skeleton parsing CSV to $903.82 dividends, $0.12 interest, 2 transactions in --dry-run mode**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-08T20:43:53Z
- **Completed:** 2026-03-08T20:49:38Z
- **Tasks:** 2 of 2 executed (checkpoint reached at Task 3)
- **Files modified:** 5

## Accomplishments

- Downloaded f1041sd.pdf (108 AcroForm fields), f8960.pdf (41 fields), f8949.pdf (229 fields) from IRS.gov
- Extended config/2025_fields.json: replaced all null field IDs in schedule_d and form_8960 sections, added complete form_8949 section with all row/column field IDs for both Part I and Part II
- Created fill_1041.py with argparse, config-driven defaults, state-machine CSV parser that correctly handles 1099-DIV/INT/B sections including two-header-row skip for 1099-B

## Task Commits

1. **Task 1: Download IRS PDFs and extend field catalog** - `3431428` (feat)
2. **Task 2: Create fill_1041.py with arg parsing and CSV parser** - `0fb3547` (feat)
3. **Fix: Remove dead b_col_headers_seen variable and unused subprocess import** - `10d0d49` (fix)

## Files Created/Modified

- `forms/f1041sd.pdf` - Blank Schedule D (Form 1041) AcroForm PDF, 108 fields
- `forms/f8960.pdf` - Blank Form 8960 (Net Investment Income Tax) AcroForm PDF, 41 fields
- `forms/f8949.pdf` - Blank Form 8949 (Sales and Dispositions) AcroForm PDF, 229 fields
- `config/2025_fields.json` - Extended with real field IDs for schedule_d, form_8960, new form_8949 section
- `fill_1041.py` - Skill script with argparse, config loading, CSV parser, dry-run mode

## Decisions Made

- 1099-B section has two header rows to skip (field-number row "1a/1b/1c..." followed by column-name row "Description of property/Date acquired...") — discovered during implementation when parser produced 3 transactions instead of 2
- Schedule D key field mappings confirmed from actual PDF: short_term summary row = f1_19-f1_22 (Part I Line 7); long_term summary row = f1_39-f1_42 (Part II Line 15); net_capital_gain = Table_Part3/Line19/f2_15
- Form 8960 field mapping: 35 sequential text fields; Line 1-8 = f1_3 through f1_14; Part II for trusts = f1_16-f1_19; Line 21 (NIIT) = f1_35
- Form 8949 has 6 checkboxes per page (not 3) — c1_1[0..5] on Page 1, c2_1[0..5] on Page 2; Box A/D = covered short/long term at index [0]

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed 1099-B parser emitting 3 transactions instead of 2**
- **Found during:** Task 2 (create fill_1041.py) — first dry-run attempt
- **Issue:** CSV 1099-B section has two header rows (field-number row + column-name row); original code only skipped one, causing the column-name row to be parsed as a transaction with term "short-term gain loss long-term gain or loss ordinary"
- **Fix:** Changed `b_col_headers_seen` boolean flag to `b_col_headers_count` integer, skipping rows until count >= 2
- **Files modified:** fill_1041.py
- **Verification:** `python fill_1041.py --dry-run` outputs exactly 2 transactions (long-term code D, short-term code A)
- **Committed in:** `0fb3547` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Fix required for correctness. Single-line counter change. No scope creep.

## Issues Encountered

None beyond the auto-fixed parser bug above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for Plan 02 (tax computation engine): all field IDs are real, fill_pdf.py interface is unchanged, CSV parser delivers correctly structured data
- Human verification checkpoint passed: field catalog confirmed correct, PDFs present in forms/, dry-run output matches expected values
- Concern: Schedule D Part III/IV field mappings are documented by position; verify against physical form before committing to fill logic in Plan 02

---

*Phase: 02-core-skill*
*Completed: 2026-03-08*
