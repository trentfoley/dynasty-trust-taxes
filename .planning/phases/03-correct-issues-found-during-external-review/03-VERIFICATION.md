---
phase: 03-correct-issues-found-during-external-review
verified: 2026-03-09T00:00:00Z
status: human_needed
score: 5/6 must-haves verified
re_verification: false
human_verification:
  - test: "Open output/2025 8960 Trent Foley Childrens 2021 Super Dynasty Trust.pdf and inspect Line 19a"
    expected: "Line 19a shows $105,141 (whole-dollar format for $105,140.67). Line 19c shows $89,491. Line 21 shows $3,401."
    why_human: "AcroForm field rendering only verifiable by opening the PDF in a viewer — dry-run confirms the field value is set but cannot confirm it is visible."
  - test: "Open output/2025 1041 Trent Foley Childrens 2021 Super Dynasty Trust.pdf, navigate to Schedule B (page 2) and inspect Lines 6 and 7"
    expected: "Line 6 shows -104,237 or (104,237). Line 7 (DNI) shows 904."
    why_human: "Same AcroForm rendering caveat. Negative dollar values may render differently across PDF viewers."
  - test: "Open output/2025 1041 Trent Foley Childrens 2021 Super Dynasty Trust.pdf, inspect Form 1041 Page 1 Line 14"
    expected: "Line 14 (attorney/accountant fees) shows 1,250. Line 16 (total deductions) shows 1,250."
    why_human: "Field visibility requires PDF viewer. The plan-02 SUMMARY documents human approval was given — this item is a confirmation check."
---

# Phase 3: Correct Issues Found During External Review — Verification Report

**Phase Goal:** Apply three precision bug fixes identified by external review — correct Form 8960 Line 19a (use gross income not taxable income), fill Schedule B Line 6 with the correct negative capital gain, and add config-driven Line 14 deduction support
**Verified:** 2026-03-09
**Status:** human_needed (all automated checks pass; PDF rendering requires human confirmation)
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Form 8960 Line 19a uses gross income ($105,140.67), not taxable income | VERIFIED | `agi_undistributed_nii = page1["total_income"]` at line 460; dry-run shows $105,140.67 |
| 2 | NIIT equals $3,400.65 (up from $3,396.85) | VERIFIED | Dry-run output: "NIIT (Line 21 = 3.8%): $3,400.65" |
| 3 | Schedule B Line 6 filled with negative capital gain (-$104,236.73) | VERIFIED | f2_13[0] = -104,237 in dry-run; `capital_gains_subtraction = -round(capital_gain, 2)` at line 309 |
| 4 | Schedule B DNI (Line 7) equals $903.94 | VERIFIED | f2_14[0] = 904 in dry-run (whole-dollar formatting); computation `dni = round(page1["total_income"] + capital_gains_subtraction, 2)` at line 312 produces $903.94 |
| 5 | Line 14 deduction reads from config/2025.json and wires into taxable income | VERIFIED | config has `"attorney_accountant_fees": 1250.00`; code reads via `cfg.get("deductions", {}).get("attorney_accountant_fees", 0.0)`; taxable_income = $103,790.67 ($105,140.67 - $1,250 - $100) |
| 6 | Zero deduction case produces no change beyond FIX-01 correction | N/A | Out-of-plan change: fees were set to $1,250 (not zero) during plan-02 human checkpoint. Truth was predicated on zero fees. With $1,250, taxable income and Schedule G tax changed as expected — behavior is correct. |

