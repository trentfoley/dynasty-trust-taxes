# Phase 03: Correct Issues Found During External Review - Research

**Researched:** 2026-03-09
**Domain:** Python tax computation logic — `fill_1041.py` and `config/2025.json`
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Form 8960 AGI fix (Line 19a)**
- Line 19a must use **gross income = $105,140.67** (Form 1041 line 17), NOT taxable income ($105,040.67)
- The $100 complex trust exemption must NOT be subtracted before feeding 8960
- Cascading corrected values: Line 19c = $89,490.67, Line 20 = $89,490.67, Line 21 NIIT = $3,400.65
- Net tax change: +$3.80 underpayment

**Schedule B Line 6 fix (capital gains)**
- Line 6 must be filled with **-$104,236.73** (negative of net total capital gain: $104,109.76 LT + $126.97 ST)
- This is the gain from Form 1041 line 4, entered as a negative per IRS instructions
- Corrected Line 7 (DNI) = $903.94 ($105,140.67 - $104,236.73)
- Tax impact: none — but DNI must be correct for audit-readiness

**Deductions support**
- Add `deductions.attorney_accountant_fees` to `config/2025.json`
- Wire into `compute_form_1041_page1()` to fill **Line 14** on Form 1041
- Line 14 flows into total deductions → reduces taxable income → cascades through Schedule G, NIIT, and all downstream computations
- Only Line 14 (attorney/accountant fees) supported — no other deduction lines

### Claude's Discretion
- Exact field ID for Form 1041 Line 14 (look up from `config/2025_fields.json`)
- Whether deductions reduce NIIT base (they should — professional fees are allocable against NII)
- How to handle zero deduction case (skip field or write $0)

### Deferred Ideas (OUT OF SCOPE)
- **Form 2210 underpayment penalty** — Requires prior-year tax data; consult tax advisor
- **Tax distribution strategy** — Separate decision; involves trust instrument review
- **Fiduciary fees (Line 11) and other deductions (Line 15)** — Not needed for 2025
</user_constraints>

---

<phase_requirements>
## Phase Requirements

Phase 3 requirements are not yet registered in REQUIREMENTS.md. The three fixes below constitute the full scope. They will be tracked here for planner use.

| ID | Description | Research Support |
|----|-------------|-----------------|
| FIX-01 | Form 8960 Line 19a: use gross income (`total_income`) not taxable income | `compute_form_8960()` line 445 identified — change `page1["taxable_income"]` to `page1["total_income"]` |
| FIX-02 | Schedule B Line 6: fill with negative net capital gain | `compute_schedule_b()` lines 295–310 identified — add `capital_gains_subtraction` field; wire to `gain_from_page1_line4` (f2_13) and `distributable_net_income` (f2_14) in `build_field_maps()` |
| FIX-03 | Line 14 deductions: read `deductions.attorney_accountant_fees` from config and wire to Form 1041 Line 14 | Field `attorney_accountant_fees` = `f1_32[0]` confirmed in `2025_fields.json`; cascade affects taxable_income → Schedule G → Form 8960 → total_tax |
</phase_requirements>

---

## Summary

Phase 3 is a precision bug-fix phase. All three fixes are isolated changes to existing Python functions and one JSON config file. No new infrastructure, forms, or architectural patterns are involved.

Fix 1 (Form 8960) is a one-line change: `page1["taxable_income"]` → `page1["total_income"]` at line 445 of `fill_1041.py`. The IRS instructions for Form 8960 Part III trusts/estates state Line 19a = Form 1041 Line 17 (adjusted total income), not Line 23 (taxable income). The $100 exemption subtraction occurs after the NIIT threshold subtraction and must not contaminate Line 19a.

Fix 2 (Schedule B Line 6) requires adding a `capital_gains_subtraction` field to `compute_schedule_b()` equal to `-1 * (st_gain + lt_gain)` and wiring it to the `gain_from_page1_line4` field (f2_13) in `build_field_maps()`. The DNI computation (`distributable_net_income`) also needs updating to `total_income + capital_gains_subtraction`. This is a $0 tax impact fix for audit-readiness.

Fix 3 (deductions) is the most cascading. Adding `attorney_accountant_fees` to config and `compute_form_1041_page1()` changes `taxable_income`, which propagates through `compute_schedule_g()`, `compute_schedule_d_part5()`, and `compute_form_8960()`. If the deduction is zero, the net effect is no change to current outputs. The deduction should reduce the NIIT base because professional fees paid by the trust are allocable against net investment income per Reg. §1.1411-10.

