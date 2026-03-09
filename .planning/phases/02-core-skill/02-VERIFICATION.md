---
phase: 02-core-skill
verified: 2026-03-08T23:00:00Z
status: passed
score: 19/19 must-haves verified
---

# Phase 2: Core Skill Verification Report

**Phase Goal:** A single Claude skill invocation reads the brokerage CSV, computes all tax schedules correctly, maps values to the known AcroForm fields, and produces a print-ready filled PDF
**Verified:** 2026-03-08
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `--dry-run` prints header showing CSV path, blank form path, output dir | VERIFIED | Dry-run output confirmed: `CSV input: 2025/XXXX-X123.CSV`, `Blank form: forms/f1041.pdf`, `Output dir: output`, `Mode: DRY RUN` |
| 2 | `--dry-run` shows parsed CSV: div_1a=$903.82, div_1b=$903.82, int=$0.12 | VERIFIED | Dry-run output: `Ordinary dividends (Box 1a): $903.82`, `Qualified dividends (Box 1b): $903.82`, `Interest income (Box 1): $0.12` |
| 3 | `--dry-run` shows 2 transactions: one long-term (Box D), one short-term (Box A) | VERIFIED | Dry-run output: `1099-B (2 transactions)` with `[Box D - Long term]` and `[Box A - Short term]` rows |
| 4 | `config/2025_fields.json` contains form_8949 section with real AcroForm field IDs | VERIFIED | Field-value mapping output shows 11+ real field IDs under `[Form 8949 (f8949.pdf)]` |
| 5 | `config/2025_fields.json` schedule_d and form_8960 sections updated from null to real field IDs | VERIFIED | Both sections appear in dry-run field mapping with real IDs (e.g., `f1_22`, `f1_44` for Sch D; `f1_3`, `f1_35` for 8960) |
| 6 | Dry-run shows Schedule D: ST net=$126.97, LT net=$104,109.76 | VERIFIED | `Net short-term capital gain (Part I Line 7): $126.97` and `Net long-term capital gain (Part II Line 15): $104,109.76` |
| 7 | Dry-run shows taxable income=$105,040.67 | VERIFIED | `Taxable income (Line 22): $105,040.67` |
| 8 | Dry-run shows Schedule G tax=$19,728.34 via QD&CG worksheet | VERIFIED | `Schedule G Line 1a tax: $19,728.34` (plan estimated ~$19,722.93; corrected by zero_bucket bug fix in Wave 3; $19,728.34 is correct) |
| 9 | Dry-run shows NIIT=$3,396.85 (3.8% of $89,390.67) | VERIFIED | `NIIT (Line 21 = 3.8%): $3,396.85` |
| 10 | Dry-run shows Schedule B with $0 income distribution deduction | VERIFIED | Schedule B fields in form_1041 mapping: f2_16=0.00, f2_17=0.00, f2_18=0.00, f2_22=0.00 |
| 11 | Validation logic prints "Validation passed" | VERIFIED | `Validation passed` appears in dry-run output |
| 12 | Dry-run field-value mapping shows 4 form groups | VERIFIED | `[Form 1041 (f1041.pdf)]`, `[Schedule D (f1041sd.pdf)]`, `[Form 8960 (f8960.pdf)]`, `[Form 8949 (f8949.pdf)]` |
| 13 | Live mode writes separate filled PDFs to output/ for each form | VERIFIED | All 4 PDFs present in output/ (413KB, 349KB, 146KB, 265KB respectively) |
| 14 | `output/2025 1041 ...pdf` exists after live run | VERIFIED | `output/2025 1041 Trent Foley Childrens 2021 Super Dynasty Trust.pdf` (413,765 bytes) |
| 15 | `output/2025 Schedule D ...pdf` exists after live run | VERIFIED | `output/2025 Schedule D Trent Foley Childrens 2021 Super Dynasty Trust.pdf` (264,460 bytes) |
| 16 | `output/2025 8960 ...pdf` exists after live run | VERIFIED | `output/2025 8960 Trent Foley Childrens 2021 Super Dynasty Trust.pdf` (145,591 bytes) |
| 17 | `output/2025 8949 ...pdf` exists after live run | VERIFIED | `output/2025 8949 Trent Foley Childrens 2021 Super Dynasty Trust.pdf` (348,643 bytes) |
| 18 | `/fill-1041 --dry-run` slash command invokes fill_1041.py | VERIFIED | `.claude/commands/fill-1041.md` exists with bash block: `cd ... && /c/ProgramData/miniconda3/python fill_1041.py $ARGUMENTS` |
| 19 | `--dry-run` writes zero files to output/ | VERIFIED | Code: `_print_dry_run(...)` then `sys.exit(0)` before the live PDF writing loop; output/ timestamps do not change on dry-run |

