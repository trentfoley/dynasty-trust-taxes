---
phase: 04-adapt-to-work-with-my-brother-chris-s-trust
verified: 2026-03-15T05:00:00Z
status: passed
score: 8/9 must-haves verified
re_verification: false
human_verification:
  - test: "Open output/chris/2025 1041 Christopher Foley Childrens 2021 Super Dynasty Trust.pdf and confirm total tax shows $779"
    expected: "Page 2 Schedule G line 1a = $779, total tax due = $779, trust identity (EIN 87-6898455, address 23606 Powder Mill Dr Tomball TX 77377) correct"
    why_human: "PDF field visibility requires visual inspection; cannot verify AcroForm rendering programmatically"
  - test: "Open output/trent/2025 1041 Trent Foley Childrens 2021 Super Dynasty Trust.pdf and confirm total tax shows $22,876"
    expected: "Total tax due = $22,876 (corrected from pre-phase $23,121 due to schedule_g cap fix — this is the IRS-correct value per Part V). Trent's EIN 87-6893299 correct."
    why_human: "PDF field visibility requires visual inspection"
  - test: "Confirm output/trent/ contains exactly 5 PDFs (1041, 1041-V, Schedule D, 8949, 8960)"
    expected: "5 files present, no extras"
    why_human: "Directory listing was automated but PDF content fidelity needs human confirmation"
  - test: "Confirm output/chris/ contains exactly 2 PDFs (1041, 1041-V) and NO Schedule D/8949/8960"
    expected: "Only 2025 1041 *.pdf and 2025 1041-V *.pdf present"
    why_human: "Automated check confirms directory contents; user should also open PDF to check fields render"
  - test: "MULTI-07 intent clarification: Trent total tax changed from $23,120.87 to $22,876.28 due to schedule_g cap fix"
    expected: "User confirms the corrected $22,876.28 is acceptable — this is the IRS-correct value matching Part V Line 45 ($19,475.63 + NIIT $3,400.65)"
    why_human: "REQUIREMENTS.md MULTI-07 still says 'unchanged...total tax = $23,120.87' but code produces $22,876.28. The change is correct per IRS Part V worksheet, but the requirement text was not updated. Human must confirm acceptance."
---

# Phase 4: Multi-Trust Support Verification Report

**Phase Goal:** Refactor fill_1041.py for multi-trust support via `--trust` CLI flag, with per-trust config files, conditional form generation (Chris gets Form 1041 only; Trent gets all 4 forms), and a fix for the compute_schedule_g cap bug that manifests when qualified dividends exceed taxable income.

**Verified:** 2026-03-15T05:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from PLAN frontmatter must_haves)

#### Plan 01 Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `fill_1041.py` accepts `--trust` flag (required) to select which trust to process | VERIFIED | `parse_trust_and_year()` at line 49 declares `--trust` as `required=True, choices=["trent","chris"]`. Running without `--trust` exits with argparse error. Tests pass. |
| 2 | `config/2025_chris.json` contains Chris's trust identity, EIN, address, and $500 attorney fees | VERIFIED | File exists. EIN=87-6898455, address=23606 Powder Mill Dr Tomball TX 77377, `attorney_accountant_fees=500.00` confirmed by direct file read. |
| 3 | `config/2025_trent.json` paths updated for renamed data directory (2025_trent/) | VERIFIED | `paths.csv_input="2025_trent/XXXX-X123.CSV"`, `paths.output_dir="output/trent"` confirmed. |
| 4 | `compute_schedule_g` produces correct tax when qualified dividends exceed taxable income | VERIFIED | `capped_preferential = min(preferential_income, taxable_income)` at line 378. Chris dry-run: $779.35 (not $824.41). Test `test_chris_schedule_g_tax` passes. |
| 5 | Chris's manual CSV parses correctly through existing parse_csv state machine | VERIFIED | `2025_chris/dividends.csv` exists with correct 1099-DIV structure. Chris dry-run succeeds with ordinary dividends $9,046 parsed correctly. |

