---
phase: 3
slug: correct-issues-found-during-external-review
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None — project uses stdlib only; dry-run output inspection |
| **Config file** | none — Wave 0 may add tests/test_fixes.py |
| **Quick run command** | `/c/ProgramData/miniconda3/python fill_1041.py --dry-run` |
| **Full suite command** | `/c/ProgramData/miniconda3/python fill_1041.py --dry-run` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `/c/ProgramData/miniconda3/python fill_1041.py --dry-run`
- **After every plan wave:** Run `/c/ProgramData/miniconda3/python fill_1041.py --dry-run`
- **Before `/gsd:verify-work`:** Full dry-run output must show all three corrected values
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | FIX-03 | smoke | `python fill_1041.py --dry-run` — verify taxable_income uses attorney_fees from config | ❌ Wave 0 | ⬜ pending |
| 3-01-02 | 01 | 1 | FIX-03 | smoke | `python fill_1041.py --dry-run` — verify Line 14 and total_deductions fields appear in output | ❌ Wave 0 | ⬜ pending |
| 3-01-03 | 01 | 1 | FIX-01 | smoke | `python fill_1041.py --dry-run` — verify NIIT = $3,400.65 (not $3,396.85) | ❌ Wave 0 | ⬜ pending |
| 3-01-04 | 01 | 1 | FIX-02 | smoke | `python fill_1041.py --dry-run` — verify distributable_net_income = $903.94 and capital_gains_subtraction = -$104,236.73 | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_fixes.py` — unit tests for FIX-01, FIX-02, FIX-03 with known inputs (optional — dry-run smoke tests may suffice)

*If formal pytest tests are out of scope, dry-run output verification serves as acceptance criteria. Dry-run output is deterministic and sufficient for this phase.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Line 14 reduces taxable income with non-zero fee | FIX-03 | No test framework; requires config edit + re-run | Set `attorney_accountant_fees` to a non-zero value in config/2025.json, run dry-run, verify taxable_income decreases by that amount and Schedule G tax decreases accordingly |
| PDF output shows correct values visually | FIX-01, FIX-02, FIX-03 | Visual PDF inspection required | Run without --dry-run, open output PDFs, confirm Form 8960 Line 19a = $105,140.67, Schedule B Line 6 = -$104,236.73 |

---

## Key Verification Values

After all three fixes with `attorney_accountant_fees = 0.00` (zero deductions):

| Field | Before | After (corrected) |
|-------|--------|-------------------|
| Form 8960 Line 19a | $105,040.67 | $105,140.67 |
| NIIT (Form 8960 Line 21) | $3,396.85 | $3,400.65 |
| Total tax | $23,125.19 | $23,129.34 (approx) |
| Schedule B Line 6 | (blank) | -$104,236.73 |
| Schedule B DNI (Line 7) | $105,140.67 | $903.94 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
