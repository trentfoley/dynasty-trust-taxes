---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Milestone v1.0 shipped
stopped_at: Phase 3 context gathered
last_updated: "2026-03-10T00:19:07.330Z"
last_activity: 2026-03-09 — v1.0 archived, 19/19 requirements verified, all 4 forms filled
progress:
  total_phases: 3
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-09 after v1.0 milestone)

**Core value:** Given a brokerage year-end CSV and blank IRS form PDFs, produce complete, filled, print-ready tax forms in one `/fill-1041` command.
**Current focus:** v1.0 shipped — planning next milestone

## Current Position

Phase: All complete (2/2)
Status: Milestone v1.0 shipped
Last activity: 2026-03-09 — v1.0 archived, 19/19 requirements verified, all 4 forms filled

Progress: [██████████] 100%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
| Phase 01-foundation P01 | 2 | 3 tasks | 5 files |
| Phase 01-foundation P02 | 45 | 2 tasks | 1 files |
| Phase 02-core-skill P01 | 5 | 2 tasks | 5 files |
| Phase 02-core-skill P01 | 5 | 2 tasks | 5 files |
| Phase 02-core-skill P02 | 4 | 2 tasks | 1 files |
| Phase 02-core-skill P03 | 15 | 2 tasks | 2 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Foundation: Use brokerage CSV as primary data source; Python + pypdf as stack; fill existing IRS AcroForm PDF
- [Phase 01-foundation]: Named bracket thresholds in config/2025.json — all rate values consumed from config, never hardcoded in scripts
- [Phase 01-foundation]: fill_pdf.py translates 'Yes' checkbox values to On-state via /_States_ runtime lookup — resilient to PDFs using non-standard On-state values
- [Phase 01-foundation]: Hard-fail on unknown AcroForm field names: collect all errors before exit(1)
- [Phase 01-foundation]: schedule_d and form_8960 are separate PDFs — those catalog sections use null field IDs with cross-reference keys for values flowing into f1041.pdf
- [Phase 01-foundation]: g2_trust_tin uses f1_15 (header field); income body text fields start at f1_16 — off-by-one confirmed by human fill test
- [Phase 01-foundation]: refund_routing_number uses comb container path Line30cCombfield[0].f1_52[0]; sign_date renamed to sign_ein_fiduciary (f1_54 is EIN of fiduciary)
- [Phase 02-core-skill]: 1099-B section has two header rows to skip (field-number row + column-name row)
- [Phase 02-core-skill]: schedule_d field IDs confirmed: short_term summary=f1_19-f1_22, long_term=f1_39-f1_42, net_capital_gain=Part3/Line19/f2_15
- [Phase 02-core-skill]: form_8960 NIIT amount (Line 21) = f1_35; trust entity checkbox = c1_1[2]
- [Phase 02-core-skill]: form_8949 Box A (short-term covered)=c1_1[0] Page1, Box D (long-term covered)=c2_1[0] Page2
- [Phase 02-core-skill]: 1099-B section has two header rows to skip before data rows (field-number row + column-name row)
- [Phase 02-core-skill]: schedule_d field mapping: short_term_proceeds=f1_19, net_short_term_gain_loss=f1_22, long_term_proceeds=f1_39, net_long_term_gain_loss=f1_42, net_capital_gain=Part3/Line19/f2_15
- [Phase 02-core-skill]: form_8960 NIIT amount (Line 21) = f1_35; trust entity checkbox = c1_1[2]
- [Phase 02-core-skill]: form_8949 Box A (short-term covered) = c1_1[0] Page1; Box D (long-term covered) = c2_1[0] Page2; 6 checkboxes per page at indices [0..5]
- [Phase 02-core-skill]: compute_schedule_g() reads all bracket thresholds from cfg — no hardcoded constants
- [Phase 02-core-skill]: validate() augments csv_data with raw transaction re-sum for st_gain/lt_gain before comparing to computed values
- [Phase 02-core-skill]: Schedule G tax /usr/bin/bash.01 rounding diff (9,722.92 vs 9,722.93) is float precision on ordinary_income — within tolerance
- [Phase 02-core-skill]: Use sys.executable in subprocess.run for fill_form() — Windows subprocess cannot resolve Unix-style bash paths
- [Phase 02-core-skill]: compute_schedule_d_part5() mirrors IRS form lines 21-45 exactly for auditability

### Roadmap Evolution

- Phase 3 added: Correct issues found during external review

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 4: AcroForm field names for 2025 IRS forms are unknown until `pypdf PdfReader.get_fields()` is run against the actual downloaded PDFs in `forms/` — this is a prerequisite for Phase 4 implementation
- Phase 4: Must verify 2025 Form 1041 uses AcroForm (not XFA) before starting filler work; if XFA, the PDF approach changes entirely

## Session Continuity

Last session: 2026-03-10T00:19:07.326Z
Stopped at: Phase 3 context gathered
Resume file: .planning/phases/03-correct-issues-found-during-external-review/03-CONTEXT.md