**Primary recommendation:** Execute the three fixes in dependency order — deductions first (because it changes taxable_income), then Form 8960 (because it uses gross_income independently), then Schedule B (fully independent). Verify by running `--dry-run` and checking summary totals match the corrected values in CONTEXT.md.

---

## Standard Stack

No new libraries required. All changes use existing stdlib and project patterns.

### Core (unchanged)
| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.x (miniconda3) | Runtime — `/c/ProgramData/miniconda3/python` |
| `fill_1041.py` | project | Computation + field mapping logic |
| `config/2025.json` | project | Tax year config including new `deductions` section |
| `config/2025_fields.json` | project | AcroForm field ID catalog |
| `fill_pdf.py` | project | Low-level PDF filler (no changes needed) |

### Installation
No new packages needed.

---

## Architecture Patterns

### Established Computation Pattern
```
parse_csv → compute_schedule_d → compute_form_1041_page1
  → compute_schedule_b → compute_schedule_g → compute_schedule_d_part5
  → compute_form_8960 → build_field_maps → fill PDFs
```

Dependencies relevant to Fix 3 (deductions):
- `compute_form_1041_page1` produces `taxable_income` used by `compute_schedule_g`, `compute_schedule_d_part5`, and `compute_form_8960`.
- If Line 14 deduction > 0, ALL downstream computations automatically receive the correct reduced `taxable_income` since they consume `page1["taxable_income"]`.
- Form 8960 Fix 1 uses `page1["total_income"]` (gross income, not taxable) — this is unaffected by deductions.

### Pattern: Config-Driven Values
All dollar values consumed from config, never hardcoded. New deduction follows same pattern:
```python
# In config/2025.json
"deductions": {
    "attorney_accountant_fees": 0.00
}

# In compute_form_1041_page1():
deductions = cfg.get("deductions", {})
attorney_fees = float(deductions.get("attorney_accountant_fees", 0.0))
```

### Pattern: Field Map via Semantic Name
```python
# In build_field_maps() p1_mappings dict:
"attorney_accountant_fees": computed.get("attorney_accountant_fees"),
```
Semantic name `attorney_accountant_fees` already exists in `config/2025_fields.json` at:
```
"attorney_accountant_fees": "topmostSubform[0].Page1[0].f1_32[0]"
```
No new field catalog entry required.

### Pattern: Schedule B Capital Gains Subtraction
IRS Form 1041 Schedule B Line 6: "Enter amount from Schedule D (Form 1041), line 19 (net long-term capital gain or loss)" — entered as negative when a gain, because it is subtracted from total income to arrive at DNI (which distributable income excludes capital gains retained in corpus).

Field mapping: semantic key `gain_from_page1_line4` → AcroForm field `f2_13[0]` (confirmed in `2025_fields.json` line 235).

Current `compute_schedule_b()` does NOT populate `gain_from_page1_line4` at all. It needs to be added to both the return dict and the `sched_b_mappings` in `build_field_maps()`.

### Anti-Patterns to Avoid
- **Using taxable_income for Form 8960 Line 19a:** Confirmed bug. IRS instructions explicitly say Line 19a for trusts = Form 1041 Line 17 (adjusted total income / gross income), not Line 23 (taxable income).
- **Omitting capital gains sign flip on Schedule B Line 6:** The capital gain amount must be negative on Schedule B. Entering it as positive would inflate DNI by twice the gain.
- **Hardcoding deduction amounts:** All deduction values must come from `config/2025.json`, not from literals in the script.
- **Forgetting to update `total_deductions` and `deductions_total_lines18_21`:** When Line 14 deductions are added, the Page 1 subtotals and Line 22 (total of lines 18-21) must also update correctly.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| NIIT threshold subtraction | Custom threshold logic | Existing `cfg["niit"]["threshold"]` — already correct |
| AcroForm field ID lookup | String manipulation | `config/2025_fields.json` — semantic names already mapped |
| PDF filling | New PDF writer | Existing `fill_pdf.py` subprocess call — no changes needed |

---

## Common Pitfalls

### Pitfall 1: Form 8960 Line 19c Cascades Must Be Verified
**What goes wrong:** Changing Line 19a changes Line 19c (= Line 19a - Line 19b, where 19b = 0 for this trust), which changes Line 20 (lesser of NII or 19c), which changes Line 21 (NIIT).
**Why it happens:** The compute function chains these computations. After the fix: 19a = $105,140.67, 19c = $89,490.67 (minus $15,650 threshold), Line 21 NIIT = $3,400.65 (vs current $3,396.85).
**How to avoid:** Confirm dry-run shows the three corrected values exactly as specified in CONTEXT.md. The diff is +$3.80 in NIIT.
**Warning signs:** NIIT still reads $3,396.85 after the fix means the wrong variable is still being used.

