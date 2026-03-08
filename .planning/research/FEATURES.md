# Feature Research

**Domain:** IRS Form 1041 — Automated tax preparation for an accumulation trust with brokerage investment income only
**Researched:** 2026-03-08
**Confidence:** HIGH (primary sources: IRS official instructions and forms, 2025 tax year)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Every item below is required to produce a legally complete Form 1041 for this trust profile. Missing any one of them means the return cannot be filed.

#### Header / Identity Fields

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Trust name in header | Required identifying field | LOW | "TRENT FOLEY CHILDRENS 2021 SUPER DYNASTY TR" — static |
| Fiduciary name and title | Required field | LOW | "Trent Foley, Trustee" — static |
| EIN | Required field | LOW | Ends X123 — static |
| Date entity created | Required field | LOW | Static from trust document |
| Mailing address | Required field | LOW | Static |
| Tax year (calendar year 2025) | Required field | LOW | Derived from CSV tax year |
| Type of entity checkbox | Item A — exactly one must be checked | LOW | "Complex trust" — accumulation trust that does not currently distribute all income |
| Item B: Number of Schedules K-1 | Required count field | LOW | 0 — no distributions |
| Item D: Employer identification number | Required | LOW | Same as EIN above |
| Item F checkboxes | Initial/Final/Amended/Name change flags | LOW | All unchecked for a routine annual filing |

#### Form 1041 Page 1 — Income Section

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Line 1 — Interest income | $0.12 from 1099-INT Box 1 | LOW | Parse 1099-INT Box 1 from CSV |
| Line 2a — Total ordinary dividends | $903.82 from 1099-DIV Box 1a | LOW | Parse 1099-DIV Box 1a from CSV |
| Line 2b — Qualified dividends | $903.82 from 1099-DIV Box 1b | LOW | Parse 1099-DIV Box 1b; drives Qualified Dividends Tax Worksheet |
| Line 4 — Capital gain or (loss) | Net from Schedule D Line 19 | MEDIUM | Pulled from Schedule D after computation |
| Line 9 — Total income | Sum of Lines 1 + 2a + 3–8 | LOW | Arithmetic; Lines 3, 5, 6, 7, 8 all zero for this trust |

#### Form 1041 Page 1 — Deduction Section

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Line 12 — Fiduciary fees | Deductible trustee fee if any paid | LOW | Zero if no fee taken; must be populated (zero or amount) |
| Line 14 — Attorney/accountant/return preparer fees | Deductible professional fees | LOW | May be zero; confirm from prior return |
| Line 15a — Other deductions not subject to 2% floor | Catch-all for allowable deductions | LOW | Likely zero; confirm from prior return |
| Line 16 — Total deductions (sum of Lines 10–15b) | Arithmetic subtotal | LOW | Sum of deduction lines |
| Line 17 — Adjusted total income (Line 9 minus Line 16) | Intermediate computation | LOW | Arithmetic |
| Line 18 — Income distribution deduction (from Schedule B) | Must be zero for an accumulation trust | LOW | Schedule B will show $0 since no distributions are made |
| Line 21 — Exemption | Complex trust exemption is $100 | LOW | Hard-coded $100 for complex trust |
| Line 22 — Total deductions (sum Lines 18–21) | Arithmetic subtotal | LOW | Lines 18 + 19 + 20 + 21 |
| Line 23 — Taxable income (Line 17 minus Line 22) | Base for Schedule G tax computation | LOW | Arithmetic; drives all tax calculations |

#### Schedule B — Income Distribution Deduction

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Schedule B, all lines | Required schedule even when zero | LOW | Because this is a complex trust, Schedule B must be present. Every line will be $0 or derived from DNI, and the deduction on Line 15 will be $0 (no distributions made). The $0 flows to Form 1041 Line 18. |