**Score:** 19/19 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `forms/f1041sd.pdf` | Blank Schedule D (Form 1041) AcroForm PDF | VERIFIED | Present, 108 AcroForm fields confirmed by SUMMARY-01 |
| `forms/f8960.pdf` | Blank Form 8960 AcroForm PDF | VERIFIED | Present, 41 AcroForm fields confirmed by SUMMARY-01 |
| `forms/f8949.pdf` | Blank Form 8949 AcroForm PDF | VERIFIED | Present, 229 AcroForm fields confirmed by SUMMARY-01 |
| `config/2025_fields.json` | Extended field catalog with real IDs | VERIFIED | Real field IDs confirmed in dry-run output for all 3 new form sections |
| `fill_1041.py` | Complete skill: parse, compute, validate, fill PDFs, slash command | VERIFIED | 1,227 lines; all computation functions present and wired in main() |
| `.claude/commands/fill-1041.md` | Claude slash command definition | VERIFIED | Exists with description frontmatter and bash invocation block |
| `output/2025 1041 ....pdf` | Filled Form 1041 (all 3 pages) | VERIFIED | 413,765 bytes; human-verified visually (SUMMARY-03 checkpoint approved) |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `fill_1041.py` | `config/2025.json` | `json.load` in `load_config()` | WIRED | Line 30: `return json.load(f)` loading `config/{year}.json` |
| `fill_1041.py` | `2025/XXXX-X123.CSV` | `parse_csv()` with `csv.reader` | WIRED | Line 130: `reader = csv.reader(f)` |
| `compute_schedule_g()` | `config/2025.json` | `cfg['qdcg_worksheet']` | WIRED | Line 320: `qdcg = cfg["qdcg_worksheet"]` |
| `compute_form_8960()` | `config/2025.json` | `cfg['niit']['threshold']` and `rate` | WIRED | Lines 437-438: `threshold = niit_cfg["threshold"]`, `rate = niit_cfg["rate"]` |
| `validate()` | `csv_data` | re-sum raw CSV values vs computed; halt on diff >= $1.00 | WIRED | Lines 955-983: raw_st_gain/lt_gain re-summed from transactions, `mismatches` list checked |
| `fill_1041.py main()` | `fill_pdf.py` | `subprocess.run([python_exe, 'fill_pdf.py', ...]` | WIRED | Lines 883-884: `subprocess.run([python_exe, "fill_pdf.py", "--fields", tmp, "--form", ..., "--output", ...])` |
| `.claude/commands/fill-1041.md` | `fill_1041.py` | `/c/ProgramData/miniconda3/python fill_1041.py $ARGUMENTS` | WIRED | Line 10 of slash command file |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| PARSE-01 | 02-01 | Parses 1099-DIV: ordinary dividends (Box 1a) and qualified dividends (Box 1b) | SATISFIED | parse_csv() section="DIV" branch; dry-run confirms $903.82/$903.82 |
| PARSE-02 | 02-01 | Parses 1099-INT: interest income (Box 1) | SATISFIED | parse_csv() section="INT" branch; dry-run confirms $0.12 |
| PARSE-03 | 02-01 | Parses 1099-B: each transaction with all fields | SATISFIED | parse_csv() section="B" branch with two-header-row skip; dry-run shows 2 transactions with all fields |
| CALC-01 | 02-01 | Computes Form 8949 rows: Box A (ST covered) or Box D (LT covered), gain/loss per transaction | SATISFIED | compute_schedule_d() splits by form8949_code "A"/"D", computes adjusted_cost + gain_loss per row |
| CALC-02 | 02-02 | Computes Schedule D: net ST and LT capital gain/loss from 8949 rows | SATISFIED | compute_schedule_d() returns st_net=$126.97, lt_net=$104,109.76 confirmed in dry-run |
| CALC-03 | 02-02 | Computes taxable income: gross income minus $100 exemption | SATISFIED | compute_form_1041_page1() returns taxable_income=$105,040.67; exemption from cfg['trust']['exemption'] |
| CALC-04 | 02-02 | Computes Schedule G via QD&CG worksheet | SATISFIED | compute_schedule_g() with 5-bracket QD&CG computation; Line 1a=$19,728.34 |
| CALC-05 | 02-02 | Computes Form 8960 NIIT: 3.8% of lesser of (NII, AGI minus $15,650) | SATISFIED | compute_form_8960() returns niit_amount=$3,396.85 = 3.8% x $89,390.67 |
| CALC-06 | Phase 1 | All bracket thresholds stored in config/YEAR.json — none hardcoded | SATISFIED | fill_1041.py contains zero hardcoded bracket values; all read from cfg['ordinary_income_brackets'], cfg['qdcg_worksheet'], cfg['niit'] |
| CALC-07 | 02-02 | Schedule B computed (zero distribution deduction) and included | SATISFIED | compute_schedule_b() returns all distribution fields = $0; mapped to f2_16–f2_22 in form_1041_map |
| PDF-02 | 02-03 | Fills all Form 1041 page 1 fields from 2024 reference return | SATISFIED | build_field_maps() maps interest, dividends, capital gain, total income, exemption, taxable income, tax due to real field IDs; 22+ fields confirmed in field mapping output |
| PDF-03 | 02-03 | Fills Schedule D fields — ST and LT summary lines | SATISFIED | schedule_d_map populated with Part I/II/III lines; Part V (lines 21-45) computed and filled in live mode |
| PDF-04 | 02-03 | Fills Schedule G fields — tax computation lines | SATISFIED | form_1041_map includes f2_23 (Line 1a), f2_27 (1e), f2_33 (Line 3), f2_35 (NIIT Line 5), f2_42 (total Line 9) |
| PDF-05 | 02-03 | Fills Form 8960 fields — NII and NIIT amount | SATISFIED | form_8960_map includes all NII lines, AGI, threshold, lesser, NIIT (f1_35=$3,396.85) |
| PDF-06 | 02-03 | NeedAppearances flag set (handled by fill_pdf.py) | SATISFIED | fill_form() calls fill_pdf.py which sets NeedAppearances via auto_regenerate=True (Phase 1 contract) |
| PDF-07 | 02-03 | Filled PDF written to output/ | SATISFIED | 4 PDFs in output/ with YYYY FormName EntityName.pdf naming (convention adopted in commit d0e43b6; differs from CONTEXT.md placeholder names but goal is met) |
| SKILL-01 | 02-03 | Invocable via single Claude skill command `/fill-1041` | SATISFIED | .claude/commands/fill-1041.md exists and wires to fill_1041.py $ARGUMENTS |
| SKILL-02 | 02-02/03 | Supports --dry-run mode: outputs all computed values without writing files | SATISFIED | --dry-run flag exits at line 1047 (sys.exit(0)) before PDF writing loop; full output confirmed in dry-run run |
| SKILL-03 | 02-02 | Validates computed totals against CSV source; surfaces mismatch before PDF output | SATISFIED | validate() checks 5 values; mismatch halts with prompt; "Validation passed" confirmed in dry-run |
| SKILL-04 | 02-01 | All file paths use config defaults and can be overridden | SATISFIED | parse_args() reads cfg['paths'] for csv_input and output_dir defaults; --csv, --output-dir, --year flags available |

