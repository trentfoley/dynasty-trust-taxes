# Dynasty Trust Tax Form Filler

## What This Is

An annual tax preparation tool for the **TRENT FOLEY CHILDRENS 2021 SUPER DYNASTY TR** (EIN-ending X123). Each tax year, the tool reads the brokerage's end-of-year CSV statement, computes all IRS Form 1041 fields (income, Schedule D capital gains, Schedule G tax), and produces a filled, print-ready PDF of the 1041.

The trust has a single brokerage account and accumulates all income (no distributions to beneficiaries, no Schedule K-1s). The trustee is Trent Foley.

## Core Value

Given a brokerage year-end CSV and a blank Form 1041 PDF, produce a complete, filled, print-ready Form 1041 that matches every field the prior year's return had populated — in one command.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Parse 1099-DIV, 1099-INT, and 1099-B data from the brokerage CSV
- [ ] Compute Schedule D (capital gains/losses: short-term and long-term)
- [ ] Compute Schedule G (tax on taxable income using trust tax brackets)
- [ ] Populate all Form 1041 page 1 fields consistent with the 2024 filed reference return
- [ ] Fill all fields into the blank IRS PDF (AcroForm) to produce a print-ready output PDF
- [ ] Tool is reusable year-over-year: accepts new CSV and new blank form each year

### Out of Scope

- Schedule K-1 / beneficiary distributions — trust accumulates all income
- State tax returns — federal Form 1041 only
- E-filing — output is for print and mail
- Other income types (rental, business) — single brokerage account only
- Foreign tax credit (no foreign tax paid in 2025 data)
- Alternative Minimum Tax (AMT) — not applicable to this trust profile

## Context

- **Tax year:** 2025 (calendar year)
- **Prior reference:** `filed_returns/2024 1041 Trent Foley Childrens 2021 Super Dynasty TR.pdf` — establishes which fields to populate
- **Blank form:** `forms/f1041.pdf` — the 2025 IRS Form 1041 with AcroForm fields
- **Brokerage data:** `2025/XXXX-X123.CSV` (primary), plus XML and PDF versions of the same statement
- **Prior Excel calculator:** `1041 Schedule G Calculator.xlsx` — reference for Schedule G computation logic
- **2025 income summary (from CSV):**
  - Ordinary dividends: $903.82 (all qualified)
  - Interest income: $0.12
  - Long-term capital gain: ~$104,109.76 (296 shares VGT, various dates, sold 12/24/2025)
  - Short-term capital gain: ~$126.97 (1.35 shares VGT, sold 12/24/2025)

## Constraints

- **Primary tool**: Claude skill — Claude handles all intelligence (CSV parsing, tax computation, field mapping)
- **PDF writing**: Thin Python script (`fill_pdf.py`) — the only maintained Python artifact; takes a field-value JSON and writes the filled PDF
- **PDF filling**: Must use AcroForm field names from the IRS PDF (not recreate the form)
- **Year-agnostic**: Field mappings and tax bracket logic are parameterized by tax year via `config/YEAR.json`
- **No external services**: Runs entirely locally — no API calls, no cloud

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Claude skill as primary implementation | Simpler than a maintained Python codebase; Claude does the heavy lifting | Decided |
| Use brokerage CSV as primary data source | Structured, machine-readable; XML/PDF are fallbacks | Decided |
| Fill existing IRS PDF via AcroForm | Preserves official form appearance; IRS PDFs support AcroForms | Decided |
| Python only for thin PDF filler | pypdf is the right tool for AcroForm writing; everything else Claude handles | Decided |

---
*Last updated: 2026-03-08 after initialization*