### Pitfall 2: Schedule B `distributable_net_income` Must Also Update
**What goes wrong:** Line 7 (DNI) = adjusted total income − capital gains subtraction. Current code sets `distributable_net_income = page1["total_income"]` without subtracting the capital gain. After fix, DNI = $903.94.
**Why it happens:** `compute_schedule_b()` currently uses total_income directly for DNI. The Schedule B Line 6 addition must also flow into the DNI calculation.
**How to avoid:** In `compute_schedule_b()`, compute `capital_gains_subtraction = -(st_net + lt_net)` (passed in as new parameter or derived from `page1["capital_gain_loss"]`), then `distributable_net_income = total_income + capital_gains_subtraction`.
**Warning signs:** `distributable_net_income` still equals `total_income` ($105,140.67) rather than $903.94.

### Pitfall 3: `compute_schedule_b` Needs Capital Gain Input
**What goes wrong:** `compute_schedule_b(page1)` currently only takes `page1` as argument. `page1["capital_gain_loss"]` already contains `sched_d["net_combined"]` (= $104,236.73). This is the right value — no new parameter needed.
**Why it happens:** `page1["capital_gain_loss"]` is populated in `compute_form_1041_page1()` from `sched_d["net_combined"]`. The subtraction is `-page1["capital_gain_loss"]` (sign already correct since capital_gain_loss is positive when it's a gain).
**Warning signs:** If capital_gain_loss is ever negative (loss year), the line 6 amount would be positive — which is correct IRS treatment, so the formula handles both cases.

### Pitfall 4: Deduction Cascade Through `total_deductions` on Page 1
**What goes wrong:** Form 1041 Page 1 has intermediate subtotals: `total_deductions` (Line 16) and `deductions_total_lines18_21` (Line 22). Currently Line 16 is not populated because all deduction lines are zero. With attorney fees, Line 16 must equal Line 14.
**Why it happens:** `build_field_maps()` currently has no mapping for `total_deductions`. It must be added.
**How to avoid:** Add `total_deductions` to `p1_mappings` in `build_field_maps()`, computed as the sum of all active deduction lines (currently just attorney_accountant_fees).
**Warning signs:** Line 16 blank while Line 14 has a value — the form will not cross-check correctly on review.

### Pitfall 5: Zero Deduction Case — Skip or Write $0
**What goes wrong:** If `attorney_accountant_fees = 0.0`, writing "$0.00" to Line 14 is harmless but noisy. Current pattern uses `if fid and val is not None` — a value of 0.0 is not None, so it would write "$0.00".
**How to avoid:** Either (a) exclude zero deduction lines from the field map (only write if > 0), or (b) write $0.00 consistently. Either approach is acceptable; choose (b) for consistency with how other zero-valued lines are handled (e.g., exemption always fills $100).
**Warning signs:** This is a style question, not a correctness issue. Document the chosen behavior.

---

## Code Examples

### Fix 1: Form 8960 Line 19a (one-line change)

Current code in `compute_form_8960()` at line 445:
```python
# CURRENT (WRONG):
agi_undistributed_nii = page1["taxable_income"]

# CORRECTED:
agi_undistributed_nii = page1["total_income"]  # Form 1041 Line 17 = gross income
```

After fix, corrected values flow automatically:
- `agi_minus_threshold` = $105,140.67 - $15,650 = $89,490.67
- `lesser_of_nii_or_agi_excess` = min($105,140.67, $89,490.67) = $89,490.67
- `niit_amount` = $89,490.67 × 0.038 = $3,400.65

### Fix 2: Schedule B Line 6 (compute_schedule_b changes)

Current function signature: `compute_schedule_b(page1)`
`page1` already contains `capital_gain_loss` = $104,236.73 (positive = gain)

```python
# UPDATED compute_schedule_b():
def compute_schedule_b(page1):
    capital_gain = page1["capital_gain_loss"]          # positive gain from Sched D
    capital_gains_subtraction = -round(capital_gain, 2) # Line 6: negative per IRS instructions
    dni = round(page1["total_income"] + capital_gains_subtraction, 2)  # Line 7

    return {
        "adjusted_total_income": page1["total_income"],
        "accounting_income": page1["total_income"],
        "capital_gains_subtraction": capital_gains_subtraction,  # NEW: Line 6
        "distributable_net_income": dni,                          # UPDATED: Line 7
        "income_required_to_be_distributed": 0.0,
        "other_amounts_distributed": 0.0,
        "total_distributions": 0.0,
        "income_distribution_deduction": 0.0,
    }
```

In `build_field_maps()`, add to `sched_b_mappings`:
```python
"gain_from_page1_line4": computed.get("sched_b_capital_gains_subtraction"),
```

In the computed dict merge block (around line 1027):
```python
"sched_b_capital_gains_subtraction": sched_b["capital_gains_subtraction"],
```

The `gain_from_page1_line4` semantic key maps to `f2_13[0]` (confirmed in `2025_fields.json`).

### Fix 3: Deductions (config + compute + field map)

In `config/2025.json`, add after `trust_exemption`:
```json
"deductions": {
    "attorney_accountant_fees": 0.00
}
```

In `compute_form_1041_page1()`, add deduction reading and subtract from taxable income:
```python
deductions = cfg.get("deductions", {})
attorney_fees = round(float(deductions.get("attorney_accountant_fees", 0.0)), 2)
total_deductions_line16 = attorney_fees  # only Line 14 active for 2025
taxable_income = round(total_income - total_deductions_line16 - exemption, 2)

return {
    ...existing keys...,
    "attorney_accountant_fees": attorney_fees,
    "total_deductions": total_deductions_line16,
    "taxable_income": taxable_income,
}
```

In `build_field_maps()` `p1_mappings`, add:
```python
"attorney_accountant_fees": computed.get("attorney_accountant_fees"),
"total_deductions":         computed.get("total_deductions"),
```

Field IDs (confirmed from `2025_fields.json`):
- `attorney_accountant_fees` → `topmostSubform[0].Page1[0].f1_32[0]`
- `total_deductions` → `topmostSubform[0].Page1[0].f1_35[0]`

---

## NIIT and Deductions: Allocability Analysis

**Question (Claude's Discretion):** Do attorney/accountant fees reduce the NIIT base?

**Finding (MEDIUM confidence — IRS Reg. reference, not directly verified via Context7):**
Treasury Regulation §1.1411-10 and IRS Publication 550 guidance indicate that deductions properly allocable to net investment income reduce the NII for Form 8960. Professional fees (attorney/accountant fees) paid by a trust in connection with investment management are generally allocable against investment income. For a trust whose only income is investment income, the fees are fully allocable against NII.

**Practical impact for Form 8960:**
Form 8960 Line 9b allows deduction of "investment expenses" and Line 9c for certain state/local taxes. However, IRS Form 8960 instructions for trusts indicate that the computation works from total NII gross (Lines 1-8), then deductions are subtracted at Lines 9a-9c to arrive at Line 12 (Net Investment Income). Attorney/accountant fees would appear on Form 8960 Line 9b.

**Decision for this phase:**
Given the complexity of modifying Form 8960 NII deduction lines (which are not currently populated and would require new field mappings), and that the deduction amount is TBD (set in config), the planner should implement Fix 3 as:
1. Line 14 on Form 1041 reduces taxable income (and thus Schedule G tax)
2. The NIIT base (total NII on Form 8960) is NOT reduced in this phase — Form 8960 Lines 9a-9c are deferred
3. This is a conservative approach: slightly overstates NIIT, is audit-safe

The CONTEXT.md does not lock a decision on NIIT allocability, so this is Claude's Discretion. The conservative approach (no NIIT reduction) is recommended for this phase.

---

## Validation Architecture

`workflow.nyquist_validation` is `true` in `.planning/config.json` — this section is required.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None detected — project uses stdlib only, no test framework present |
| Config file | None — see Wave 0 gaps |
| Quick run command | `/c/ProgramData/miniconda3/python fill_1041.py --dry-run` |
| Full suite command | `/c/ProgramData/miniconda3/python fill_1041.py --dry-run` (same — no automated test suite) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FIX-01 | Form 8960 Line 19a = $105,140.67 (gross income) | smoke | `python fill_1041.py --dry-run` — check NIIT = $3,400.65 | ❌ Wave 0 |
| FIX-01 | NIIT amount = $3,400.65 (not $3,396.85) | smoke | `python fill_1041.py --dry-run` — check total tax = $23,129.34 (not $23,125.19) | ❌ Wave 0 |
| FIX-02 | Schedule B Line 6 = -$104,236.73 | smoke | `python fill_1041.py --dry-run` — check `sched_b_capital_gains_subtraction` | ❌ Wave 0 |
| FIX-02 | DNI = $903.94 | smoke | `python fill_1041.py --dry-run` — check `distributable_net_income` | ❌ Wave 0 |
| FIX-03 | Line 14 reads from config | unit | Manual: set attorney_fees > 0, run dry-run, verify taxable_income decreases | ❌ Wave 0 |
| FIX-03 | taxable_income cascades correctly | smoke | Run dry-run with non-zero fees, verify Schedule G tax decreases proportionally | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `/c/ProgramData/miniconda3/python fill_1041.py --dry-run`
- **Per wave merge:** `/c/ProgramData/miniconda3/python fill_1041.py --dry-run` (full dry-run covers all computed values)
- **Phase gate:** Dry-run output shows all three corrected values before `/gsd:verify-work`

### Key Verification Values
After all three fixes with `attorney_accountant_fees = 0.00` (zero deductions):
- Form 8960 Line 19a: `$105,140.67`
- NIIT: `$3,400.65`
- Total tax: `$23,129.34` (Schedule G $19,728.69 + NIIT $3,400.65)
  - Note: Schedule G may change slightly from the deductions cascade even at $0 fees — only NIIT change is guaranteed
- Schedule B `distributable_net_income`: `$903.94`
- Schedule B Line 6 (`capital_gains_subtraction`): `-$104,236.73`

### Wave 0 Gaps
- [ ] `tests/test_fixes.py` — unit tests for FIX-01, FIX-02, FIX-03 (covers all three fixes with known inputs)
- [ ] No test framework installed — project relies on `--dry-run` output inspection

*(If formal pytest tests are out of scope for this phase, the dry-run verification checks above serve as the acceptance criteria.)*

---

## State of the Art

| Old Behavior | Corrected Behavior | Impact |
|--------------|-------------------|--------|
| Form 8960 Line 19a = taxable_income ($105,040.67) | Line 19a = gross_income ($105,140.67) | NIIT increases $3.80 |
| Schedule B Line 6 = blank | Line 6 = -$104,236.73 | DNI corrected from $105,140.67 to $903.94 |
| No Line 14 deduction | Config-driven attorney/accountant fees → Line 14 | Taxable income reduced if fees > $0 |

---

## Open Questions

1. **Actual attorney/accountant fee amount**
   - What we know: The config key `deductions.attorney_accountant_fees` will be added; value is TBD
   - What's unclear: The dollar amount of 2025 professional fees has not been provided
   - Recommendation: Set to `0.00` initially; user updates config with actual amount before filing. All cascading computations work correctly with any non-negative value.

2. **Schedule G tax change with deductions**
   - What we know: If attorney_fees = $0, Schedule G tax is unchanged at $19,728.34. If fees > $0, taxable income decreases and tax decreases.
   - What's unclear: The exact CONTEXT.md values ($19,728.34 for Schedule G) assume $0 deductions. The CONTEXT.md notes "Net tax change: +$3.80" for FIX-01 only.
   - Recommendation: Document clearly that the corrected totals in CONTEXT.md assume zero deductions. If actual fees are entered, all values will shift further.

3. **Form 8960 Lines 9a-9c for professional fee deductions**
   - What we know: IRS allows deduction of professional fees allocable to NII on Form 8960 Line 9b
   - What's unclear: Whether the user wants Form 8960 to reflect the Line 14 deduction
   - Recommendation: Deferred per conservative approach above. Flag as open for future phase if NIIT reduction is desired.

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `fill_1041.py` lines 295–460, 516–604, 960–1059
- Direct field catalog inspection: `config/2025_fields.json` — `attorney_accountant_fees` = `f1_32[0]`, `gain_from_page1_line4` = `f2_13[0]`, `total_deductions` = `f1_35[0]`
- CONTEXT.md: locked decisions and corrected values verified

### Secondary (MEDIUM confidence)
- IRS Form 1041 Schedule B instructions: Line 6 treatment of capital gains (negative when gain, to compute DNI)
- IRS Form 8960 Part III instructions: Line 19a for trusts = Form 1041 Line 17 (adjusted total income, not Line 23 taxable income)
- Treasury Regulation §1.1411-10: NII deduction allocability for professional fees

### Tertiary (LOW confidence)
- None — all findings based on direct code and config inspection or well-established IRS instructions

---

## Metadata

**Confidence breakdown:**
- Fix 1 (Form 8960): HIGH — exact line of code identified, corrected values confirmed in CONTEXT.md
- Fix 2 (Schedule B): HIGH — field IDs confirmed, computation logic clear, IRS instruction basis documented
- Fix 3 (Deductions): HIGH for config/compute wiring; MEDIUM for NIIT allocability recommendation
- Cascade analysis: HIGH — computation chain fully traced

**Research date:** 2026-03-09
**Valid until:** 2027-04-15 (stable — IRS form fields and Python code do not change until next tax year)