**All 20 phase 2 requirements satisfied. CALC-06 (phase 1 requirement also tested) confirmed no hardcoded values.**

**Orphaned requirements check:** REQUIREMENTS.md Traceability table maps all Phase 2 requirement IDs exactly to the plans above. No orphaned requirements.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `fill_1041.py` | 1061 | `_print_dry_run` does not pass `sched_d_part5` to `build_field_maps`, so Schedule D Part V field IDs (lines 21-45) are absent from the dry-run field-value mapping section | Info | Dry-run pre-flight does not show Part V lines, but live mode fills them correctly (line 1023 passes `"part5": sched_d_part5`). Not a blocker. |

No TODO/FIXME/placeholder comments found. No empty implementations. No stub return values (`return null`, `return {}`, `return []`). "Live mode not yet implemented" stub from Plan 02-02 was fully replaced in Plan 02-03.

---

## Human Verification Required

### 1. Visual PDF Inspection

**Test:** Open each filled PDF in a browser PDF viewer and confirm all fields are visibly rendered (not blank or greyed-out).
**Expected:**
- `output/2025 1041 Trent Foley Childrens 2021 Super Dynasty Trust.pdf` — Page 1 income lines filled; Page 2 Schedule B ($0 distribution) and Schedule G (tax lines) filled; Page 3 Other Information checkboxes checked
- `output/2025 Schedule D Trent Foley Childrens 2021 Super Dynasty Trust.pdf` — Part I/II/III summary rows filled; Part V lines 21-45 filled; QOF No checkbox checked
- `output/2025 8960 Trent Foley Childrens 2021 Super Dynasty Trust.pdf` — NII lines, AGI, NIIT amount filled
- `output/2025 8949 Trent Foley Childrens 2021 Super Dynasty Trust.pdf` — Box A checked (Page 1 ST row); Box D checked (Page 2 LT row); transaction rows filled
**Why human:** Visual field rendering in PDF viewers depends on NeedAppearances and viewer support — cannot verify programmatically that fields are visible vs. technically-present-but-blank.
**Note:** SUMMARY-03 documents that this checkpoint was already approved by the user on 2026-03-09.

