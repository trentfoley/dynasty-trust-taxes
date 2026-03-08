# Phase 1: Foundation - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Create the three static artifacts that Phase 2 (Core Skill) depends on: `config/2025.json` (tax brackets + trust metadata + file paths), `config/2025_fields.json` (AcroForm field catalog with semantic names mapped to IRS field IDs), and `fill_pdf.py` (thin Python script that writes a filled PDF from a field-value JSON). No tax computation, no skill logic — those are Phase 2.

</domain>

<decisions>
## Implementation Decisions

### Approach pivot
- Primary implementation is a Claude skill, not a Python codebase
- Python exists only for `fill_pdf.py` — the one thing Claude can't do natively (write bytes to a PDF file)
- No pytest, no dataclasses, no Python modules beyond the filler script

### Config schema (config/2025.json)
- **Format**: Named thresholds, not array of tuples — brackets expressed as named rate tiers (e.g., `"10_pct_max": 3150`) for readability and direct reference by name
- **Trust metadata**: Full trust identity in the config — trust name, EIN, trustee name, trustee address — so Claude can fill header fields (Form 1041 Lines A/B/C) without looking them up each run
- **File paths**: All default file paths in config — CSV input, blank form PDF, output directory. Updating one file each year handles the year-over-year refresh.
- **All bracket math in config**: Ordinary income brackets, capital gains brackets, NIIT threshold, trust exemption ($100), and QD&CG worksheet thresholds — no rate values hardcoded anywhere in skill or script

### Field catalog (config/2025_fields.json)
- **Structure**: Grouped by form section — `form_1041_page1`, `schedule_d`, `schedule_g`, `form_8960` top-level keys; each maps semantic names to AcroForm field IDs
- **Semantic mapping in Phase 1**: Foundation does the full mapping work, not just raw field name dump. Cryptic pypdf IDs (e.g., `f1_12`) are mapped to readable semantic names (e.g., `ordinary_dividends`) before Phase 2 starts.
- **Mapping method**: Claude reads `filed_returns/2024 1041.pdf` and `forms/f1041.pdf` side-by-side to identify which AcroForm field IDs correspond to which form line numbers, then writes the semantic mapping

### fill_pdf.py interface
- **Input**: `python fill_pdf.py --fields <json_file> --form <blank_pdf>` — Claude writes field-value pairs to a temp JSON file, passes the file path
- **Error behavior**: Fail hard — exit non-zero if any field name in the JSON is not found in the AcroForm. No silent skips, no warnings-and-continue. Forces the skill to have correct field names.
- **Field types**: Handles both text fields and checkbox fields. Checkbox values use `"Yes"` / `"Off"` convention.
- **NeedAppearances**: Set automatically so filled fields are visible in any PDF viewer

### Python environment
- Minimal — `fill_pdf.py` only needs `pypdf`
- Claude's discretion on whether to use `requirements.txt` or `pyproject.toml`

</decisions>

<specifics>
## Specific Ideas

- The approach pivot is intentional: "keep this very simple, let Claude do the heavy lifting instead of Python"
- Year-over-year reuse: update `config/YEAR.json` with new brackets and file paths, point at new CSV and blank form — the skill and filler are unchanged

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — fresh project, no existing Python code

### Established Patterns
- None yet — Phase 1 establishes the patterns

### Integration Points
- `2025/XXXX-X123.CSV` — primary data source (Phase 2 reads this)
- `forms/f1041.pdf` — blank IRS AcroForm (Phase 1 catalogs fields from this)
- `filed_returns/2024 1041 Trent Foley Childrens 2021 Super Dynasty Trust.pdf` — reference return (Phase 1 uses for semantic field mapping)
- `1041 Schedule G Calculator.xlsx` — Schedule G reference (Phase 2 validates against this)

</code_context>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-03-08*