#### Schedule D — Capital Gains and Losses (Form 1041)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Form 8949 — Short-term, Part I, Box A (covered, basis reported) | 1.35 shares VGT, code A | MEDIUM | Proceeds $1,030.79, cost $903.82, gain $126.97. Must complete Form 8949 before Schedule D Lines 1b/2/3. |
| Form 8949 — Long-term, Part II, Box D (covered, basis reported) | 296 shares VGT, code D | MEDIUM | Proceeds $226,514.41, cost $122,404.65, gain $104,109.76. Must complete Form 8949 before Schedule D Lines 8b/9/10. |
| Schedule D Part I — Short-term totals | Net short-term gain/loss | MEDIUM | Line 1b carries from Form 8949 Part I Box A totals; Line 7 = net short-term |
| Schedule D Part II — Long-term totals | Net long-term gain/loss | MEDIUM | Line 8b carries from Form 8949 Part II Box D totals; Line 15 = net long-term from carryovers (if any); Line 16 = net long-term |
| Schedule D Line 17 — Allocate gains between beneficiaries and trust | Distribution allocation | LOW | Zero allocated to beneficiaries (no distributions); all retained by trust |
| Schedule D Line 18a — Net long-term capital gain | Amount retained by trust | LOW | = Line 16 (all retained) |
| Schedule D Line 19 — Total net capital gain (col 3) | Flows to Form 1041 Line 4 | LOW | Sum of net short + net long allocated to trust |

#### Schedule G — Tax Computation and Payments

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Qualified Dividends Tax Worksheet (in-worksheet, referenced by Schedule G Line 1a) | Required when trust has qualified dividends or capital gains | HIGH | Computes tax using preferential rates on qualified dividends and long-term capital gains. 2025 trust brackets: 0% on first $3,250; 15% on $3,250–$15,900; 20% above $15,900. |
| Schedule G Line 1a — Tax on taxable income | Result of Qualified Dividends Tax Worksheet | HIGH | Takes result from worksheet (smaller of Line 21 or Line 22 of the worksheet) |
| Schedule G Line 1b — Tax on net long-term capital gain (if applicable) | May be folded into worksheet | MEDIUM | Verify against prior return; may be reported separately or within worksheet |
| Schedule G Line 2a — NIIT via Form 8960 | 3.8% on net investment income above $15,650 AGI threshold | HIGH | Trust AGI will substantially exceed $15,650 threshold (total income ~$105,140). Form 8960 must be completed and attached. NIIT = 3.8% × lesser of (undistributed NII, excess AGI over $15,650) |
| Schedule G Line 9 — Total tax | Sum of Schedule G lines | LOW | Arithmetic; flows to Form 1041 Line 24 |

#### Form 8960 — Net Investment Income Tax

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Form 8960 computation | NIIT applies: AGI >> $15,650 threshold | HIGH | All income (interest, dividends, capital gains) is net investment income. Must compute NII, compare to excess AGI over $15,650, take lesser, multiply by 3.8%. Result feeds Schedule G Line 2a. |

#### Tax Computation Logic

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| 2025 ordinary income trust tax brackets | Required to compute Schedule G correctly | MEDIUM | 10% on $0–$3,150; 24% on $3,150–$11,450; 35% on $11,450–$15,650; 37% above $15,650 |
| 2025 qualified dividends / long-term capital gains trust brackets | Required for Qualified Dividends Tax Worksheet | MEDIUM | 0% on $0–$3,250; 15% on $3,250–$15,900; 20% above $15,900 |
| Parameterized brackets by tax year | Required for year-over-year reuse | MEDIUM | Brackets change annually via IRS inflation adjustments; store as config per tax year |

#### Output

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Filled Form 1041 PDF (AcroForm) | Core deliverable | HIGH | Use IRS AcroForm field names from f1041.pdf to fill all computed values |
| Filled Schedule D PDF | Required attachment | HIGH | f1041sd.pdf AcroForm fields |
| Filled Form 8949 PDF | Required attachment before Schedule D | MEDIUM | f8949.pdf AcroForm fields; two transactions |
| Filled Form 8960 PDF | Required attachment (NIIT) | MEDIUM | f8960.pdf AcroForm fields |
| Print-ready output (single run command) | Core value proposition | LOW | Concatenate or produce all pages into one printable output |

