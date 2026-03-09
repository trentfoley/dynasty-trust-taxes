---
phase: 02-core-skill
plan: "03"
subsystem: pdf-filling
tags: [python, pypdf, fill_pdf, subprocess, tax-forms, form-1041, schedule-d, form-8960, form-8949]

# Dependency graph
requires:
  - phase: 02-core-skill/02-01
    provides: AcroForm field catalog (config/2025_fields.json), blank PDFs in forms/
  - phase: 02-core-skill/02-02
    provides: Full computation engine (compute_schedule_g, compute_form_8960, validate, build_field_maps)
provides:
  - fill_form() helper that writes field values via fill_pdf.py subprocess
  - complete_schedule_d_part5() computing all 25 Part V lines
  - Live PDF output for all 4 forms: 1041, Schedule D, 8960, 8949
  - print_summary() displaying gross income, taxable income, Schedule G tax, NIIT, total tax
  - /fill-1041 slash command (.claude/commands/fill-1041.md)
affects: [future tax years, phase-03-review]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - fill_form() writes temp JSON, calls fill_pdf.py via subprocess, deletes temp in finally block
    - sys.executable used for subprocess to inherit correct Python interpreter (not hardcoded path)
    - Live vs dry-run branch in main() after field_maps computed

key-files:
  created:
    - .claude/commands/fill-1041.md
  modified:
    - fill_1041.py

key-decisions:
  - "Use sys.executable rather than hardcoded /c/ProgramData/miniconda3/python in subprocess.run — Windows subprocess cannot resolve Unix-style paths that bash can"
  - "compute_schedule_d_part5() mirrors IRS Schedule D Part V worksheet line-by-line (lines 21-45) for auditability"
  - "fill_form() raises RuntimeError on non-zero exit, includes stderr text for diagnosis"

patterns-established:
  - "Pattern: fill_form(field_values, form_path, output_path) — reusable for any AcroForm PDF"
  - "Pattern: Loop over form_keys with empty-map check before calling fill_form (XFA skip with WARNING)"

requirements-completed: [PDF-02, PDF-03, PDF-04, PDF-05, PDF-06, PDF-07, SKILL-01, SKILL-02, SKILL-03, SKILL-04]

# Metrics
duration: 15min
completed: 2026-03-08
---

# Phase 2 Plan 03: Wire Live PDF Output and Slash Command Summary

**Complete end-to-end Form 1041 skill: fill_form() subprocess helper, Schedule D Part V computation, live PDF writing for all 4 forms, and /fill-1041 slash command**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-08T22:05:00Z
- **Completed:** 2026-03-08T22:20:00Z
- **Tasks:** 3 of 3 complete (including human-verify checkpoint, approved 2026-03-09)
- **Files modified:** 2

## Accomplishments
- `fill_form()` implemented using tempfile + subprocess, raises RuntimeError with stderr on failure
- `compute_schedule_d_part5()` added implementing all 25 IRS lines (21-45) of Schedule D Part V
- Fixed `compute_schedule_g()` zero_bucket formula: ordinary income now fills lower brackets before preferential income takes 0% rate
- All 4 PDFs written on live run: 1041, Schedule D, 8960, 8949
- `/fill-1041` slash command created at `.claude/commands/fill-1041.md`

## Task Commits

1. **Task 1: fill_form() and live PDF writing** - `9405e1b` (feat)
2. **Task 2: /fill-1041 slash command** - `9876694` (feat) — created in prior session, verified present

## Files Created/Modified
- `fill_1041.py` — Added fill_form(), compute_schedule_d_part5(), fixed compute_schedule_g() bucket formula, completed main() live mode
- `.claude/commands/fill-1041.md` — Claude slash command invoking fill_1041.py with $ARGUMENTS from project root

## Decisions Made
- Used `sys.executable` in subprocess call instead of hardcoded `/c/ProgramData/miniconda3/python` — Windows subprocess cannot resolve Unix-style bash paths
- Schedule D Part V computed line-by-line matching IRS form exactly (lines 21-45) for auditability
- fill_form() uses `delete=False` NamedTemporaryFile to ensure temp file path is available after context manager exits, cleaned up in finally block

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed compute_schedule_g() zero_bucket formula**
- **Found during:** Task 1 (implementing fill_form and reviewing computation)
- **Issue:** Old formula `min(zero_max, taxable_income, preferential_income)` placed all preferential income in 0% bucket without accounting for ordinary income filling lower brackets. Understated tax by $5.42.
- **Fix:** Changed to `max(0.0, min(zero_max, taxable_income) - ordinary_income)` so ordinary income displaces preferential income from 0% bracket
- **Files modified:** fill_1041.py
- **Verification:** Schedule G Line 1a now = $19,728.34 (matches 2025 tax table expectations)
- **Committed in:** 9405e1b

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug)
**Impact on plan:** Bug fix necessary for correct tax computation. No scope creep.

## Issues Encountered
- Task 2 (.claude/commands/fill-1041.md) was already committed in a prior session (9876694) before the WIP checkpoint. No re-work needed.

## Checkpoint Status

**APPROVED** — Human verified all filled PDFs render correctly in browser PDF viewer and /fill-1041 slash command works from Claude chat. Phase 2 complete.

## Next Phase Readiness
- Phase 2 skill is fully implemented and human-verified — CSV parse, compute, validate, fill PDFs, slash command
- All 4 filled PDFs in output/ confirmed visually correct
- Phase 2 is complete

---
*Phase: 02-core-skill*
*Completed: 2026-03-08*
