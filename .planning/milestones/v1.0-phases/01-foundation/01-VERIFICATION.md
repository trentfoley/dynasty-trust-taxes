---
phase: 01-foundation
verified: 2026-03-08T19:00:00Z
status: human_needed
score: 9/9 must-haves verified
re_verification: true
  previous_status: human_needed
  previous_score: 8/9
  gaps_closed:
    - "schedule_d.capital_gain_on_form1041_page1 cross-reference corrected from f1_20 to f1_21 (commit 8e980ad)"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Open output/test_filled.pdf in a PDF viewer (browser or Acrobat) and confirm filled fields are visibly rendered without any additional interaction"
    expected: "The trust name field shows 'TEST TRUST NAME', the text amount field shows '999', and the complex trust checkbox appears checked — all visible without saving or refreshing"
    why_human: "NeedAppearances=True is confirmed programmatically, but whether the viewer actually renders all fields immediately depends on viewer behavior and cannot be verified without opening the file"
---

# Phase 1: Foundation Verification Report

**Phase Goal:** All static artifacts are in place so the Core Skill has everything it needs: known tax brackets, known AcroForm field names, and a working PDF writer it can call
**Verified:** 2026-03-08
**Status:** human_needed (all automated checks passed; 1 item needs human visual confirmation)
**Re-verification:** Yes — after gap closure (previous status: human_needed)

## Re-verification Summary

| Item | Previous | Current | Change |
|------|----------|---------|--------|
| schedule_d cross-reference field ID | WARNING: stale f1_20 | VERIFIED: corrected to f1_21 (commit 8e980ad) | Closed |
| Visual PDF field rendering | NEEDS HUMAN | NEEDS HUMAN | Unchanged — inherently visual |
| All 9 automated truths | 8/9 auto-verified | 9/9 auto-verified | Improved |

No regressions detected. All artifacts remain intact and substantive.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | config/2025.json exists and contains named bracket thresholds for all 2025 ordinary income, capital gains, and NIIT tiers — no rate values appear in any script | VERIFIED | All 8 bracket values confirmed numerically (10_pct_max=3150, 24_pct_max=11450, 35_pct_max=15650, 0_pct_max=3250, 15_pct_max=15900, niit.threshold=15650, niit.rate=0.038, trust_exemption=100); grep of fill_pdf.py found 0 hardcoded rate constants |
| 2 | fill_pdf.py accepts --fields --form --output and exits 0 on --help | VERIFIED | --help ran, exit code 0, all three args shown in usage output |
| 3 | fill_pdf.py exits non-zero with a clear error message when a field name in the JSON is not found in the AcroForm | VERIFIED | Test with fake_field_xyz_nonexistent: stderr printed "ERROR: field not found in AcroForm: 'fake_field_xyz_nonexistent'", exit code 1 |
| 4 | fill_pdf.py sets NeedAppearances automatically via auto_regenerate=True — filled fields are visible in PDF viewers | VERIFIED (auto) / NEEDS HUMAN (visual) | Programmatic: output/test_filled.pdf NeedAppearances=True confirmed; visual rendering requires human |
| 5 | fill_pdf.py translates "Yes"/"Off" checkbox convention to the actual On-state value read from /_States_ at runtime | VERIFIED | Code reads /_States_ in get_on_state() (lines 55-65); smoke test output: 57 checkbox fields, 0 retain "Yes" as value |
| 6 | config/2025_fields.json exists and contains real AcroForm field names from forms/f1041.pdf — not placeholder names | VERIFIED | File loaded; 142 real field IDs all begin with topmostSubform[0]...; enumerated via pypdf against actual PDF |
| 7 | Field names are grouped by form section: form_1041_page1, schedule_b, schedule_d, schedule_g, form_8960 | VERIFIED | All 5 required sections present; _metadata section also present (benign addition) |
| 8 | Each entry maps a readable semantic name to a full hierarchical AcroForm field ID | VERIFIED | Spot checks: interest_income->f1_16[0], ordinary_dividends->f1_17[0], taxable_income->f1_42[0], tax_on_taxable_income->f2_23[0], niit_form_8960_line21->f2_35[0] — all begin topmostSubform[0]... |
| 9 | Checkbox entries include their On-state value (1 or 2) alongside the field ID | VERIFIED | entity_type_complex_trust: on_state="1", field_type="checkbox"; discuss_with_preparer_no: on_state="2" — pattern confirmed throughout |

