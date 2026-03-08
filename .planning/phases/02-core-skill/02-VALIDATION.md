---
phase: 2
slug: core-skill
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-08
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None — no pytest per locked decisions (CONTEXT.md) |
| **Config file** | none |
| **Quick run command** | `python fill_1041.py --dry-run` |
| **Full suite command** | `python fill_1041.py` (then open all output PDFs in browser) |
| **Estimated runtime** | ~5 seconds (dry-run), ~10 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `python fill_1041.py --dry-run`
- **After every plan wave:** Run `python fill_1041.py` then open all output PDFs in browser
- **Before `/gsd:verify-work`:** Full suite must be green — all 5 output PDFs exist and fields visually confirmed
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-W0-forms | TBD | 0 | PDF-03, PDF-05, CALC-01 | manual | Download PDFs from IRS, run `python fill_pdf.py` enumerate | ❌ Wave 0 | ⬜ pending |
| 2-W0-catalog | TBD | 0 | PDF-03, PDF-05, CALC-01 | smoke | Inspect `config/2025_fields.json` for non-null field IDs | ❌ Wave 0 | ⬜ pending |
| 2-parse | TBD | 1 | PARSE-01/02/03 | smoke | `python fill_1041.py --dry-run` — check DIV/INT/1099-B values | ❌ Wave 0 | ⬜ pending |
| 2-calc-d | TBD | 1 | CALC-01/02 | smoke | `python fill_1041.py --dry-run` — ST=$126.97, LT=$104,109.76 | ❌ Wave 0 | ⬜ pending |
| 2-calc-taxable | TBD | 1 | CALC-03 | smoke | `python fill_1041.py --dry-run` — taxable income=$105,040.67 | ❌ Wave 0 | ⬜ pending |
| 2-calc-g | TBD | 1 | CALC-04 | smoke | `python fill_1041.py --dry-run` — Schedule G tax≈$19,722.93 | ❌ Wave 0 | ⬜ pending |
| 2-calc-niit | TBD | 1 | CALC-05 | smoke | `python fill_1041.py --dry-run` — NIIT=$3,396.85 | ❌ Wave 0 | ⬜ pending |
| 2-calc-b | TBD | 1 | CALC-07 | smoke | `python fill_1041.py --dry-run` — Schedule B zero-fill | ❌ Wave 0 | ⬜ pending |
| 2-pdf-fill | TBD | 2 | PDF-02/03/04/05/07 | manual | Open output PDFs in browser, visually confirm all fields | ❌ Wave 0 | ⬜ pending |
| 2-skill | TBD | 2 | SKILL-01/02/03/04 | smoke | `/fill-1041 --dry-run` from Claude chat | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `fill_1041.py` — main script; covers PARSE-01/02/03, CALC-01/02/03/04/05/07, PDF-02/03/04/05/07, SKILL-01/02/03/04
- [ ] `.claude/commands/fill-1041.md` — slash command file; covers SKILL-01
- [ ] `forms/f1041sd.pdf` — Schedule D (Form 1041) from IRS; required for PDF-03
- [ ] `forms/f8960.pdf` — Form 8960 from IRS; required for PDF-05
- [ ] `forms/f8949.pdf` — Form 8949 from IRS; required for CALC-01
- [ ] Field catalog extensions in `config/2025_fields.json` — Schedule D, Form 8960, Form 8949 real AcroForm field IDs (replaces null placeholders)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Form 1041 Page 1 visually correct | PDF-02 | AcroForm rendering requires visual inspection | Open `output/2025_1041_filled.pdf` in browser PDF viewer; confirm all fields visible |
| Schedule D (Form 1041) visually correct | PDF-03 | AcroForm rendering requires visual inspection | Open `output/2025_sched_d_filled.pdf` in browser PDF viewer |
| Schedule G (Pages 2-3 of f1041.pdf) visually correct | PDF-04 | AcroForm rendering requires visual inspection | Open `output/2025_1041_filled.pdf` pages 2-3 in browser PDF viewer |
| Form 8960 visually correct | PDF-05 | AcroForm rendering requires visual inspection | Open `output/2025_8960_filled.pdf` in browser PDF viewer |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
