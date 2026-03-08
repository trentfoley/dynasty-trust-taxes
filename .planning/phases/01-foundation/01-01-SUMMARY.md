---
phase: 01-foundation
plan: "01"
subsystem: infra
tags: [pypdf, python, pdf, acroform, tax-brackets, config]

# Dependency graph
requires: []
provides:
  - "config/2025.json: all 2025 tax bracket values, trust metadata, file paths — no hardcoding in scripts"
  - "fill_pdf.py: thin AcroForm PDF filler with runtime /_States_ checkbox translation"
  - "requirements.txt: pypdf>=6.7.5 dependency declaration"
affects:
  - "02-core-skill"
  - "03-schedule-g"
  - "04-output"

# Tech tracking
tech-stack:
  added: [pypdf>=6.7.5]
  patterns:
    - "Config-first bracket values: all rate thresholds live in config/2025.json, never in scripts"
    - "Runtime checkbox translation: read /_States_ array at fill time to discover On-state value"
    - "Hard-fail field validation: collect all unknown fields, print all errors, exit(1) once"

key-files:
  created:
    - config/2025.json
    - fill_pdf.py
    - requirements.txt
    - test_fields.json
    - output/test_filled.pdf
  modified: []

key-decisions:
  - "Named bracket thresholds in config JSON (e.g. 10_pct_max: 3150), not arrays of tuples — easier to reference by name from Phase 2 skill"
  - "fill_pdf.py translates 'Yes' to On-state via /_States_ at runtime — handles PDFs using '1', '2', or any non-'/Off' value as On-state"
  - "page=None fills all 3 Form 1041 pages in one call; auto_regenerate=True sets NeedAppearances automatically"
  - "Hard-fail on unknown field names: Phase 2 will pass exact field names from research; silent skip would hide typos"

patterns-established:
  - "Pattern 1: Phase 2 skill reads all bracket values from config/2025.json via json.load — no rate constants in skill code"
  - "Pattern 2: fill_pdf.py is a dumb file writer — it knows nothing about tax math"
  - "Pattern 3: Checkbox callers pass 'Yes'/'Off'; fill_pdf.py handles On-state translation internally"

requirements-completed: [CALC-06, PDF-FILLER]

# Metrics
duration: 2min
completed: "2026-03-08"
---

# Phase 1 Plan 01: Foundation — Tax Config and PDF Filler Summary

**2025 tax bracket config (named thresholds, no hardcoding) and pypdf AcroForm filler with runtime /_States_ checkbox translation and hard-fail field validation**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-08T17:33:37Z
- **Completed:** 2026-03-08T17:35:52Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Created `config/2025.json` with all 2025 ordinary income, capital gains, NIIT, and QD&CG worksheet brackets as named thresholds — single source of truth for Phase 2
- Created `fill_pdf.py`: thin AcroForm filler that validates field names hard-fail, translates "Yes" checkboxes to the actual On-state by reading /_States_ at runtime, and sets NeedAppearances via auto_regenerate=True
- Smoke test confirmed: f1041.pdf fills correctly, NeedAppearances=True, checkbox c1_3[0] translated from "Yes" to On-state "1"

## Task Commits

Each task was committed atomically:

1. **Task 1: Create config/2025.json** — `e01fa2e` (feat)
2. **Task 2: Create fill_pdf.py and requirements.txt** — `94c4eb2` (feat)
3. **Task 3: Smoke test — fill test PDF** — `563686f` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `config/2025.json` — 2025 bracket thresholds, NIIT, QD&CG worksheet, trust metadata, file paths, _notes warning
- `fill_pdf.py` — Thin AcroForm filler: arg parsing, field validation, checkbox translation, PDF write
- `requirements.txt` — pypdf>=6.7.5
- `test_fields.json` — Smoke test input with text field and "Yes" checkbox
- `output/test_filled.pdf` — Smoke test output (401KB), NeedAppearances=True

## Decisions Made

- Named thresholds over arrays of tuples: Phase 2 accesses values by key (e.g., `cfg["ordinary_income_brackets"]["10_pct_max"]`), which is clearer and less error-prone than index arithmetic.
- Runtime /_States_ lookup: the 2025 f1041.pdf uses "1" (not "Yes") as checkbox On-state. Hardcoding "Yes"->"1" would break on any PDF that uses a different value. Reading /_States_ at runtime is resilient.
- Hard-fail field validation: collect all unknown fields before exiting so the caller sees all errors at once, not one at a time.

## Deviations from Plan

### Minor Field Path Correction

The plan's Task 3 suggested checkbox path `EntityCheckBoxes[0].c1_3[0]` did not match the actual AcroForm hierarchy. Running `get_fields()` against f1041.pdf revealed the correct path is `LinesA-B[0].c1_3[0]`. Updated test_fields.json to use the actual path. This is within normal scope — the plan explicitly instructs: "If the path above does not match what get_fields() returns, use the actual path from get_fields()."

**Total deviations:** 0 auto-fixes required — field path correction was pre-anticipated and instructed by the plan.
**Impact on plan:** None — all success criteria met exactly as specified.

## Issues Encountered

None — all tools and dependencies were already installed. pypdf 6.7.5 was available in the miniconda environment.

## User Setup Required

Before running Phase 2, update `config/2025.json` with real values:
- `trust.ein` — replace "XX-XXXXXXX" with the actual trust EIN
- `trust.trustee_name` — replace "Trent Foley" with full legal name if different
- `trust.trustee_address` — replace "..." with the trustee mailing address
- `paths.csv_input` — replace "2025/XXXX-X123.CSV" with actual CSV file path

## Next Phase Readiness

- Phase 2 (Core Skill) can consume `config/2025.json` for all bracket values via `json.load`
- Phase 2 can call `fill_pdf.py --fields <json> --form forms/f1041.pdf --output <path>` to produce filled PDFs
- AcroForm field names for f1041.pdf are now discoverable via `reader.get_fields()` — Phase 4 blocker partially resolved

---
*Phase: 01-foundation*
*Completed: 2026-03-08*
