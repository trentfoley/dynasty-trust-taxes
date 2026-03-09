---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-08
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None — testing is manual (per locked decisions: no pytest) |
| **Config file** | none |
| **Quick run command** | `python fill_pdf.py --help` |
| **Full suite command** | `python fill_pdf.py --fields test_fields.json --form forms/f1041.pdf` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python fill_pdf.py --help`
- **After every plan wave:** Run `python fill_pdf.py --fields <test_json> --form forms/f1041.pdf --output output/test_filled.pdf` then verify visible fields in output
- **Before `/gsd:verify-work`:** All three files exist, `--help` passes, test fill produces a readable PDF
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 0 | CALC-06 | manual | inspect file + grep scripts for hardcoded numbers | ❌ Wave 0 | ⬜ pending |
| 1-01-02 | 01 | 0 | PDF-01 | smoke | `python -c "import json; d=json.load(open('config/2025_fields.json')); print(len(d))"` | ❌ Wave 0 | ⬜ pending |
| 1-01-03 | 01 | 0 | PDF-FILLER | smoke | `python fill_pdf.py --help` | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `config/2025.json` — covers CALC-06
- [ ] `config/2025_fields.json` — covers PDF-01 (real field names from `get_fields()`)
- [ ] `fill_pdf.py` — covers PDF-FILLER
- [ ] `requirements.txt` — `pypdf>=6.7.5`
- [ ] `output/` directory — created by fill_pdf.py at runtime with `os.makedirs(..., exist_ok=True)`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `config/2025.json` contains correct 2025 brackets, no hardcoded values in scripts | CALC-06 | No pytest per locked decisions | Open file, verify bracket values; grep scripts for hardcoded numbers |
| Test fill produces visible-field PDF | PDF-FILLER | Visual verification required | Run fill, open output PDF, confirm fields are visible |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