**Score:** 9/9 truths verified automatically; 1 truth (Truth 4 visual rendering) requires human confirmation

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `config/2025.json` | 2025 tax brackets, trust metadata, file paths | VERIFIED | 35 lines; all sections present: ordinary_income_brackets, capital_gains_brackets, niit, qdcg_worksheet, trust_exemption, trust, paths, _notes; valid JSON |
| `fill_pdf.py` | Thin AcroForm PDF filler | VERIFIED | 125 lines; argparse, json, os, sys, pypdf imports; parse_args(), get_on_state(), main() all substantively implemented; no placeholders or stubs |
| `requirements.txt` | Python dependency declaration | VERIFIED | Single line: pypdf>=6.7.5 |
| `config/2025_fields.json` | Semantic-to-AcroForm-ID field catalog | VERIFIED | 376 lines; 5 sections; 142 real field IDs starting with topmostSubform[0]...; checkbox metadata present; schedule_d and form_8960 use null field_id with _note pattern (documented design decision — separate PDFs not embedded in f1041.pdf) |
| `output/test_filled.pdf` | Smoke test output | VERIFIED | 401,587 bytes; NeedAppearances=True confirmed; 57 checkbox fields examined, 0 retain "Yes" value |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| fill_pdf.py | pypdf PdfWriter.update_page_form_field_values | page=None, auto_regenerate=True | WIRED | Lines 108-110: writer.update_page_form_field_values(page=None, fields=translated, auto_regenerate=True) |
| fill_pdf.py | AcroForm /_States_ | runtime checkbox On-state lookup | WIRED | Lines 55-65: get_on_state() reads field.get("/_States_", []); lines 95-103: called for all "Yes" values before fill |
| Phase 2 skill | config/2025.json | json.load — all bracket values consumed from here | NOT WIRED (Phase 2 not yet built) | Intentional — Phase 2 is the next phase; this link is the consumption contract, not yet implemented |
| Phase 2 skill | config/2025_fields.json | json.load — skill reads semantic names to build field-value dict | NOT WIRED (Phase 2 not yet built) | Intentional — same as above |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CALC-06 | 01-01-PLAN.md | All tax bracket thresholds and rates stored in config/YEAR.json — no bracket values hardcoded in any skill or script | SATISFIED | config/2025.json contains all bracket values with named thresholds; grep of fill_pdf.py returned 0 hardcoded numeric constants |
| PDF-FILLER | 01-01-PLAN.md | fill_pdf.py accepts --fields and --form and writes filled PDF with NeedAppearances set | SATISFIED | --help exits 0; hard-fail confirmed; smoke test: NeedAppearances=True; checkbox translation verified (0 of 57 retain "Yes") |
| PDF-01 | 01-02-PLAN.md | AcroForm field names discovered from blank forms/f1041.pdf via pypdf PdfReader.get_fields() and stored in config/YEAR_fields.json | SATISFIED | config/2025_fields.json has 142 real hierarchical field IDs enumerated from f1041.pdf; human-verify gate completed with corrections committed across 6a1d941, 4f462d4, 8e980ad |

All three Phase 1 requirements (CALC-06, PDF-01, PDF-FILLER) are accounted for. REQUIREMENTS.md traceability table marks all three as Complete for Phase 1. No orphaned requirements.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| config/2025.json | Lines 6, 11 | Placeholder values: ein="XX-XXXXXXX", csv_input="2025/XXXX-X123.CSV" | INFO (expected) | Intentional per plan — _notes field warns user to update before Phase 2. No impact on Phase 1 goal. |
| config/2025_fields.json | Various checkbox entries | _note annotations on c1_21, c1_22, c1_24[1], c1_25 entries: "Verify exact purpose against form visual" | INFO | These are low-confidence checkbox mappings for non-critical fields (Line F extras, preparer checkboxes). The primary income, deduction, and tax computation fields are clean. Phase 2 will not touch these ambiguous fields initially. |

No blocker or warning-level anti-patterns. All critical fields are substantively mapped and verified.

### Human Verification Required

#### 1. Visual PDF Field Rendering

**Test:** Open `output/test_filled.pdf` in a PDF viewer (browser or Acrobat).
**Expected:** Fields are visibly filled without any extra interaction — trust name shows "TEST TRUST NAME", the text amount field shows "999", and the complex trust checkbox appears checked.
**Why human:** NeedAppearances=True is confirmed programmatically, but whether the PDF viewer actually renders fields immediately (vs. requiring a save or refresh) depends on viewer behavior and cannot be verified without opening the file.

### Gaps Summary

No blocking gaps. All three PLAN-declared requirement IDs for goal achievement are satisfied:

1. **Tax brackets** — config/2025.json contains all 2025 ordinary income, capital gains, NIIT, and QD&CG worksheet values as named thresholds. No bracket values appear in fill_pdf.py.
2. **AcroForm field catalog** — config/2025_fields.json contains 142 real hierarchical field IDs from forms/f1041.pdf enumerated via pypdf, with semantic names and checkbox metadata, human-verified and corrected across multiple fix commits (6a1d941, 4f462d4, 8e980ad). The previous off-by-one and stale cross-reference issues are resolved.
3. **PDF writer** — fill_pdf.py is fully implemented (125 lines, no stubs), exits 0 on --help, hard-fails on unknown field names, translates "Yes" via /_States_ at runtime, and writes visible-field PDFs with NeedAppearances=True.

The phase goal is achieved. Phase 2 (Core Skill) has everything it needs to proceed.

---

_Verified: 2026-03-08_
_Verifier: Claude (gsd-verifier)_