**Score:** 5/5 applicable truths verified (truth 6 superseded by out-of-plan change; outcome is correct)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `config/2025.json` | Contains `deductions.attorney_accountant_fees` | VERIFIED | Key present with value `1250.00` (plan specified `0.00`; updated to `1250.00` during plan-02 — intentional user change) |
| `fill_1041.py` | All three bug fixes applied | VERIFIED | compute_form_1041_page1(), compute_form_8960(), compute_schedule_b(), and both build_field_maps() extensions all present and substantive |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `config/2025.json` | `compute_form_1041_page1()` | `cfg.get('deductions', {}).get('attorney_accountant_fees', 0.0)` | WIRED | Lines 277-279 of fill_1041.py |
| `compute_form_1041_page1()` | `taxable_income` | `total_income - total_deductions_line16 - exemption` | WIRED | Line 285; dry-run confirms $103,790.67 |
| `compute_form_8960()` | `page1['total_income']` | `agi_undistributed_nii = page1["total_income"]` | WIRED | Line 460; pattern `total_income` confirmed |
| `compute_schedule_b()` | `capital_gains_subtraction` | `-page1['capital_gain_loss']` | WIRED | Lines 308-309; returned in dict at line 319 |
| `sched_b_capital_gains_subtraction` | `gain_from_page1_line4` in sched_b_mappings | `computed.get("sched_b_capital_gains_subtraction")` | WIRED | Line 606 in build_field_maps(); assembled into computed dict at line 1054 |
| `distributable_net_income` | f2_14[0] (Schedule B Line 7) | `sched_b_mappings["distributable_net_income"]` | WIRED | Line 607; dry-run shows f2_14[0] = 904 |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| FIX-01 | 03-01-PLAN.md | Form 8960 Line 19a uses gross income (Form 1041 Line 17), not taxable income | SATISFIED | `agi_undistributed_nii = page1["total_income"]`; NIIT = $3,400.65 confirmed |
| FIX-02 | 03-01-PLAN.md | Schedule B Line 6 filled with negative net capital gain; DNI corrected | SATISFIED | `capital_gains_subtraction = -104,237`; DNI = 904 in dry-run |
| FIX-03 | 03-01-PLAN.md | Config-driven Line 14 deduction support — attorney/accountant fees | SATISFIED | `config/2025.json` deductions block present; wired through compute chain; taxable income reduced by $1,250 |

**Orphaned Requirements Note:** FIX-01, FIX-02, and FIX-03 do not appear in `.planning/REQUIREMENTS.md`. The requirements document was finalized at phase 2 (last updated 2026-03-08) before phase 3 was conceived. These are valid phase requirements declared in the PLAN frontmatter and ROADMAP.md but the traceability table in REQUIREMENTS.md is not updated. This is a documentation gap, not a functional gap — no functional requirement is unaddressed.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `fill_1041.py` | 445-446 | Stale docstring: "AGI basis is undistributed net income = taxable_income" — contradicts the fix applied at line 460 which correctly uses `total_income` | Warning | None on computation; misleads future readers of the code |

No placeholder returns, TODO markers, or empty implementations found in any phase-3-modified code paths.

### Human Verification Required

#### 1. Form 8960 Line 19a and NIIT rendering

**Test:** Open `output/2025 8960 Trent Foley Childrens 2021 Super Dynasty Trust.pdf` in a PDF viewer and inspect Part III.
**Expected:** Line 19a shows 105,141 (whole-dollar format). Line 19c shows 89,491. Line 21 shows 3,401.
**Why human:** AcroForm field rendering depends on the viewer rendering NeedAppearances correctly. The dry-run confirms the field value string is set; actual visibility requires opening the file.

#### 2. Schedule B Line 6 and Line 7 rendering

**Test:** Open `output/2025 1041 Trent Foley Childrens 2021 Super Dynasty Trust.pdf`, navigate to page 2 (Schedule B).
**Expected:** Line 6 shows -104,237 or (104,237). Line 7 (DNI) shows 904.
**Why human:** Negative dollar values in AcroForm fields may render differently across PDF viewers (parentheses vs. minus sign). Only visual inspection confirms the field is visible and the negative sign is handled correctly.

#### 3. Form 1041 Line 14 attorney/accountant fees rendering

**Test:** Open `output/2025 1041 Trent Foley Childrens 2021 Super Dynasty Trust.pdf`, inspect Page 1 Line 14 and Line 16.
**Expected:** Line 14 shows 1,250. Line 16 (total deductions) shows 1,250.
**Why human:** Plan-02 SUMMARY documents that the human checkpoint was passed and "approved" — this is a confirmation check to close the loop with the verifier.

**Note on plan-02 human checkpoint:** The 03-02-SUMMARY.md states human verification was completed and approved on 2026-03-09. The three items above correspond directly to what was approved. If that approval is trusted, status can be upgraded to `passed` without re-opening the PDFs.

### Gaps Summary

No functional gaps found. All three bug fixes are implemented correctly, wired through the computation chain, and produce the expected numeric outputs confirmed by dry-run.

Two items are noted but do not block the goal:

1. **Stale docstring** in `compute_form_8960()` (lines 445-446): says `taxable_income` when code correctly uses `total_income`. This is a cosmetic issue — the actual fix is correct and verified.

2. **REQUIREMENTS.md not updated**: FIX-01/02/03 are not in the traceability table. The requirements document was not designed for post-phase bug fix requirements. No functional coverage is missing.

3. **Out-of-plan changes are incorporated**: The attorney fees were set to $1,250 (not $0.00) and dollar formatting was changed to whole numbers. Both changes are correctly propagated through the codebase and produce valid IRS-formatted output.

---

_Verified: 2026-03-09_
_Verifier: Claude (gsd-verifier)_
