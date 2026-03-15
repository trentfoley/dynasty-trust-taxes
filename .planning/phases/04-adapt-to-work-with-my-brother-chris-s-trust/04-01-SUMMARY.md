---
phase: 04-adapt-to-work-with-my-brother-chris-s-trust
plan: 01
subsystem: cli
tags: [argparse, multi-trust, tax-computation, schedule-g, config]

# Dependency graph
requires:
  - phase: 03-correct-issues-found-during-external-review
    provides: Working fill_1041.py with correct tax computation for single trust
provides:
  - "--trust CLI flag for multi-trust selection"
  - "Per-trust config files (config/2025_trent.json, config/2025_chris.json)"
  - "Chris's manual CSV data (2025_chris/dividends.csv)"
  - "Fixed compute_schedule_g cap bug for QD > taxable_income"
affects: [04-02-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns: [two-phase-argparse, per-trust-config]

key-files:
  created:
    - config/2025_chris.json
    - 2025_chris/dividends.csv
    - test_multi_trust.py
  modified:
    - fill_1041.py
    - config/2025_trent.json

key-decisions:
  - "compute_schedule_g cap fix also corrects Trent's tax from $19,720.22 to $19,475.63 (matching Part V canonical)"
  - "Two-phase argparse: parse_trust_and_year() extracts --trust before config load"
  - "Duplicate brackets across trust configs (no shared config layer)"

patterns-established:
  - "Two-phase CLI parsing: parse_trust_and_year() -> load_config() -> parse_args()"
  - "Per-trust config: config/{year}_{trust}.json"

requirements-completed: [MULTI-01, MULTI-02, MULTI-03, MULTI-04]

# Metrics
duration: 5min
completed: 2026-03-15
---

# Phase 4 Plan 01: Multi-Trust Infrastructure Summary

**Multi-trust CLI via --trust flag, per-trust configs, Chris's CSV data, and compute_schedule_g cap fix correcting both trusts' tax computation**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-15T03:15:36Z
- **Completed:** 2026-03-15T03:21:07Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created per-trust config files with Chris trust identity (EIN 87-6898455, $500 attorney fees)
- Refactored CLI to require --trust flag with two-phase argument parsing
- Fixed compute_schedule_g cap bug: preferential_income now capped at taxable_income
- Chris tax: $779.35 (correct), Trent tax: $19,475.63 + $3,400.65 NIIT = $22,876.28 (corrected from $23,120.87)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Chris config, Chris CSV, update Trent config paths** - `feb497c` (feat)
2. **Task 2 RED: Failing tests for multi-trust CLI and schedule_g** - `afc86c8` (test)
3. **Task 2 GREEN: Implement --trust flag and fix cap bug** - `fcc9d8d` (feat)

## Files Created/Modified
- `config/2025_chris.json` - Chris trust config with identity, brackets, $500 fees
- `config/2025_trent.json` - Updated paths to 2025_trent/ and output/trent
- `2025_chris/dividends.csv` - Manual CSV with 1099-DIV data ($9,045.68 ordinary, $8,671 qualified)
- `fill_1041.py` - Refactored CLI (--trust flag), fixed compute_schedule_g cap bug
- `test_multi_trust.py` - 5 unit tests for CLI behavior and tax computation

## Decisions Made
- **compute_schedule_g cap fix changes Trent's tax too:** The cap bug affected Trent as well (preferential $105,013.58 > taxable $103,790.67). Old schedule_g produced $19,720.22; correct Part V answer is $19,475.63. The fix reduces Trent's total tax by $244.59 (from $23,120.87 to $22,876.28). This is a genuine correction, not a regression -- Part V (the IRS authoritative worksheet) always computed $19,475.63.
- **Two-phase argparse:** parse_trust_and_year() uses parse_known_args to extract --trust before loading config, then parse_args() re-declares --trust for help text consistency.
- **Duplicate brackets:** Per plan, brackets are duplicated across trust configs (no shared config layer).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Trent's Schedule G tax also corrected by cap fix**
- **Found during:** Task 2 (compute_schedule_g cap fix)
- **Issue:** The plan expected Trent's tax to remain unchanged at $19,720.22, but the cap fix also corrects Trent's computation. For Trent, preferential_income ($105,013.58) exceeds taxable_income ($103,790.67) by $1,222.91, causing $244.59 excess tax in the twenty_bucket. Part V (compute_schedule_d_part5) always returned the correct $19,475.63.
- **Fix:** Updated test expectation to $19,475.63 (matching Part V canonical answer). The fix is correct -- the old value was wrong.
- **Files modified:** test_multi_trust.py
- **Verification:** compute_schedule_g now matches compute_schedule_d_part5 line 45 for both trusts
- **Committed in:** fcc9d8d

---

**Total deviations:** 1 auto-fixed (1 bug correction)
**Impact on plan:** The cap fix correctly applies to both trusts. Trent's total tax decreases from $23,120.87 to $22,876.28. This is the IRS-correct value per Part V worksheet.

## Issues Encountered
None beyond the Trent tax correction documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Both trusts process through dry-run with correct tax computation
- Ready for Plan 02: conditional form generation, per-trust output directories, PDF generation
- Chris needs only Form 1041 (no Schedule D, 8949, or 8960)
- Output directories: output/trent/ and output/chris/

---
*Phase: 04-adapt-to-work-with-my-brother-chris-s-trust*
*Completed: 2026-03-15*