### 2. Slash Command End-to-End Test

**Test:** From Claude chat, run `/fill-1041 --dry-run`.
**Expected:** Claude executes the bash block from .claude/commands/fill-1041.md, which runs fill_1041.py --dry-run from the project root and shows the full dry-run output.
**Why human:** Slash command invocation behavior depends on Claude's command runner — cannot verify the /fill-1041 chat integration programmatically.
**Note:** SUMMARY-03 documents that this test was already confirmed passing by the user on 2026-03-09.

---

## Notable Deviations from Plan (Informational)

1. **Output file naming convention changed** — Plans and CONTEXT.md specified `output/2025_1041_filled.pdf`; actual output uses `output/2025 1041 Trent Foley Childrens 2021 Super Dynasty Trust.pdf`. This was an explicit decision (commit `d0e43b6`). PDF-07 goal (filled PDF in output/) is fully met.

2. **Schedule G tax value differs from plan estimate** — Plan 02-02 specified "~$19,722.93"; actual is $19,728.34. The difference is a bug fix (commit `9405e1b`) correcting the zero_bucket formula. The corrected $19,728.34 is verified correct per MEMORY.md.

3. **`sys.executable` used instead of hardcoded Python path** — Plan 02-03 specified `/c/ProgramData/miniconda3/python` in subprocess.run. Actual uses `sys.executable` because Windows subprocess cannot resolve Unix-style bash paths. This is the correct behavior.

---

## Verification Method

All automated checks executed:
- `python fill_1041.py --dry-run` — full output verified against all ground-truth values
- `grep` checks on fill_1041.py for key patterns (subprocess.run, cfg['qdcg_worksheet'], cfg['niit'], csv.reader, mismatches)
- `ls output/` — all 4 filled PDFs confirmed present with non-trivial file sizes
- `ls forms/` — all 3 IRS blank PDFs confirmed present
- `ls .claude/commands/` — fill-1041.md confirmed present
- `git log` — all 6 SUMMARY-documented commits confirmed present in repository
- Anti-pattern scan: no TODO/FIXME/placeholder/stub patterns found

---

_Verified: 2026-03-08T23:00:00Z_
_Verifier: Claude (gsd-verifier)_