#### Plan 02 Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 6 | Chris's run generates only Form 1041 and 1041-V (no Schedule D, 8949, or 8960) | VERIFIED | Chris dry-run output: "Schedule D: skipped (no transactions)", "Form 8960: skipped (income below NIIT threshold)". `output/chris/` contains exactly 2 PDFs. |
| 7 | Trent's run generates all 5 PDFs (1041, Schedule D, 8949, 8960, 1041-V) | VERIFIED | `output/trent/` contains 5 PDFs: 1041, 1041-V, Schedule D, 8949, 8960. |
| 8 | Output PDFs go to trust-specific subfolders (output/trent/, output/chris/) | VERIFIED | Both directories exist and contain correctly named PDFs. `output_dir.mkdir(parents=True, exist_ok=True)` at line 1166. Output dir comes from per-trust config `paths.output_dir`. |
| 9 | Trent's tax computation is unchanged after multi-trust refactor | PARTIAL | Trent total tax is $22,876.28 (not $23,120.87 stated in MULTI-07). The change is documented as a **correct bug fix** in SUMMARY: the schedule_g cap bug affected Trent too (preferential $105,013.58 > taxable $103,790.67). The new value matches Part V Line 45 canonical answer. REQUIREMENTS.md MULTI-07 was not updated to reflect the corrected amount. Human confirmation needed. |

**Score:** 8/9 truths verified (9th is partially verified with a documentation discrepancy requiring human acceptance)

### Required Artifacts

| Artifact | Provides | Exists | Substantive | Wired | Status |
|----------|----------|--------|-------------|-------|--------|
| `fill_1041.py` | Multi-trust CLI, schedule_g fix, conditional forms | Yes | Yes (1350+ lines, full implementation) | Yes — `parse_trust_and_year()` called in `main()` line 990; `has_transactions`/`needs_*` flags gate compute and PDF output | VERIFIED |
| `config/2025_chris.json` | Chris trust config with identity, brackets, paths | Yes | Yes — all required fields present | Yes — loaded by `load_config(year, "chris")` | VERIFIED |
| `config/2025_trent.json` | Updated Trent config with corrected paths | Yes | Yes — `2025_trent/` and `output/trent` present | Yes — loaded by `load_config(year, "trent")` | VERIFIED |
| `2025_chris/dividends.csv` | Manual CSV with Chris's 1099-DIV data | Yes | Yes — contains `$9,045.68` ordinary and `$8,671.00` qualified dividends | Yes — read by `parse_csv()` via config `paths.csv_input` | VERIFIED |
| `output/chris/2025 1041 Christopher Foley Childrens 2021 Super Dynasty Trust.pdf` | Chris's filled Form 1041 | Yes | Cannot programmatically verify PDF field rendering | N/A — PDF generated | HUMAN NEEDED |
| `output/trent/2025 1041 Trent Foley Childrens 2021 Super Dynasty Trust.pdf` | Trent's filled Form 1041 | Yes | Cannot programmatically verify PDF field rendering | N/A — PDF generated | HUMAN NEEDED |

### Key Link Verification

| From | To | Via | Status | Evidence |
|------|----|-----|--------|----------|
| `fill_1041.py parse_trust_and_year()` | `load_config()` | `--trust` flag parsed first, config loaded as `config/{year}_{trust}.json` | WIRED | `main()` lines 990-993: `trust_name, year = parse_trust_and_year()` then `cfg = load_config(year, trust_name)` |
| `fill_1041.py parse_known_args` pattern | argparse `--trust` | `parser.parse_known_args()` used in `parse_trust_and_year()` | WIRED | Line 58: `known, _ = parser.parse_known_args()` — correctly ignores unknown args for first-pass parsing |
| `compute_schedule_g` | taxable_income cap | preferential_income capped at taxable_income before bucket distribution | WIRED | Lines 376-381: `capped_preferential = min(preferential_income, taxable_income)`, then `twenty_bucket = max(0.0, capped_preferential - zero_bucket - fifteen_bucket)` |
| `fill_1041.py main()` | `fill_form()` calls | `has_transactions` and `needs_form_8960` flags gate which forms are generated | WIRED | Lines 1009-1157: flags computed, guard `if needs_schedule_d/needs_form_8960` blocks gate computation and form_pdfs dict population |
| `fill_1041.py output_dir` | `output/{trust}/` | `cfg paths.output_dir` read from per-trust config | WIRED | Line 1135: `output_dir = Path(args.output_dir)`, which defaults from `cfg["paths"]["output_dir"]` |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| MULTI-01 | 04-01-PLAN | `fill_1041.py` accepts required `--trust` flag (choices: trent, chris) | SATISFIED | `parse_trust_and_year()` declares `required=True, choices=["trent","chris"]`; test passes |
| MULTI-02 | 04-01-PLAN | Per-trust config files exist with trust-specific identity, address, fees, paths; brackets duplicated | SATISFIED | Both `config/2025_trent.json` and `config/2025_chris.json` exist with full independent configs |
| MULTI-03 | 04-01-PLAN | Chris's 1099-DIV data available as manual CSV compatible with `parse_csv()` state machine | SATISFIED | `2025_chris/dividends.csv` with 4-line CSV, parse succeeds in dry-run |
| MULTI-04 | 04-01-PLAN | `compute_schedule_g()` caps preferential income at taxable income (Chris: $779.35, not $824.41) | SATISFIED | Cap applied at line 378; dry-run and unit test confirm $779.35 |
| MULTI-05 | 04-02-PLAN | Forms generated conditionally — Schedule D/8949 only with transactions; 8960 only above NIIT threshold | SATISFIED | Flags `needs_schedule_d`, `needs_form_8949`, `needs_form_8960` gate computation and PDF dict building |
| MULTI-06 | 04-02-PLAN | Output PDFs in per-trust subdirectories (`output/trent/`, `output/chris/`) | SATISFIED | Both subdirectories exist with correctly named PDFs; `output_dir.mkdir(parents=True, exist_ok=True)` |
| MULTI-07 | 04-02-PLAN | Trent's tax computation unchanged after refactor (regression: $23,120.87) | PARTIAL — DOCUMENTATION GAP | Trent dry-run produces $22,876.28. The schedule_g cap fix also corrected Trent's computation (preferential $105,013.58 > taxable $103,790.67 by $1,222.91). $22,876.28 is IRS-correct per Part V Line 45. REQUIREMENTS.md MULTI-07 dollar figure was not updated. Requirement was marked [x] despite the number changing. |