---

### Differentiators (Competitive Advantage)

This is a single-user internal tool, not a commercial product. "Differentiators" here mean what makes this tool better than doing the math by hand or re-using the Excel spreadsheet.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| One-command operation | "Drop CSV, run script, get PDF" — zero manual steps | MEDIUM | Primary motivation for building vs. manual entry |
| Idempotent computation | Running twice produces identical output; no hidden state | LOW | All inputs explicit (CSV + blank form) |
| Year-over-year reusability | New tax year = new CSV + new blank form; no code changes | MEDIUM | Tax brackets and AcroForm field names parameterized by year |
| Traceable intermediate values | Print computed values (income, gains, taxes) to stdout before PDF fill | LOW | Enables spot-check before accepting output |
| Prior-return field parity check | Warn if any field populated in the 2024 reference return is absent from 2025 output | MEDIUM | Guards against regressions when form layout changes year to year |

---

### Anti-Features (Do Not Build)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Schedule K-1 generation | Trust has beneficiaries | This trust accumulates all income; no distributions are made; K-1s would be incorrect | Leave out entirely; Schedule B shows $0 distribution |
| State tax returns | Tax software often includes them | Out of scope by design; state returns have different forms/rules | Federal Form 1041 only |
| E-filing / IRS Direct File | Seems modern | Trusts require third-party e-file provider setup; print-and-mail is the stated delivery method | Output for print and mail |
| AMT computation (Schedule I) | Could apply to some trusts | Not applicable to this trust profile; Schedule I is for alternative minimum tax on complex trusts with preference items; this trust has none | Skip Schedule I |
| Schedule J (Accumulation Distribution Throwback) | This is an accumulation trust | Schedule J applies only to complex trusts created before March 1, 1984 or formerly foreign trusts; this trust was created in 2021 | Skip Schedule J |
| Charitable deduction (Schedule A) | Trust might donate | This trust makes no charitable contributions | Skip Schedule A; Line 13 = $0 |
| Foreign tax credit | 1099-DIV Box 7 | 2025 brokerage data shows no foreign tax paid | Skip; Box 7 is blank in CSV |
| Section 199A / QBI deduction | Pass-through income | This trust has no pass-through business income; 1099-DIV Box 5 is blank | Skip Line 20; $0 |
| Interactive UI or web app | Seems useful | Adds frontend complexity; the user is the only user and runs it from the command line | CLI script only |
| PDF form recreation | If IRS form changes layout | Recreating the form is error-prone and legally risky | Fill existing IRS AcroForm; absorb layout changes by updating field-name mappings |
| Section 1250 / 1202 / collectibles gains | Edge case capital gain types | 2025 CSV shows all blanks for boxes 2b, 2c, 2d; VGT ETF sales generate only standard long-term gain | Validate that these are zero; raise error if non-zero (don't silently ignore) |

---

## Feature Dependencies

```
CSV Parsing (1099-DIV, 1099-INT, 1099-B)
    └──required by──> Intermediate Value Computation
                          └──required by──> Form 8949 fill
                                               └──required by──> Schedule D fill
                                                                      └──required by──> Form 1041 Line 4
                          └──required by──> Qualified Dividends Tax Worksheet
                                               └──required by──> Schedule G Line 1a
                          └──required by──> Form 8960 (NIIT)
                                               └──required by──> Schedule G Line 2a
                                                                      └──required by──> Schedule G Line 9
                                                                                             └──required by──> Form 1041 Line 24

Tax Bracket Config (parameterized by year)
    └──required by──> Qualified Dividends Tax Worksheet
    └──required by──> Ordinary Income Tax Computation
    └──required by──> NIIT threshold check

AcroForm Field Mapping (parameterized by year)
    └──required by──> PDF Fill (all forms)

Schedule B (zero distributions)
    └──required by──> Form 1041 Line 18 ($0 income distribution deduction)
```

### Dependency Notes

- **Form 8949 must be completed before Schedule D:** IRS instructions explicitly require Form 8949 completion before populating Schedule D Lines 1b, 2, 3, 8b, 9, 10.
- **Schedule D must be completed before Form 1041 Line 4:** Line 4 pulls the net capital gain figure from Schedule D Line 19.
- **Schedule G depends on Form 8960:** NIIT from Form 8960 feeds Schedule G Line 2a before Schedule G Line 9 (total tax) can be computed.
- **Tax brackets parameterized by year:** The 2025 ordinary income brackets ($3,150 / $11,450 / $15,650 thresholds) and capital gains brackets ($3,250 / $15,900 thresholds) differ from 2024; hard-coding them breaks year-over-year reuse.

---

## MVP Definition

### Launch With (v1)

The MVP is the complete return for tax year 2025 — there is no "partial" filing.

- [ ] Parse 1099-DIV (Box 1a, 1b) from brokerage CSV — ordinary and qualified dividends
- [ ] Parse 1099-INT (Box 1) from brokerage CSV — interest income
- [ ] Parse 1099-B (columns: description, date acquired, date sold, proceeds, cost, short/long flag, covered/noncovered flag) from brokerage CSV
- [ ] Compute Form 8949: one short-term row (code A, covered), one long-term row (code D, covered)
- [ ] Compute Schedule D: net short-term gain (Line 7), net long-term gain (Line 16), allocation to trust (Lines 17–19)
- [ ] Compute Schedule B: all lines = $0 (no distributions)
- [ ] Compute Form 1041 Lines 1, 2a, 2b, 4, 9 (income section)
- [ ] Compute Form 1041 Lines 16, 17, 18, 21, 22, 23 (deduction and taxable income)
- [ ] Compute Qualified Dividends Tax Worksheet (applies 2025 preferential rates to QD and LTCG)
- [ ] Compute Form 8960 (NIIT): verify AGI > $15,650 threshold; compute 3.8% on net investment income
- [ ] Compute Schedule G Lines 1a, 2a, 9 (total tax computation)
- [ ] Compute Form 1041 Lines 24–27 (tax due)
- [ ] Fill all computed values into IRS AcroForm PDFs: Form 1041, Schedule D, Form 8949, Form 8960
- [ ] Produce print-ready output PDF with all pages combined

### Add After Validation (v1.x)

- [ ] Prior-return field parity check — compare 2024 filed return fields against 2025 output; warn on mismatches
- [ ] Stdout summary of all intermediate computed values before PDF fill — enables manual spot-check
- [ ] Validate that unsupported income types (Section 1250, 1202, collectibles, foreign tax) are zero; raise error if not

### Future Consideration (v2+)

- [ ] Support for multiple brokerage accounts — not needed now; single account only
- [ ] Automated bracket/threshold updates from IRS published data — not needed now; annual manual config update is acceptable

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| CSV parsing (1099-DIV/INT/B) | HIGH | LOW | P1 |
| Form 8949 computation and fill | HIGH | MEDIUM | P1 |
| Schedule D computation and fill | HIGH | MEDIUM | P1 |
| Schedule B (zero distributions) | HIGH | LOW | P1 |
| Form 1041 page 1 income lines | HIGH | LOW | P1 |
| Form 1041 page 1 deduction lines | HIGH | LOW | P1 |
| Qualified Dividends Tax Worksheet | HIGH | HIGH | P1 |
| Form 8960 (NIIT) computation and fill | HIGH | MEDIUM | P1 |
| Schedule G computation and fill | HIGH | MEDIUM | P1 |
| Parameterized tax brackets by year | HIGH | LOW | P1 |
| Parameterized AcroForm field names by year | HIGH | MEDIUM | P1 |
| Print-ready combined PDF output | HIGH | MEDIUM | P1 |
| Stdout intermediate value trace | MEDIUM | LOW | P2 |
| Prior-return field parity check | MEDIUM | MEDIUM | P2 |
| Zero-validation for unsupported income types | MEDIUM | LOW | P2 |

**Priority key:**
- P1: Must have for launch (return cannot be filed without it)
- P2: Should have, add when P1 is complete
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

This is an internal tool, not a commercial product. The relevant comparison is against the prior manual workflow.

| Feature | Manual Workflow (Prior) | This Tool |
|---------|------------------------|-----------|
| Data entry | Hand-enter values from 1099 PDFs into Excel, then into form | Parse CSV automatically |
| Schedule D computation | Excel spreadsheet ("1041 Schedule G Calculator.xlsx") | Code computes; removes spreadsheet dependency |
| Tax bracket application | Excel formulas (maintained annually) | Code with year-parameterized config |
| NIIT (Form 8960) | Manual computation | Code computes and fills form |
| PDF filling | Manual entry in Acrobat or print-and-type | AcroForm fill via Python (pypdf or pdfrw) |
| Repeatability | Prone to transcription error | Deterministic; same CSV = same output |

---

## Appendix: 2025 Tax Computation Reference

### Ordinary Income Tax Brackets (Trust, 2025)

| Taxable Income | Rate |
|----------------|------|
| $0 – $3,150 | 10% |
| $3,150 – $11,450 | 24% |
| $11,450 – $15,650 | 35% |
| Over $15,650 | 37% |

### Qualified Dividends and Long-Term Capital Gains Brackets (Trust, 2025)

| Net Capital Gain / QD Amount | Rate |
|-------------------------------|------|
| $0 – $3,250 | 0% |
| $3,250 – $15,900 | 15% |
| Over $15,900 | 20% |

### Net Investment Income Tax (NIIT, 2025)

- Rate: 3.8%
- Trust threshold: AGI over $15,650
- Applies to: lesser of (undistributed net investment income, excess AGI over $15,650)
- Reported on: Form 8960; flows to Schedule G Line 2a

### 2025 Income Summary (From Brokerage CSV)

| Item | Source | Amount |
|------|--------|--------|
| Interest income | 1099-INT Box 1 | $0.12 |
| Ordinary dividends | 1099-DIV Box 1a | $903.82 |
| Qualified dividends | 1099-DIV Box 1b | $903.82 (100% qualified) |
| Long-term capital gain (296 sh VGT, code D) | 1099-B | $226,514.41 proceeds − $122,404.65 basis = $104,109.76 |
| Short-term capital gain (1.35 sh VGT, code A) | 1099-B | $1,030.79 proceeds − $903.82 basis = $126.97 |
| **Total income (approximate)** | | **~$105,140** |

At this income level, the trust is firmly in the 37% ordinary income bracket and the 20% long-term capital gains bracket. NIIT applies to substantially all income. The Qualified Dividends Tax Worksheet is the governing computation for Schedule G Line 1a.

---

## Sources

- [Instructions for Form 1041 and Schedules A, B, G, J, and K-1 (2025) — IRS](https://www.irs.gov/instructions/i1041)
- [Instructions for Schedule D (Form 1041) (2025) — IRS](https://www.irs.gov/instructions/i1041sd)
- [Instructions for Form 8949 (2025) — IRS](https://www.irs.gov/instructions/i8949)
- [Instructions for Form 8960 (2025) — IRS](https://www.irs.gov/instructions/i8960)
- [2025 Trust Tax Rates and Deductions — Ardent Trust](https://www.ardentrust.com/insights/trust-tax-rates-deductions)
- [Schedule D (Form 1041) 2025 — IRS PDF](https://www.irs.gov/pub/irs-pdf/f1041sd.pdf)
- [Form 8949 2025 — IRS PDF](https://www.irs.gov/pub/irs-pdf/f8949.pdf)

---
*Feature research for: IRS Form 1041 automated filler — TRENT FOLEY CHILDRENS 2021 SUPER DYNASTY TR*
*Researched: 2026-03-08*
