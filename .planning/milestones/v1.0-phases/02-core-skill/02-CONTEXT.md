# Phase 2: Core Skill - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning

<domain>
## Phase Boundary

A single Claude skill invocation reads `2025/XXXX-X123.CSV`, computes all tax schedules (Schedule D, Schedule G, Form 8960), maps values to known AcroForm fields, and produces print-ready filled PDFs for Form 1041 and all required attachments. No new infrastructure — all static artifacts (config, field catalog, fill_pdf.py) were built in Phase 1.

</domain>

<decisions>
## Implementation Decisions

### Skill invocation
- Skill command: `/fill-1041` with optional `--dry-run` flag and optional year argument
- Default file paths come from `config/YEAR.json`; all overridable via flags (SKILL-04)
- Brief header at start of every run showing: CSV input path, blank form path, output directory

### Output scope — filled PDFs
- Fill ALL forms required to be attached with the Form 1041 filing for this trust, not just Form 1041 itself
- Known required forms: Form 1041 (page 1), Schedule D (Form 1041), Schedule G (Form 1041), Form 8960, Form 8949
- If other attachment forms are required (e.g., Schedule B per CALC-07), include those too
- Blank IRS forms for attachments (e.g., Form 8949) are downloaded from IRS.gov and stored in `forms/`
- Each filled form written to `output/` as a separate PDF (e.g., `output/2025_1041_filled.pdf`, `output/2025_8949_filled.pdf`)

### Mismatch validation (SKILL-03)
- Validate computed totals against CSV source before writing any file
- Tolerance: round-to-dollar — flag if difference ≥ $1.00; allow <$1.00 rounding differences
- Validated totals: ordinary dividends (1099-DIV Box 1a), qualified dividends (Box 1b), interest (1099-INT Box 1), net short-term gain, net long-term gain
- On mismatch: halt, show expected vs computed diff, require explicit user confirmation ("yes") to proceed
- Even on halt, display what the field values would be (acts as implicit dry-run output)

### Execution feedback (normal mode)
- Step-by-step progress lines as each stage completes:
  - `Parsed CSV ✓` — after extracting all 1099 sections
  - `Computed Schedule D ✓` — after netting gains/losses
  - `Computed Schedule G ✓` — after QD&CG worksheet
  - `Computed Form 8960 ✓` — after NIIT calculation
  - `Validation passed ✓` (or halt on mismatch)
  - `PDF written: output/2025_1041_filled.pdf ✓` — per form
- Final summary after all PDFs written: gross income, taxable income, Schedule G tax, NIIT, total tax due, output file paths
- On failure: show which steps completed ✓ then the specific error for the failing step

### Dry-run output format (SKILL-02)
- Invoked with `--dry-run` flag; no files written
- Output structure:
  1. Computation steps with intermediate values (gross income, taxable income, bracket lookups, etc.)
  2. Field-value mapping grouped by form section: [Form 1041 Page 1], [Schedule D], [Schedule G], [Form 8960], [Form 8949]
- Validation runs in dry-run too — same mismatch check before displaying output
- Useful as a pre-flight check before the real run

### Schedule D / Form 8949 detail
- 296 1099-B transactions (all VGT shares, various acquisition dates, sold 12/24/2025)
- Internal computation: process each transaction individually for accuracy
- Dry-run display: one row per acquisition-date lot (group transactions with same acquisition date) showing: acquisition date, proceeds, cost basis, gain/loss, short/long-term flag
- Wash sale disallowed amounts: add back to cost basis per IRS Form 8949 Box 1g instructions — IRS-correct treatment
- Verify all transactions are "covered" (known basis); flag any uncovered transactions as a warning
- Form 8949 rows organized as CALC-01 specifies: Box A (short-term covered), Box D (long-term covered)

### Claude's Discretion
- Exact Schedule G QD&CG worksheet step-by-step implementation details
- How to download and store blank IRS forms for attachments (manual pre-step vs skill-automated)
- Schedule B (Form 1041) handling — researcher to determine if it's embedded in the 1041 PDF or a separate download needed
- Whether to produce a single merged PDF or separate files per form

</decisions>

<specifics>
## Specific Ideas

- The skill should feel like a complete pre-flight check when run with `--dry-run` — user can verify all numbers before committing to writing files
- "Include all forms required to be attached with the 1041" — completeness is a priority; a partial return is not useful
- Year-over-year reuse: update `config/YEAR.json` with new year's paths and brackets, point at new CSV — skill and filler unchanged

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `fill_pdf.py`: accepts `--fields <json_file> --form <blank_pdf> --output <path>`; handles text fields and checkboxes; hard-fails on unknown field names; sets NeedAppearances
- `config/2025.json`: brackets (ordinary, capital gains, NIIT threshold, QD&CG worksheet), trust metadata, file paths
- `config/2025_fields.json`: semantic name → AcroForm field ID for Form 1041 page 1, Schedule D, Schedule G, Form 8960; grouped by form section

### Established Patterns
- Hard-fail on any unknown field name (collect all errors before exit)
- Config-driven: no bracket values hardcoded; all paths from config
- Checkbox values use `"Yes"` / `"Off"` — fill_pdf.py translates to actual On-state at runtime
- Separate PDFs: Schedule D and Form 8960 are separate from f1041.pdf; field IDs for each are in their respective sections of 2025_fields.json

### Integration Points
- `2025/XXXX-X123.CSV` — primary data source; contains 1099-DIV, 1099-INT, 1099-B sections
- `forms/f1041.pdf` — blank AcroForm for main form; already cataloged in 2025_fields.json
- `forms/` directory — additional blank forms (Form 8949, etc.) need to be added here
- `fill_pdf.py` — skill calls this for each form after computing field values
- `output/` — all filled PDFs written here

</code_context>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope (Form 8949 addition was incorporated into Phase 2 scope per user decision)

</deferred>

---

*Phase: 02-core-skill*
*Context gathered: 2026-03-08*
