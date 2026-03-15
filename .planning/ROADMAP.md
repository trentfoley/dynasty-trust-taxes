# Roadmap: Dynasty Trust Tax Form Filler

## Overview

A two-phase build: foundation first (config + field catalog + thin PDF filler), then the complete Claude skill that does all the work. The skill reads the brokerage CSV, computes all IRS Form 1041 schedules, maps values to AcroForm fields, and calls a minimal Python filler to write the output PDF. No maintained Python codebase — Claude handles all intelligence, Python handles one dumb file-writing task.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Tax bracket config, AcroForm field catalog, and thin PDF filler script (completed 2026-03-08)
- [x] **Phase 2: Core Skill** - Complete Claude skill for CSV parsing, tax computation, field mapping, and PDF output (completed 2026-03-09)

## Phase Details

### Phase 1: Foundation
**Goal**: All static artifacts are in place so the Core Skill has everything it needs: known tax brackets, known AcroForm field names, and a working PDF writer it can call
**Depends on**: Nothing (first phase)
**Requirements**: CALC-06, PDF-01, PDF-FILLER
**Success Criteria** (what must be TRUE):
  1. `config/2025.json` exists and contains 2025 ordinary income brackets, capital gains brackets, NIIT threshold ($15,650), and trust metadata (EIN, trustee name, tax year) — no bracket values are embedded in any skill or script
  2. `config/2025_fields.json` exists and contains all AcroForm field names discovered from `forms/f1041.pdf` via `pypdf PdfReader.get_fields()` — field names are real, not placeholder
  3. `fill_pdf.py` accepts `--fields <json_file>` and `--form <blank_pdf>` and writes a filled PDF to `output/YEAR_1041_filled.pdf` with `NeedAppearances` set — running it against a test field map produces a visible-field PDF
  4. Running `python fill_pdf.py --help` succeeds — the filler is operational with no additional dependencies
**Plans**: 2 plans

Plans:
- [ ] 01-01-PLAN.md — Create config/2025.json (tax brackets + trust metadata), fill_pdf.py (PDF filler), requirements.txt, and smoke test
- [ ] 01-02-PLAN.md — Discover AcroForm fields from forms/f1041.pdf and write semantically-mapped config/2025_fields.json with human verification

### Phase 2: Core Skill
**Goal**: A single Claude skill invocation reads the brokerage CSV, computes all tax schedules correctly, maps values to the known AcroForm fields, and produces a print-ready filled PDF
**Depends on**: Phase 1
**Requirements**: PARSE-01, PARSE-02, PARSE-03, CALC-01, CALC-02, CALC-03, CALC-04, CALC-05, CALC-07, PDF-02, PDF-03, PDF-04, PDF-05, PDF-06, PDF-07, SKILL-01, SKILL-02, SKILL-03, SKILL-04
**Success Criteria** (what must be TRUE):
  1. The skill reads `2025/XXXX-X123.CSV` and correctly extracts: ordinary dividends = $903.82, qualified dividends = $903.82, interest = $0.12, net long-term gain ≈ $104,109.76, net short-term gain ≈ $126.97
  2. Schedule G tax is computed via the Qualified Dividends and Capital Gains Tax Worksheet (not the simple rate table) — worksheet selection is conditional and documented
  3. Form 8960 NIIT equals 3.8% applied to the lesser of net investment income and (AGI minus $15,650)
  4. The skill produces a field-value mapping that covers every field populated on the 2024 reference return and calls `fill_pdf.py` to write `output/2025_1041_filled.pdf`
  5. Dry-run mode prints all computed field values without writing any file
  6. The filled PDF opens in a browser PDF viewer with all values visibly filled
**Plans**: 3 plans

Plans:
- [ ] 02-01-PLAN.md — Download IRS PDFs (Schedule D, Form 8960, Form 8949), extend field catalog, create fill_1041.py skeleton with CSV parser
- [ ] 02-02-PLAN.md — Implement tax computation engine (Schedule D, G, B, Form 8960 NIIT, validation) and full dry-run output
- [ ] 02-03-PLAN.md — Wire live PDF output per form, create /fill-1041 slash command, visual verification checkpoint

### Phase 3: Correct issues found during external review

**Goal:** Apply three precision bug fixes identified by external review — correct Form 8960 Line 19a (use gross income not taxable income), fill Schedule B Line 6 with the correct negative capital gain, and add config-driven Line 14 deduction support
**Requirements**: FIX-01, FIX-02, FIX-03
**Depends on:** Phase 2
**Plans:** 2 plans

Plans:
- [ ] 03-01-PLAN.md — Apply all three bug fixes to fill_1041.py and config/2025.json (deductions support, Form 8960 AGI fix, Schedule B Line 6 fix)
- [ ] 03-02-PLAN.md — Regenerate output PDFs and human-verify corrected values are visible in all forms

### Phase 4: Adapt to work with my brother Chris's trust

**Goal:** Refactor fill_1041.py for multi-trust support via `--trust` CLI flag, with per-trust config files, conditional form generation (Chris gets Form 1041 only; Trent gets all 4 forms), and a fix for the compute_schedule_g cap bug that manifests when qualified dividends exceed taxable income
**Requirements**: MULTI-01, MULTI-02, MULTI-03, MULTI-04, MULTI-05, MULTI-06, MULTI-07
**Depends on:** Phase 3
**Plans:** 2/2 plans complete

Plans:
- [ ] 04-01-PLAN.md — Create Chris config + CSV, update Trent config paths, refactor CLI for --trust flag, fix compute_schedule_g cap bug
- [ ] 04-02-PLAN.md — Implement conditional form generation, per-trust output directories, generate and verify PDFs for both trusts

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 2/2 | Complete   | 2026-03-08 |
| 2. Core Skill | 3/3 | Complete   | 2026-03-09 |
| 3. Correct issues found during external review | 2/2 | Complete | 2026-03-10 |
| 4. Adapt to work with my brother Chris's trust | 2/2 | Complete   | 2026-03-15 |

---
*Created: 2026-03-08*
*Revised: 2026-03-08 — switched from 5-phase Python pipeline to 2-phase Claude skill approach*
*Revised: 2026-03-08 — Phase 1 plans created (2 plans, Wave 1 parallel)*
*Revised: 2026-03-08 — Phase 2 plans created (3 plans, Wave 1-2-3 sequential)*
*Revised: 2026-03-10 — Phase 3 plans created (2 plans, Wave 1-2 sequential)*
*Revised: 2026-03-14 — Phase 4 plans created (2 plans, Wave 1-2 sequential)*
