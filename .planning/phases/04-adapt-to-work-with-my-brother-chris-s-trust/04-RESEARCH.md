# Phase 4: Adapt to work with my brother Chris's trust - Research

**Researched:** 2026-03-14
**Domain:** Multi-trust refactoring, conditional form generation, IRS tax computation edge cases
**Confidence:** HIGH

## Summary

Phase 4 adapts fill_1041.py to support two trusts (Trent and Chris) via a `--trust` CLI flag, with per-trust config files and conditional form output. The existing codebase is well-structured for this -- config-driven architecture, modular compute functions, and per-form field maps all support parameterization naturally.

The most critical finding is a **latent bug in `compute_schedule_g()`** that only manifests when qualified dividends exceed taxable income (Chris's case: $8,671 QD vs $8,445.68 taxable). The function's `twenty_bucket` is not capped by taxable income, producing $824.41 instead of the correct $779.35. The more rigorous `compute_schedule_d_part5()` handles this correctly but is only invoked when Schedule D is filed. This must be fixed as part of the multi-trust work.

Chris's trust is dividends-only ($9,045.68 ordinary, $8,671.00 qualified), below the NIIT threshold ($15,650), with no capital gains. This means: no Schedule D, no Form 8949, no Form 8960. Only Form 1041 (with Schedule B and Schedule G) is needed.

**Primary recommendation:** Refactor in three stages: (1) config/CLI multi-trust plumbing, (2) fix compute_schedule_g to handle QD > taxable_income, (3) conditional form generation with Chris's CSV data.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Separate config file per trust: `config/2025_trent.json` and `config/2025_chris.json`
- Rename existing `config/2025.json` to `config/2025_trent.json`
- Chris's trust details: Christopher Foley Childrens 2021 Super Dynasty Trust, EIN 87-6898455, fiduciary Christopher B. Foley, Trustee, 23606 Powder Mill Dr, Tomball TX 77377, attorney fees $500
- Same trust structure as Trent's: complex accumulation trust, no distributions, no K-1s
- Tax brackets/thresholds identical (same tax year) -- only trust identity and fees differ
- Chris's brokerage (Vanguard) provides PDF only, no CSV; manual CSV creation acceptable as fallback
- Chris's 2025 data: ordinary dividends $9,045.68, qualified dividends $8,671.00, Section 199A dividends $253.46, interest $0, capital gains $0
- Conditional form output: Chris gets Form 1041 only; Trent gets all 4 forms
- Trust selected via `--trust` flag: `--trust trent` or `--trust chris`
- Short name maps to config: `--trust chris` -> `config/2025_chris.json`
- No "process all" mode -- explicit per-trust invocation
- Rename `2025/` to `2025_trent/` and `2025 Chris/` to `2025_chris/`
- Output in subfolders: `output/trent/` and `output/chris/`
- PDF filenames retain full trust name pattern

### Claude's Discretion
- How to refactor fill_1041.py to accept trust selection (argument parsing changes)
- Whether to share a common config section (brackets/thresholds) or duplicate across trust configs
- PDF extraction implementation approach (if tackled in this phase vs deferred)
- How to handle `config/2025_fields.json` -- shared across trusts (same IRS forms)

### Deferred Ideas (OUT OF SCOPE)
- PDF extraction from Vanguard 1099-DIV
- "Process all trusts" batch mode
- Shared config section for tax brackets/thresholds
</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib | 3.x | argparse, csv, json, subprocess, pathlib | Already in use, no new dependencies |
| pypdf | existing | PDF field filling via fill_pdf.py | Already in use, trust-agnostic |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| config/2025_fields.json | shared | AcroForm field catalog | Same IRS forms for all trusts |
| fill_pdf.py | existing | PDF filler subprocess | Already trust-agnostic, no changes needed |

No new libraries are needed. This phase is pure refactoring of existing code and adding a new config file.

## Architecture Patterns

### Recommended Config Structure

Duplicate brackets/thresholds across trust configs (simplest, no shared config layer needed):

```
config/
  2025_trent.json    # Full config: trust identity + brackets + paths
  2025_chris.json    # Full config: trust identity + brackets + paths (brackets identical)
  2025_fields.json   # Shared AcroForm field catalog (same IRS forms)
```

**Rationale:** Duplication is acceptable because brackets change annually (new file each year anyway), there are only 2 trusts, and a shared-config abstraction adds complexity with no real benefit for 2 consumers. This is also consistent with the deferred ideas list.

### Recommended CLI Pattern

```
python fill_1041.py --trust trent [--year 2025] [--dry-run]
python fill_1041.py --trust chris [--year 2025] [--dry-run]
```

**Implementation:** Parse `--trust` first (before loading config), then load `config/{year}_{trust}.json`. The `--trust` flag should be required (no default) to prevent accidentally running with wrong trust.

### Refactored `load_config` and `parse_args`

```python
def load_config(year, trust_name):
    """Load config/{year}_{trust_name}.json."""
    path = Path("config") / f"{year}_{trust_name}.json"
    if not path.exists():
        print(f"ERROR: Config file not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        return json.load(f)
```

**Argument parsing order change:** Currently `parse_args(cfg)` receives config to get path defaults. With multi-trust, we need `--trust` parsed before config loads. Recommended approach: two-phase parsing.

```python
def parse_trust_and_year():
    """First pass: extract --trust and --year before loading config."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--trust", required=True, choices=["trent", "chris"])
    parser.add_argument("--year", type=int, default=2025)
    known, _ = parser.parse_known_args()
    return known.trust, known.year

def parse_args(cfg, trust_name):
    """Second pass: full argument parsing with config defaults."""
    # ... existing logic plus --trust (already consumed but re-declared for help text)
```

### Conditional Form Generation

The main() function currently always computes and fills all 4 forms. For Chris (dividends-only):

| Form | Trent | Chris | Condition |
|------|-------|-------|-----------|
| Form 1041 (+ Sched B, G) | Yes | Yes | Always |
| Schedule D | Yes | No | Only if transactions exist |
| Form 8949 | Yes | No | Only if transactions exist |
| Form 8960 | Yes | No | Only if total income > NIIT threshold |
| Form 1041-V | Yes | Yes | Always (payment voucher) |

**Detection logic:**
```python
has_transactions = len(csv_data["transactions"]) > 0
needs_schedule_d = has_transactions
needs_form_8949 = has_transactions
needs_form_8960 = page1["total_income"] > cfg["niit"]["threshold"]
```

### Chris's CSV Format

Chris has no brokerage CSV export. A manually-created CSV with just the 1099-DIV data is needed. The simplest approach: create a minimal CSV that the existing `parse_csv()` state machine can process.

```csv
Form 1099DIV
Box,Description,Amount,Total
1a,Ordinary dividends,,"$9,045.68"
1b,Qualified dividends,"$8,671.00",
```

No 1099-INT or 1099-B sections needed (parser returns 0.0 defaults for missing sections).

### Output Directory Structure

```
output/
  trent/
    2025 1041 Trent Foley Childrens 2021 Super Dynasty Trust.pdf
    2025 Schedule D Trent Foley Childrens 2021 Super Dynasty Trust.pdf
    2025 8949 Trent Foley Childrens 2021 Super Dynasty Trust.pdf
    2025 8960 Trent Foley Childrens 2021 Super Dynasty Trust.pdf
    2025 1041-V Trent Foley Childrens 2021 Super Dynasty Trust.pdf
  chris/
    2025 1041 Christopher Foley Childrens 2021 Super Dynasty Trust.pdf
    2025 1041-V Christopher Foley Childrens 2021 Super Dynasty Trust.pdf
```

### Anti-Patterns to Avoid
- **Hardcoding trust names in logic:** All trust-specific values must come from config JSON, not if/else branches
- **Optional --trust flag:** Making it optional with a default would risk running for wrong trust silently
- **Modifying fill_pdf.py:** It is already trust-agnostic; no changes needed

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSV for Chris | Complex PDF parser | Manual CSV creation from 1099-DIV PDF | Only 4 values needed; PDF extraction deferred |
| Shared config layer | Config inheritance/merge system | Duplicate brackets in each trust config | 2 trusts, annual files -- duplication is simpler |
| Form selection logic | Per-trust form lists in config | Runtime detection from data | `has_transactions` and income-vs-threshold checks are reliable and self-documenting |

## Common Pitfalls

### Pitfall 1: compute_schedule_g bug when QD > taxable_income (CRITICAL)

**What goes wrong:** The existing `compute_schedule_g()` does not cap the total preferential tax buckets at taxable_income. When qualified dividends exceed taxable income (Chris: $8,671 QD vs $8,445.68 taxable), the twenty_bucket captures the overflow, producing $824.41 instead of the correct $779.35.

**Root cause:** The bucket calculation uses `preferential_income` (which can exceed taxable_income) as the total to distribute across 0%/15%/20% brackets, but should be implicitly capped at taxable_income.

**Trace with Chris's numbers:**
- taxable_income = 8,445.68, qual_div = 8,671.00, lt_net = 0
- preferential_income = 8,671.00 (exceeds taxable by 225.32)
- ordinary_income = 0
- zero_bucket = 3,250.00
- fifteen_bucket = min(15900, 8445.68) - 0 - 3250 = 5,195.68
- twenty_bucket = max(0, 8671 - 3250 - 5195.68) = **225.32** (should be 0!)
- Tax = 0 + 779.35 + 45.06 = **824.41** (wrong; correct is 779.35)

**Correct behavior (from Schedule D Part V with lt_net=0):**
- l31 = min(taxable_income, preferential_income) = 8,445.68
- l40 (twenty_bucket) = max(0, 8445.68 - 8445.68) = **0**
- Tax = 0 + 779.35 + 0 = **779.35**

**Fix:** Cap preferential_income at taxable_income in compute_schedule_g:
```python
preferential_income = min(qual_div + lt_net_gain, taxable_income)
```
Or equivalently, cap twenty_bucket:
```python
twenty_bucket = max(0.0, min(preferential_income, taxable_income) - zero_bucket - fifteen_bucket)
```

**Why it never showed before:** For Trent, preferential_income ($45,406.67) < taxable_income ($103,790.67). This only triggers when QD is a large fraction of total income with minimal ordinary income.

**Warning signs:** Schedule G tax does not match Part V line 45, or tax exceeds what ordinary rate schedule would produce.

### Pitfall 2: parse_csv with dividends-only CSV

**What goes wrong:** The CSV parser expects Schwab-format CSV sections. A manually-created CSV for Chris must match the exact section headers and column layout.

**How to avoid:** Test the manual CSV against parse_csv() before running the full pipeline. Verify `div_1a`, `div_1b`, `int_box1`, and `transactions` (empty list) in the parsed output.

### Pitfall 3: Schedule D Part V invocation for dividends-only trust

**What goes wrong:** Schedule D Part V is currently always computed in main(). For Chris with no capital gains, Part V is not needed (and not filed). The function still works (lt_net=0, net_combined=0), but the results should not be written to any form.

**How to avoid:** Guard Part V computation and field mapping behind `has_transactions` / `needs_schedule_d`.

### Pitfall 4: Data directory rename breaking git history

**What goes wrong:** Renaming `2025/` to `2025_trent/` could break git history tracking.

**How to avoid:** Use `git mv` for the rename. The `2025 Chris/` directory (with space) also needs renaming to `2025_chris/`.

### Pitfall 5: Output directory must exist before writing

**What goes wrong:** `fill_form()` calls `fill_pdf.py` which writes to the output path. If `output/chris/` does not exist, it will fail.

**How to avoid:** Add `output_dir.mkdir(parents=True, exist_ok=True)` before writing PDFs.

### Pitfall 6: Form 8960 computation for below-threshold trust

**What goes wrong:** `compute_form_8960()` always runs. For Chris ($9,045.68 < $15,650 threshold), NIIT = $0. The function handles this correctly (agi_minus_threshold = 0, niit_amount = 0), but the form should not be filed.

**How to avoid:** Skip Form 8960 computation entirely when not needed, or compute but skip PDF generation. Either works; skipping PDF is simpler and safer.

### Pitfall 7: Schedule B capital_gains_subtraction with zero gains

**What goes wrong:** `compute_schedule_b()` subtracts capital gains from total income for DNI. With no capital gains, `capital_gains_subtraction = 0` and DNI = total income. This is correct behavior -- no issue, just verify.

## Code Examples

### Chris's config file (config/2025_chris.json)

```json
{
  "tax_year": 2025,
  "trust": {
    "name": "Christopher Foley Childrens 2021 Super Dynasty Trust",
    "ein": "87-6898455",
    "fiduciary_name_title": "Christopher B. Foley, Trustee",
    "address_street": "23606 Powder Mill Dr",
    "address_city": "Tomball",
    "address_state": "TX",
    "address_zip": "77377",
    "date_entity_created": "12/14/2021",
    "num_schedules_k1": "0"
  },
  "paths": {
    "csv_input": "2025_chris/dividends.csv",
    "blank_form": "forms/f1041.pdf",
    "output_dir": "output/chris"
  },
  "ordinary_income_brackets": {
    "10_pct_max": 3150,
    "24_pct_max": 11450,
    "35_pct_max": 15650,
    "37_pct_rate": 0.37
  },
  "capital_gains_brackets": {
    "0_pct_max": 3250,
    "15_pct_max": 15900,
    "20_pct_threshold": 15900
  },
  "niit": {
    "rate": 0.038,
    "threshold": 15650
  },
  "qdcg_worksheet": {
    "0_pct_max": 3250,
    "20_pct_threshold": 15900
  },
  "trust_exemption": 100,
  "deductions": {
    "attorney_accountant_fees": 500.00
  },
  "entity_type": "complex_trust",
  "other_information": {
    "q1_tax_exempt_income": "No",
    "q2_contract_assignment": "No",
    "q3_foreign_account": "No",
    "q4_foreign_trust": "No",
    "q5_qualified_residence_interest": "No",
    "q6_sec663b_election": false,
    "q7_sec643e3_election": false,
    "q8_estate_open_2years": false,
    "q9_beneficiaries_skip_persons": "No",
    "q10_form8938_required": "No",
    "q11a_965i_distribution": "No",
    "q11b_beneficiary_agreement": "No",
    "q12_965i_transfer": "No",
    "q13_digital_assets": "No"
  }
}
```

### Chris's manual CSV (2025_chris/dividends.csv)

```csv
Form 1099DIV
Box,Description,Amount,Total
1a,Ordinary dividends,,"$9,045.68"
1b,Qualified dividends,"$8,671.00",
```

### Expected Chris tax numbers

```
Gross income:    $9,045.68
Attorney fees:   $500.00
Exemption:       $100.00
Taxable income:  $8,445.68
Qualified divs:  $8,671.00

Schedule G (QD worksheet):
  Preferential:  $8,445.68 (capped at taxable)
  Ordinary:      $0.00
  0% bucket:     $3,250.00
  15% bucket:    $5,195.68
  20% bucket:    $0.00
  Tax:           $779.35

NIIT:            $0.00 (income below $15,650 threshold)
Total tax:       $779.35
```

### Conditional main() flow

```python
# After parsing CSV and computing page1:
has_transactions = len(csv_data["transactions"]) > 0
needs_schedule_d = has_transactions
needs_form_8949 = has_transactions
needs_form_8960 = page1["total_income"] > cfg["niit"]["threshold"]

# Conditional computation
if needs_schedule_d:
    sched_d = compute_schedule_d(csv_data["transactions"])
    sched_d_part5 = compute_schedule_d_part5(...)
else:
    sched_d = {"st_net": 0, "lt_net": 0, "net_combined": 0, ...}  # zero stub

sched_g = compute_schedule_g(page1["taxable_income"], csv_data["div_1b"], sched_d["lt_net"], cfg)

if needs_form_8960:
    form_8960 = compute_form_8960(csv_data, page1, sched_d, cfg)
else:
    form_8960 = {"niit_amount": 0.0}  # zero stub

total_tax = sched_g["tax_on_taxable_income"] + form_8960.get("niit_amount", 0.0)

# Conditional PDF generation
for form_key in forms_to_generate:
    fill_form(...)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single trust hardcoded | Config-driven single trust | Phase 1-2 | Good foundation for multi-trust |
| `config/2025.json` single file | Per-trust config files | Phase 4 (this phase) | Enables `--trust` flag |
| Always generate all forms | Conditional form generation | Phase 4 (this phase) | Chris gets only Form 1041 |

## Open Questions

1. **Qualified Dividends Tax Worksheet vs Schedule D Part V**
   - What we know: When no Schedule D is filed, IRS instructions say to use the "Qualified Dividends Tax Worksheet" (in Form 1041 instructions) instead of Schedule D Part V. Both compute the same preferential rates but the QD worksheet has fewer lines (no capital gains lines).
   - What's unclear: Whether the existing `compute_schedule_g()` (once the cap bug is fixed) produces identical results to the QD Tax Worksheet.
   - Recommendation: After fixing the cap bug, `compute_schedule_g()` with lt_net=0 will match the QD worksheet. No separate worksheet function is needed. Verify by computing Chris's tax and checking against manual calculation ($779.35).

2. **Trent's config path update**
   - What we know: `config/2025.json` is renamed to `config/2025_trent.json`. The old `2025.json` should be deleted.
   - What's unclear: Whether `config/2025_trent.json` already exists (it does -- confirmed in directory listing).
   - Recommendation: Delete `config/2025.json` (already tracked as deleted in git status) and update `paths.csv_input` in `2025_trent.json` from `2025/XXXX-X123.CSV` to `2025_trent/XXXX-X123.CSV`. Also update `paths.output_dir` to `output/trent`.

3. **Validation for dividends-only trust**
   - What we know: `validate()` checks st_gain and lt_gain against CSV data. For Chris with no transactions, both are 0.
   - What's unclear: Whether the validation raw re-sum loop (lines 1013-1024 in main) handles empty transaction list gracefully.
   - Recommendation: It does -- `sum(... for t in [])` returns 0. But verify.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None detected -- no test infrastructure exists |
| Config file | None |
| Quick run command | `python fill_1041.py --trust chris --dry-run` |
| Full suite command | `python fill_1041.py --trust trent --dry-run && python fill_1041.py --trust chris --dry-run` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| N/A | Multi-trust CLI flag works | smoke | `python fill_1041.py --trust chris --dry-run` | N/A -- dry-run output |
| N/A | Chris tax = $779.35 | smoke | `python fill_1041.py --trust chris --dry-run` (check output) | N/A |
| N/A | Trent still works after refactor | regression | `python fill_1041.py --trust trent --dry-run` | N/A |
| N/A | compute_schedule_g cap fix | unit | Manual trace or dry-run comparison | N/A |
| N/A | Conditional forms: Chris gets 1041 only | smoke | Check output/chris/ has only 2 PDFs (1041 + 1041-V) | N/A |

### Sampling Rate
- **Per task commit:** `python fill_1041.py --trust trent --dry-run` (regression) + `python fill_1041.py --trust chris --dry-run` (new)
- **Per wave merge:** Both trusts dry-run + live PDF generation
- **Phase gate:** Both trusts produce correct PDFs; Chris total tax = $779.35; Trent total tax unchanged ($23,120.87)

### Wave 0 Gaps
- [ ] `2025_chris/dividends.csv` -- manual CSV for Chris's 1099-DIV data
- [ ] `config/2025_chris.json` -- Chris's trust config file
- [ ] `output/chris/` directory (created automatically via mkdir)

## Sources

### Primary (HIGH confidence)
- Existing codebase: fill_1041.py (all compute functions, main flow, field maps)
- Existing config: config/2025_trent.json (trust config structure)
- CONTEXT.md: User decisions on trust details, CLI design, directory layout

### Secondary (MEDIUM confidence)
- [IRS Form 1041 Instructions 2025](https://www.irs.gov/instructions/i1041) -- Schedule G line 1a, QD Tax Worksheet
- [IRS Schedule D Instructions 2025](https://www.irs.gov/pub/irs-pdf/i1041sd.pdf) -- Part V conditions

### Tertiary (LOW confidence)
- QD Tax Worksheet line-by-line steps (could not access full worksheet; verified behavior through Part V trace with lt_net=0)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries, pure refactoring of known code
- Architecture: HIGH -- config-driven patterns already established, multi-trust extension is straightforward
- Pitfalls: HIGH -- compute_schedule_g bug verified by manual trace against Part V logic with Chris's actual numbers
- Tax computation: HIGH -- Chris's expected tax ($779.35) derived from IRS worksheet logic and cross-verified

**Research date:** 2026-03-14
**Valid until:** 2026-04-14 (stable -- IRS forms finalized for 2025 tax year)
