# Phase 4: Adapt to work with my brother Chris's trust - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Refactor fill_1041.py and config structure to support multiple trusts. The tool currently handles only Trent's trust — this phase adds Chris's trust as a second consumer using the same engine, with trust selection via CLI flag.

</domain>

<decisions>
## Implementation Decisions

### Trust identity & config
- Separate config file per trust: `config/2025_trent.json` and `config/2025_chris.json`
- Rename existing `config/2025.json` → `config/2025_trent.json`
- Chris's trust details:
  - Name: Christopher Foley Childrens 2021 Super Dynasty Trust
  - Fiduciary: Christopher B. Foley, Trustee
  - EIN: 87-6898455
  - Address: 23606 Powder Mill Dr, Tomball, TX 77377
  - Attorney/accountant fees: $500
- Same trust structure as Trent's: complex accumulation trust, no distributions, no K-1s
- Tax brackets and thresholds are identical (same tax year) — only trust identity and fees differ

### Input data source
- Chris's brokerage (Vanguard) provides PDF only, no CSV
- Support both input paths: CSV parsing (Trent) and PDF extraction (Chris) as future capability; for now, manual CSV creation from PDF data is acceptable as fallback
- Chris's 2025 data (from 1099-DIV PDF):
  - Ordinary dividends (1a): $9,045.68
  - Qualified dividends (1b): $8,671.00
  - Section 199A dividends (5): $253.46
  - Interest: $0.00
  - Capital gains: $0.00
  - Total income: $9,045.68
- No 1099-B transactions — dividends only

### Form generation
- Conditional form output — only generate forms that apply to each trust
- Chris (dividends only, below NIIT threshold): Form 1041 only (with Schedule B, Schedule G)
- Trent (dividends + capital gains, above NIIT threshold): all 4 forms (1041, Schedule D, 8949, 8960)
- Skip Schedule D, Form 8949, and Form 8960 when not needed

### Multi-trust invocation
- Trust selected via `--trust` flag with short name: `--trust trent` or `--trust chris`
- Short name maps to config file: `--trust chris` → `config/2025_chris.json`
- No "process all" mode — explicit per-trust invocation

### Data directory naming
- Rename `2025/` → `2025_trent/` and `2025 Chris/` → `2025_chris/` — no spaces, consistent with short names
- Config `paths.csv_input` updated accordingly in each trust's config

### Output organization
- Output in subfolders per trust: `output/trent/` and `output/chris/`
- Subfolder names match the `--trust` flag short names
- PDF filenames retain the full trust name pattern: `2025 1041 Christopher Foley Childrens 2021 Super Dynasty Trust.pdf`

### Claude's Discretion
- How to refactor fill_1041.py to accept trust selection (argument parsing changes)
- Whether to share a common config section (brackets/thresholds) or duplicate across trust configs
- PDF extraction implementation approach (if tackled in this phase vs deferred)
- How to handle the `config/2025_fields.json` — shared across trusts (same IRS forms)

</decisions>

<specifics>
## Specific Ideas

- Chris's trust is structurally identical to Trent's — same dynasty trust type, same tax year, same creation date (12/14/2021)
- The Vanguard PDF has a clean summary page with all 1099-DIV values clearly labeled — suitable for manual CSV creation or future PDF extraction
- Chris's income ($9,045.68) is below the NIIT threshold ($15,650) — no Form 8960 needed
- No capital gains means Schedule G uses the simple rate table or QD&CG worksheet with zero capital gains — qualified dividends still require the worksheet

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `fill_1041.py`: Complete computation chain (parse_csv → compute_* → build_field_maps → fill PDFs) — needs trust parameterization but core logic is reusable
- `fill_pdf.py`: Thin PDF filler — fully trust-agnostic already, no changes needed
- `config/2025_fields.json`: AcroForm field catalog — shared across trusts (same IRS forms)
- `dollar()` helper in `build_field_maps`: formatting already works for any trust

### Established Patterns
- Config-driven: all trust-specific values read from JSON config — extending to multi-trust is natural
- Computation chain is modular: each `compute_*` function takes config and data, returns results
- Form filling is already per-form with separate field maps — conditional generation maps cleanly

### Integration Points
- `load_config(year)` needs to accept trust short name: `load_config(year, trust)`
- `parse_args()` needs `--trust` flag added
- `paths.csv_input` in config needs per-trust data directory path
- Output directory construction needs trust subfolder: `output/{trust}/`
- `/fill-1041` skill command needs to pass `--trust` argument through

</code_context>

<deferred>
## Deferred Ideas

- PDF extraction from Vanguard 1099-DIV — could be a future phase to automate Chris's data input instead of manual CSV creation
- "Process all trusts" batch mode — run all configured trusts in one command
- Shared config section for tax brackets/thresholds to avoid duplication across trust configs

</deferred>

---

*Phase: 04-adapt-to-work-with-my-brother-chris-s-trust*
*Context gathered: 2026-03-14*
