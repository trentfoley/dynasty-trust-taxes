# Dynasty Trust Tax Form Filler

## What This Is

An annual tax preparation tool for the **TRENT FOLEY CHILDRENS 2021 SUPER DYNASTY TR** (EIN-ending X123). Each tax year, the tool reads the brokerage's end-of-year CSV statement, computes all IRS Form 1041 fields (income, Schedule D capital gains, Schedule G tax, Form 8960 NIIT, Schedule B), and produces filled, print-ready PDFs for all four required forms (Form 1041, Schedule D, Form 8960, Form 8949).

The trust has a single brokerage account and accumulates all income (no distributions to beneficiaries, no Schedule K-1s). The trustee is Trent Foley.

## Core Value

Given a brokerage year-end CSV and blank IRS form PDFs, produce complete, filled, print-ready tax forms that match every field the prior year's return had populated — in one `/fill-1041` command.

## Requirements

### Validated

- ✓ Parse 1099-DIV, 1099-INT, and 1099-B data from the brokerage CSV — v1.0
- ✓ Compute Schedule D (capital gains/losses: short-term and long-term) — v1.0
- ✓ Compute Schedule G tax using the QD&CG worksheet (trust bracket rates) — v1.0
- ✓ Compute Form 8960 NIIT (3.8% of lesser of NII, AGI minus threshold) — v1.0
- ✓ Compute Schedule B (zero-distribution deduction for complex trust) — v1.0
- ✓ Populate all Form 1041 page 1 fields consistent with 2024 filed reference return — v1.0
- ✓ Fill all fields into blank IRS PDFs (AcroForm) to produce print-ready output PDFs — v1.0
- ✓ Dry-run mode prints all computed field values without writing any file — v1.0
- ✓ Validation re-sums CSV data vs computed values, halts on ≥$1.00 mismatch — v1.0
- ✓ Tool is reusable year-over-year: accepts new CSV and new blank forms each year — v1.0
- ✓ Invocable via `/fill-1041` Claude skill command — v1.0
- ✓ All tax bracket values in `config/YEAR.json` — no hardcoding in scripts — v1.0

### Active

(None — v1.0 complete. Define next milestone requirements via `/gsd:new-milestone`.)

### Out of Scope

- Schedule K-1 / beneficiary distributions — trust accumulates all income
- State tax returns — federal Form 1041 only
- E-filing — output is for print and mail
- Other income types (rental, business) — single brokerage account only
- Foreign tax credit (no foreign tax paid in 2025 data)
- Alternative Minimum Tax (AMT) — not applicable to this trust profile

## Context

- **Tax year:** 2025 (calendar year), filed 2026
- **Current state:** v1.0 shipped — all 4 forms fill correctly, `/fill-1041` command works
- **Prior reference:** `filed_returns/2024 1041 Trent Foley Childrens 2021 Super Dynasty TR.pdf`
- **Blank forms:** `forms/f1041.pdf`, `forms/f1041sd.pdf`, `forms/f8960.pdf`, `forms/f8949.pdf`
- **Brokerage data:** `2025/XXXX-X123.CSV`
- **2025 verified tax numbers:**
  - Ordinary dividends: $903.82 (all qualified) | Interest: $0.12
  - LT capital gain: $104,109.76 | ST capital gain: $126.97
  - Taxable income: $105,040.67 | Schedule G tax: $19,728.34
  - NIIT: $3,396.85 | Total tax: $23,125.19

## Constraints

- **Primary tool**: Claude skill — Claude handles all intelligence (CSV parsing, tax computation, field mapping)
- **PDF writing**: Thin Python script (`fill_pdf.py`) — the only maintained Python artifact
- **PDF filling**: Must use AcroForm field names from the IRS PDF (not recreate the form)
- **Year-agnostic**: Field mappings and tax bracket logic parameterized by tax year via `config/YEAR.json`
- **No external services**: Runs entirely locally — no API calls, no cloud

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Claude skill as primary implementation | Simpler than maintained Python codebase; Claude does the heavy lifting | ✓ Worked well — entire engine in one invocation |
| Use brokerage CSV as primary data source | Structured, machine-readable; XML/PDF are fallbacks | ✓ State-machine parser handles multi-section CSV cleanly |
| Fill existing IRS PDF via AcroForm | Preserves official form appearance; IRS PDFs support AcroForms | ✓ All 4 forms filled successfully |
| Python only for thin PDF filler | pypdf is the right tool for AcroForm writing; Claude handles everything else | ✓ `fill_pdf.py` is ~80 lines, zero logic |
| Separate PDF per form (not embed into 1041) | Schedule D, 8960, 8949 are standalone attachments | ✓ Correct — each form is a separate AcroForm file |
| `sys.executable` for subprocess in `fill_form()` | Windows subprocess cannot resolve Unix-style bash paths | ✓ Required on Windows — prevents interpreter mismatch |
| QD&CG worksheet for Schedule G | Trust has qualified dividends + LT gains — worksheet is required, not optional | ✓ Tax correct at $19,728.34 vs simple rate would differ |
| Runtime /_States_ checkbox translation in fill_pdf.py | IRS PDFs use non-standard On-state values (e.g., `1` not `Yes`) | ✓ Makes filler resilient across different IRS form versions |

---
*Last updated: 2026-03-09 after v1.0 milestone*
