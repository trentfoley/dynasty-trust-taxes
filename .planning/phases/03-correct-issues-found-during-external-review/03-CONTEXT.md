# Phase 3: Correct issues found during external review - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix three specific errors identified by external review of the v1.0 output forms, and add deduction support to the computation chain. The fixes are to `fill_1041.py` computation logic and `config/2025.json`. No new forms, no new infrastructure, no architectural changes.

</domain>

<decisions>
## Implementation Decisions

### Form 8960 AGI fix (Line 19a)
- Line 19a must use **gross income = $105,140.67** (Form 1041 line 17), NOT taxable income ($105,040.67)
- The $100 complex trust exemption must NOT be subtracted before feeding 8960
- Cascading corrected values: Line 19c = $89,490.67, Line 20 = $89,490.67, Line 21 NIIT = $3,400.65
- Net tax change: +$3.80 underpayment (trust was underpaying, not overpaying)

### Schedule B Line 6 fix (capital gains)
- Line 6 must be filled with **-$104,236.73** (negative of net total capital gain: $104,109.76 LT + $126.97 ST)
- This is the gain from Form 1041 line 4, entered as a negative per IRS instructions
- Corrected Line 7 (DNI) = $903.94 ($105,140.67 − $104,236.73)
- Tax impact: none (no distributions made, Lines 9–11 = $0) — but DNI must be correct for audit-readiness

### Deductions support
- Add `deductions.attorney_accountant_fees` to `config/2025.json`
- Wire into `compute_form_1041_page1()` to fill **Line 14** on Form 1041
- Line 14 amount flows into total deductions → reduces taxable income → cascades through Schedule G, NIIT, and all downstream computations
- Only Line 14 (attorney/accountant fees) supported — no other deduction lines needed

### Claude's Discretion
- Exact field ID for Form 1041 Line 14 (look up from `config/2025_fields.json`)
- Whether deductions reduce NIIT base (they should — professional fees are allocable against NII)
- How to handle zero deduction case (skip field or write $0)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `compute_form_8960()` in `fill_1041.py`: target function for the AGI fix — change input from `taxable_income` to `gross_income`
- `compute_schedule_b()` in `fill_1041.py`: target function for Line 6 fix — add `line6_capital_gains` computation using `st_gain + lt_gain` totals
- `config/2025.json`: target file for new `deductions` section
- `config/2025_fields.json`: field catalog — contains Form 1041 AcroForm field IDs for Line 14

### Established Patterns
- All dollar values computed in Python floats, rounded to 2 decimal places at output
- Config values read via `cfg = json.load(...)` at top of `fill_1041.py` — deductions can follow same pattern
- Field maps built in `build_field_maps()` — Line 14 field ID addition goes there
- `compute_form_1041_page1()` already handles income lines and exemption — deduction wire-in follows same pattern

### Integration Points
- Form 8960 fix: `compute_form_8960(cfg, form_data)` — `form_data["gross_income"]` is already computed as `ordinary_dividends + interest + st_gain + lt_gain`; just need to pass it correctly to line 19a instead of `taxable_income`
- Schedule B fix: `compute_schedule_b()` — `net_capital_gain = st_gain + lt_gain` is already computed upstream; line 6 = `-net_capital_gain`
- Deductions cascade: Line 14 → total deductions → taxable income → Schedule G → Form 8960 → all downstream amounts

</code_context>

<specifics>
## Specific Ideas

- Reviewer confirmed: Form 8960 instructions explicitly state line 19a for estates/trusts = Form 1041 line 17 (not line 23)
- Schedule B Line 6: IRS instructions say "enter the gain from Schedule D (Form 1041), line 19" as a negative — this is the net long-term + short-term total
- Deductions: only Line 14 for now (attorney/accountant fees paid in 2025). Amount TBD — will be set in `config/2025.json`

</specifics>

<deferred>
## Deferred Ideas

- **Form 2210 underpayment penalty** — Trust made no estimated payments and owes $23,125.19. Penalty may apply, but Form 2210 calculation requires prior-year tax data and is complex. Out of scope for this phase — consult tax advisor.
- **Tax distribution strategy** — Distributing ordinary income to beneficiaries in lower brackets could reduce tax burden. Separate decision from return preparation; involves trust instrument review.
- **Fiduciary fees (Line 11) and other deductions (Line 15)** — Not needed for 2025. Can be added in a future year if applicable.

</deferred>

---

*Phase: 03-correct-issues-found-during-external-review*
*Context gathered: 2026-03-09*
