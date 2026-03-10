---
phase: 03-correct-issues-found-during-external-review
plan: 02
subsystem: tax-forms
tags: [pdf, fill_1041, schedule-b, form-8960, form-1041, attorney-fees, formatting]

# Dependency graph
requires:
  - phase: 03-correct-issues-found-during-external-review
    plan: 01
    provides: Three bug fixes applied to fill_1041.py and config/2025.json
provides:
  - Regenerated output PDFs with all three bug fixes visible and human-verified
  - Dollar formatting as whole numbers with thousands separators across all forms
  - Attorney/accountant fees of $1,250 set in config/2025.json
affects:
  - future phases involving PDF generation or tax computation review

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Human checkpoint pattern: regenerate PDFs then human visually verifies specific field values before approving"

key-files:
  created: []
  modified:
    - output/2025 1041 Trent Foley Childrens 2021 Super Dynasty Trust.pdf
    - output/2025 Schedule D Trent Foley Childrens 2021 Super Dynasty Trust.pdf
    - output/2025 8960 Trent Foley Childrens 2021 Super Dynasty Trust.pdf
    - output/2025 8949 Trent Foley Childrens 2021 Super Dynasty Trust.pdf
    - fill_1041.py
    - config/2025.json

key-decisions:
  - "Dollar values formatted as whole numbers with thousands separators (e.g., 105,141 not 105140.67) for readability on printed forms"
  - "Attorney/accountant fees set to $1,250 in config/2025.json — deductible on Form 1041 Line 14"

patterns-established:
  - "Visual PDF verification checkpoint: agent regenerates PDFs, human opens and confirms specific field values, returns 'approved' or describes discrepancies"

requirements-completed: [FIX-01, FIX-02, FIX-03]

# Metrics
duration: ~30min (including human checkpoint)
completed: 2026-03-09
---

# Phase 03 Plan 02: PDF Regeneration and Visual Verification Summary

**All four output PDFs regenerated with three bug fixes applied and human-verified: NIIT $3,400.65 (Form 8960), DNI $903.94 (Schedule B), attorney fees $1,250 (Form 1041 Line 14)**

## Performance

- **Duration:** ~30 min (including human checkpoint review)
- **Started:** 2026-03-09
- **Completed:** 2026-03-09
- **Tasks:** 2
- **Files modified:** 4 output PDFs + 2 source files (outside-plan changes)

## Accomplishments
- Regenerated all four output PDFs with corrected Form 8960, Schedule B, and Form 1041 Line 14 values
- Human confirmed all three bug fixes render correctly in the printed PDFs
- Dollar formatting improved to whole numbers with thousands separators (e.g., 105,141)
- Attorney/accountant fees set to $1,250 in config — deductible on Form 1041 Line 14

## Final Tax Figures (2025 return)

| Line | Value |
|------|-------|
| Gross income | $105,140.67 |
| Taxable income | $103,790.67 |
| Schedule G tax | $19,720.22 |
| NIIT (Form 8960) | $3,400.65 |
| Total tax | $23,120.87 |

## Task Commits

1. **Task 1: Regenerate all output PDFs** - `b77b790` (chore)
2. **Task 2: Verify corrected values in output PDFs** - Human-approved (no commit — verification only)

**Out-of-plan changes committed during checkpoint:**
- `c651a68` - style(formatting): format all dollar values as whole numbers with thousands separators
- `3e731c7` - config(2025): set attorney_accountant_fees to $1,250

## Files Created/Modified
- `output/2025 1041 ....pdf` - Regenerated with attorney fees on Line 14, corrected Schedule B DNI
- `output/2025 Schedule D ....pdf` - Regenerated with updated figures
- `output/2025 8960 ....pdf` - Regenerated with Line 19a = gross income ($105,140.67), NIIT = $3,400.65
- `output/2025 8949 ....pdf` - Regenerated (no changes to values)
- `fill_1041.py` - Dollar formatting updated to whole numbers with thousands separators
- `config/2025.json` - attorney_accountant_fees set to 1250

## Decisions Made
- Dollar values formatted as whole numbers with thousands separators for readability on printed tax forms (the IRS expects whole-dollar amounts for most lines)
- Attorney/accountant fees of $1,250 entered into config — this is a real deductible expense for trust administration

## Deviations from Plan

### Out-of-Plan Changes (committed during checkpoint by user)

Two changes were made outside this plan during the human checkpoint review:

**1. Dollar formatting** (`c651a68`)
- All dollar values now format as whole numbers with thousands separators
- Applies across all four output PDFs
- No plan task for this — committed directly during review

**2. Attorney/accountant fees** (`3e731c7`)
- config/2025.json `attorney_accountant_fees` set to $1,250
- Changes taxable income from $105,040.67 to $103,790.67
- Changes Schedule G tax slightly (from $19,728.34 to $19,720.22)
- No plan task for this — committed directly during review

These were user-initiated changes, not auto-fix deviations.

## Issues Encountered
None — plan executed cleanly. Human verification passed on first review.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 3 is now complete — all three external-review issues corrected and verified
- Final tax figures: Total tax $23,120.87 (Schedule G $19,720.22 + NIIT $3,400.65)
- PDFs are print-ready for filing
- No blockers for future phases

---
*Phase: 03-correct-issues-found-during-external-review*
*Completed: 2026-03-09*
