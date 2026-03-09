# Milestones

## v1.0 MVP (Shipped: 2026-03-09)

**Phases completed:** 2 phases, 5 plans
**Files changed:** 41 | **Python LOC:** ~1,352 | **Timeline:** 1 day (2026-03-08)
**Git range:** 5525d5b → 0a6bfe2

**Key accomplishments:**
1. Tax bracket config (`config/2025.json`) + `fill_pdf.py` AcroForm writer with runtime checkbox translation
2. Complete AcroForm field catalog for Form 1041 via pypdf discovery → `config/2025_fields.json`
3. Three IRS PDFs downloaded (Sch D, Form 8960, Form 8949) + `fill_1041.py` with state-machine CSV parser
4. Full tax computation engine: Schedule D, G (QD&CG worksheet), B, Form 8960 NIIT, dry-run validation
5. Live PDF output for all 4 forms + `/fill-1041` slash command, visually verified

**Verification:** 19/19 must-haves verified (automated) + human visual checkpoint approved

---