#### Orphaned Requirements

No requirements mapped to Phase 4 in REQUIREMENTS.md that are absent from plan frontmatter. All 7 MULTI-* requirements are covered by plans 01 and 02.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `fill_1041.py` | 1001 | Duplicate step label `# 4.` (appears twice in main()) | Info | No functional impact — cosmetic comment numbering error |

No stubs, TODOs, placeholders, or empty implementations found in modified files.

### Human Verification Required

#### 1. Chris PDF Visual Inspection

**Test:** Open `output/chris/2025 1041 Christopher Foley Childrens 2021 Super Dynasty Trust.pdf`

**Expected:**
- Trust name: "Christopher Foley Childrens 2021 Super Dynasty Trust"
- EIN: 87-6898455
- Address: 23606 Powder Mill Dr, Tomball TX 77377
- Total income: $9,046
- Deductions (attorney fees): $500
- Taxable income: $8,446
- Schedule G tax (line 1a): $779
- Total tax due: $779
- No Schedule D, Form 8949, or Form 8960 attached

**Why human:** AcroForm field rendering with NeedAppearances flag cannot be verified programmatically; field values may be populated but invisible in some viewers.

#### 2. Trent PDF Visual Inspection

**Test:** Open `output/trent/2025 1041 Trent Foley Childrens 2021 Super Dynasty Trust.pdf`

**Expected:**
- Trust name: "Trent Foley Childrens 2021 Super Dynasty Trust"
- EIN: 87-6893299
- Total tax due: $22,876 (Schedule G $19,476 + NIIT $3,401)
- All 5 forms present and filled (1041, Schedule D, 8949, 8960, 1041-V)

**Why human:** PDF rendering verification; also confirm Trent accepts the corrected tax amount ($22,876 vs. prior $23,121).

#### 3. MULTI-07 Dollar Amount Acceptance

**Test:** Review REQUIREMENTS.md MULTI-07 which states "total tax = $23,120.87" but code produces $22,876.28.

**Expected:** User acknowledges the $22,876.28 is the correct IRS amount per Part V Line 45 ($19,475.63 schedule_g + $3,400.65 NIIT). If accepted, REQUIREMENTS.md MULTI-07 should be updated to read "$22,876.28" to close the documentation gap.

**Why human:** Cannot programmatically determine whether the requirement intent allows a corrected value or requires the exact pre-phase amount. The SUMMARY documented this as a correct bug fix, not a regression.

### Gaps Summary

There are no implementation gaps — all code, configs, CSVs, and PDFs exist and are correctly wired. The single open item is a **documentation discrepancy in REQUIREMENTS.md MULTI-07**: the dollar amount was written before the schedule_g cap fix was applied and was never updated after the fix correctly changed Trent's tax from $23,120.87 to $22,876.28. This does not block the phase goal — the computation is IRS-correct and the SUMMARY fully documents the deviation.

Human verification is needed to:
1. Visually confirm both PDFs render correctly with correct field values
2. Explicitly accept the corrected Trent total tax ($22,876.28) and update REQUIREMENTS.md if desired

---

_Verified: 2026-03-15T05:00:00Z_
_Verifier: Claude (gsd-verifier)_
