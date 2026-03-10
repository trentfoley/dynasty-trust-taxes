---
phase: 03-correct-issues-found-during-external-review
plan: 01
subsystem: tax-computation
tags: [form-1041, form-8960, schedule-b, niit, dni, python]

# Dependency graph
requires:
  - phase: 02-core-skill
    provides: fill_1041.py with all four forms computed and filled
provides:
  - Form 8960 Line 19a correctly uses gross income ($105,140.67) not taxable income
  - Schedule B Line 6 capital gains subtraction (-$104,236.73) and corrected DNI ($903.94)
  - Config-driven attorney/accountant fee deduction support via config/2025.json
affects: [any future phase that computes NIIT, DNI, or Form 1041 deductions]

# Tech tracking
tech-stack:
  added: []
  patterns: [config-driven deductions via cfg.get("deductions", {}), Schedule B DNI = total_income - capital_gains_retained_in_corpus]

key-files:
  created: []
  modified:
    - config/2025.json
    - fill_1041.py

key-decisions:
  - "Form 8960 Line 19a for trusts = Form 1041 Line 17 (gross/adjusted total income), NOT Line 23 (taxable income) — $100 exemption must not be subtracted before NIIT calculation"
  - "Schedule B DNI excludes capital gains retained in corpus per IRS instructions — Line 6 = negative capital gain, Line 7 = ordinary income only"
  - "Attorney/accountant fees read from config deductions.attorney_accountant_fees — not hardcoded; zero for 2025 so taxable_income unchanged"
  - "Form 8960 NII deduction for attorney fees deferred (Lines 9a-9c) — conservative approach overstates NIIT slightly but is audit-safe"

patterns-established:
  - "Pattern: deductions via cfg.get('deductions', {}) — extensible for future deduction types"
  - "Pattern: capital_gains_subtraction = -page1['capital_gain_loss'] — handles gain/loss years correctly"

requirements-completed: [FIX-01, FIX-02, FIX-03]

# Metrics
duration: 2min
completed: 2026-03-10
---

# Phase 3 Plan 01: Three Precision Bug Fixes Summary

**Three targeted IRS computation corrections: NIIT now uses gross income ($3,400.65), Schedule B DNI reduced to $903.94 via capital gains exclusion, and attorney fee deduction wired from config**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-10T00:39:28Z
- **Completed:** 2026-03-10T00:41:37Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- FIX-01: Form 8960 Line 19a corrected from taxable_income to total_income — NIIT increased from $3,396.85 to $3,400.65 (+$3.80)
- FIX-02: Schedule B Line 6 populated with -$104,236.73 capital gains subtraction; DNI corrected from $105,140.67 to $903.94
- FIX-03: config/2025.json now has deductions.attorney_accountant_fees (0.00); compute_form_1041_page1() reads it and both fields wire into form field maps

## Task Commits

Each task was committed atomically:

1. **Task 1: Add deductions support (FIX-03)** - `08971ea` (feat)
2. **Task 2: Fix Form 8960 Line 19a to use gross income (FIX-01)** - `a2851fe` (fix)
3. **Task 3: Fix Schedule B Line 6 capital gains subtraction (FIX-02)** - `a69f168` (fix)

## Files Created/Modified
- `config/2025.json` - Added "deductions": {"attorney_accountant_fees": 0.00} block after trust_exemption
- `fill_1041.py` - Three function updates: compute_form_1041_page1() (deductions), compute_form_8960() (gross income), compute_schedule_b() (capital gains subtraction + DNI); two build_field_maps() extensions (p1_mappings and sched_b_mappings); two computed dict assembly updates in main() and _print_dry_run()

## Decisions Made
- Attorney fee deduction does NOT reduce Form 8960 NII (Lines 9a-9c deferred) — conservative approach slightly overstates NIIT but is audit-safe for 2025 filing
- Zero deduction values still written to PDF fields ($0.00) — consistent with how the $100 exemption is always written

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Dry-run output showed field ID collision: f1_35[0] appears in both form_1041_page1 (total_deductions) and form_8960 (niit_amount). These resolve to different PDFs (f1041.pdf vs f8960.pdf) so actual form filling is correct — the collision only appears in the combined dry-run output display.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All three bug fixes applied and verified via dry-run
- NIIT: $3,400.65 | DNI: $903.94 | Total tax: $23,128.99
- Ready to regenerate filled PDFs with corrected values

---
*Phase: 03-correct-issues-found-during-external-review*
*Completed: 2026-03-10*
