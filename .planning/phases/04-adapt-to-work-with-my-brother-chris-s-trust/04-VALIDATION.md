---
phase: 4
slug: adapt-to-work-with-my-brother-chris-s-trust
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None — smoke tests via dry-run |
| **Config file** | none |
| **Quick run command** | `/c/ProgramData/miniconda3/python fill_1041.py --trust chris --dry-run` |
| **Full suite command** | `/c/ProgramData/miniconda3/python fill_1041.py --trust trent --dry-run && /c/ProgramData/miniconda3/python fill_1041.py --trust chris --dry-run` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick run command (Chris dry-run)
- **After every plan wave:** Run full suite command (both trusts)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | N/A | smoke | `/c/ProgramData/miniconda3/python fill_1041.py --trust chris --dry-run` | N/A | ⬜ pending |
| 04-01-02 | 01 | 1 | N/A | regression | `/c/ProgramData/miniconda3/python fill_1041.py --trust trent --dry-run` | N/A | ⬜ pending |
| 04-02-01 | 02 | 2 | N/A | smoke | Check `output/chris/` has only 1041 PDF | N/A | ⬜ pending |
| 04-02-02 | 02 | 2 | N/A | smoke | Chris total tax = $779.35 in dry-run | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `2025_chris/dividends.csv` — manual CSV for Chris's 1099-DIV data
- [ ] `config/2025_chris.json` — Chris's trust config file
- [ ] Rename `config/2025.json` → `config/2025_trent.json`
- [ ] Rename `2025/` → `2025_trent/` and create `2025_chris/`

*Wave 0 data setup is prerequisite for all smoke tests.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| PDF output correctness | N/A | Visual check of filled fields | Open output PDFs, verify trust name/EIN/amounts |
| Chris tax = $779.35 | N/A | Final number validation | Check dry-run output total tax line |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
