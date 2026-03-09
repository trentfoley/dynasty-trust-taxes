---
phase: 01-foundation
plan: 02
subsystem: infra
tags: [pypdf, acroform, form-1041, field-mapping, pdf-fill]

# Dependency graph
requires:
  - phase: 01-foundation plan 01
    provides: fill_pdf.py and forms/f1041.pdf in place; Python + pypdf stack confirmed working
provides:
  - config/2025_fields.json — complete semantic-to-AcroForm-ID field catalog for Form 1041 (all five sections)
affects: [phase-02-core-skill, phase-04-implementation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "AcroForm field discovery via pypdf PdfReader.get_fields() — run once, store in config/2025_fields.json, never at runtime"
    - "Semantic naming: human-readable key (e.g., interest_income) maps to full hierarchical field ID (topmostSubform[0].Page1[0].f1_16[0])"
    - "Checkbox fields carry on_state and field_type metadata; text fields use plain string values"
    - "Separate-form fields (Schedule D, Form 8960) documented with field_id: null and _note; cross-reference field IDs provided for values that flow into f1041.pdf"

key-files:
  created: [config/2025_fields.json]
  modified: []

key-decisions:
  - "schedule_d and form_8960 are separate PDFs — those sections document semantic computation intent with null field IDs; cross-reference keys point to where their totals land in f1041.pdf"
  - "g2_trust_tin uses f1_15 (header field on Page1 outside DateNameAddress block); income fields start at f1_16"
  - "sign_date renamed to sign_ein_fiduciary (f1_54 is EIN of fiduciary, not a signature date)"
  - "refund_routing_number uses the comb-container path (Line30cCombfield[0].f1_52[0]) not a bare f1_52"
  - "Schedule G Line 5 references Form 8960 line 21 (trust NIIT line), documented as niit_form_8960_line21 -> f2_35[0]"

patterns-established:
  - "Field catalog pattern: config/2025_fields.json is the single source of truth for all AcroForm IDs — Phase 2 skill loads it via json.load(), never calls get_fields() at runtime"
  - "Cross-reference pattern: when a computed value from a separate form flows into f1041.pdf, a _form1041_cross_reference key documents the target field ID alongside the null-field separate-form entries"

requirements-completed: [PDF-01]

# Metrics
duration: 45min
completed: 2026-03-08
---

# Phase 01 Plan 02: Form 1041 AcroForm Field Catalog Summary

**Semantic-to-AcroForm-ID field catalog for Form 1041 written to config/2025_fields.json via pypdf enumeration and human fill-test verification, covering all five sections needed by Phase 2.**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-03-08
- **Completed:** 2026-03-08
- **Tasks:** 2 (1 auto + 1 human-verify checkpoint)
- **Files modified:** 1

## Accomplishments

- Enumerated all 184 AcroForm fields from forms/f1041.pdf using pypdf PdfReader.get_fields()
- Wrote complete semantic-to-field-ID catalog covering form_1041_page1 (60 text + 27 checkbox fields), schedule_b (Page 2 income distribution), schedule_d (cross-reference structure for separate PDF), schedule_g (Pages 2-3 tax computation), and form_8960 (cross-reference structure for separate PDF)
- Human verified catalog correctness via live fill test with fill_pdf.py; corrections applied and committed

## Task Commits

Each task was committed atomically:

1. **Task 1: Enumerate all AcroForm fields and write config/2025_fields.json** - `53e559c` (feat)
2. **Task 2: Human verification corrections applied** - `6a1d941` (fix)

**Plan metadata:** _(docs commit follows)_

## Files Created/Modified

- `config/2025_fields.json` - Complete semantic-to-AcroForm-ID field catalog for Form 1041; five sections covering all fields Phase 2 needs to populate

## Decisions Made

- schedule_d and form_8960 are separate PDF forms not embedded in f1041.pdf — those sections use null field IDs with _note documentation, plus cross-reference keys for values that carry into f1041.pdf
- g2_trust_tin (Line G2 Trust TIN header) maps to f1_15; all income/deduction body text fields start at f1_16 (off-by-one correction applied during human verification)
- sign_date renamed to sign_ein_fiduciary because f1_54 holds the EIN of the fiduciary, not a signature date
- refund_routing_number uses the comb container path (Line30cCombfield[0].f1_52[0]) confirmed by fill test
- Schedule G niit field named niit_form_8960_line21 to make clear it references Form 8960 line 21 (trust line), not the individual line 11

## Deviations from Plan

### Auto-fixed Issues

None — Task 1 executed as specified.

### Human Verification Corrections (Task 2 gate)

The human-verify checkpoint produced corrections that were applied before approval:

**1. Missing g2_trust_tin field**
- **Found during:** Live fill test (Task 2 verification)
- **Issue:** f1_15 was skipped; the G2 Trust TIN header field was not in the catalog
- **Fix:** Added g2_trust_tin -> f1_15; shifted all subsequent body text fields +1
- **Files modified:** config/2025_fields.json
- **Committed in:** 6a1d941

**2. Off-by-one on body text fields f1_15 through f1_52**
- **Found during:** Live fill test
- **Issue:** All income/deduction/payment fields were one position too low
- **Fix:** Shifted f1_15->f1_16 through f1_51->f1_52 throughout the catalog
- **Files modified:** config/2025_fields.json
- **Committed in:** 6a1d941

**3. refund_routing_number comb path**
- **Found during:** Live fill test
- **Issue:** Routing number field was mapped to bare f1_52 path; actual field lives under Line30cCombfield[0] container
- **Fix:** Updated to topmostSubform[0].Page1[0].Line30cCombfield[0].f1_52[0]; removed duplicate entry
- **Files modified:** config/2025_fields.json
- **Committed in:** 6a1d941

**4. sign_date / preparer field renames**
- **Found during:** Fill test inspection
- **Issue:** f1_54 is EIN of fiduciary, not a date; preparer fields were named incorrectly
- **Fix:** sign_date -> sign_ein_fiduciary; sign_ein_financial_institution -> preparer_name; preparer fields shifted accordingly
- **Files modified:** config/2025_fields.json
- **Committed in:** 6a1d941

---

**Total deviations:** 4 corrections applied during human-verify gate (all field mapping accuracy issues, no scope creep)
**Impact on plan:** All corrections necessary for correctness. Phase 2 can now load this catalog and fill correct form locations.

## Issues Encountered

None beyond the field mapping corrections addressed in the human-verify gate.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- config/2025_fields.json is complete and human-verified; Phase 2 skill can load it directly
- All five required sections present: form_1041_page1, schedule_b, schedule_d, schedule_g, form_8960
- The blocker noted in STATE.md ("AcroForm field names unknown until get_fields() run") is resolved for Form 1041
- Phase 2 should download Schedule D (Form 1041) and Form 8960 PDFs to enumerate their AcroForm fields separately if those forms will be filled programmatically

---
*Phase: 01-foundation*
*Completed: 2026-03-08*
