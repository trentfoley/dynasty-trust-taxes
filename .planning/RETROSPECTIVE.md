# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-09
**Phases:** 2 | **Plans:** 5 | **Sessions:** ~3

### What Was Built
- `config/2025.json` — all 2025 tax bracket thresholds, trust metadata, file paths
- `fill_pdf.py` — thin AcroForm PDF filler with runtime checkbox translation (no hardcoded On-state values)
- `config/2025_fields.json` — complete semantic-to-field-ID catalog for Form 1041 + 3 attachment forms
- `fill_1041.py` — complete tax engine: CSV parser, Schedule D, G (QD&CG worksheet), B, Form 8960 NIIT, validation, dry-run, PDF fill for all 4 forms
- `.claude/commands/fill-1041.md` — `/fill-1041` slash command for one-command invocation

### What Worked
- **Config-first architecture:** All bracket values, paths, and field IDs externalized to config — zero hardcoding in scripts made the tool immediately year-agnostic
- **GSD wave structure:** Sequential wave execution (wave 1 → 2 → 3 within Phase 2) enforced natural dependency order without coordination overhead
- **Human checkpoint placement:** Putting visual PDF verification at the end of Phase 2 (after all computation was automated) was the right gate — caught no bugs but confirmed the output correctly
- **Dry-run mode first:** Building `--dry-run` before live PDF output made debugging computation much faster — could verify all values without touching files
- **pypdf field discovery:** Running `PdfReader.get_fields()` once and storing results in config eliminated all runtime field-name guessing

### What Was Inefficient
- **Multiple field ID corrections:** Several field IDs (Schedule D Part V, Form 8949 column totals, Form 1041 header) had to be corrected after initial mapping — the field catalog needed a second human-verify pass that wasn't planned
- **Rework on compute_schedule_g:** `zero_bucket` formula was wrong (ordinary income must fill lower brackets first) — caught by running against real data, could have been caught earlier with a unit test against the Excel reference calculator
- **Duplicate decisions in STATE.md:** Some decisions were logged twice (1099-B two-header-row skip) due to multiple plan sessions touching the same area

### Patterns Established
- `sys.executable` in subprocess calls — required on Windows; never hardcode interpreter paths
- Runtime /_States_ checkbox translation — makes `fill_pdf.py` resilient across IRS form versions
- State-machine CSV parser with section detection — handles Schwab multi-section CSV cleanly
- Separate output PDF per form — each IRS attachment is a standalone AcroForm, not embedded
- `YYYY FormName EntityName.pdf` output naming convention

### Key Lessons
1. **Enumerate AcroForm fields from the actual PDFs before planning field mappings** — the IRS form field IDs are not predictable from form instructions; discovery must precede implementation
2. **Test Schedule G against a known reference (Excel calculator) before wiring to PDF** — the worksheet has enough branching logic that a manual spot-check on real data is essential
3. **For tax tools, dry-run verification of every computed line is worth the extra task** — the $5.42 zero_bucket bug was only caught because dry-run made all intermediate values visible

### Cost Observations
- Model mix: ~100% Sonnet 4.6 (claude-sonnet-4-6)
- Sessions: ~3
- Notable: GSD executor subagents completed computation-heavy plans (02-02, 02-03) in single sessions with no backtracking

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | ~3 | 2 | Initial build — established config-first + thin-filler architecture |

### Cumulative Quality

| Milestone | Verification | Coverage | Notes |
|-----------|-------------|----------|-------|
| v1.0 | 19/19 must-haves | Manual visual + dry-run | No automated unit tests yet |

### Top Lessons (Verified Across Milestones)

1. Enumerate AcroForm fields from actual PDFs before any field-mapping work
2. Dry-run mode is essential for tax computation tools — makes all intermediate values auditable
