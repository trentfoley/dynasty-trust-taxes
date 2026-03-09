# dynasty-trust-taxes

Form 1041 tax preparation for **Trent Foley Childrens 2021 Super Dynasty Trust** (EIN 87-6893299).

## What it does

Reads the year-end brokerage CSV, runs all tax computations, and writes five filled PDFs to `output/`:

| File | Form |
|------|------|
| `YYYY 1041 <entity>.pdf` | Form 1041 (main return) |
| `YYYY Schedule D <entity>.pdf` | Schedule D — capital gains |
| `YYYY 8960 <entity>.pdf` | Form 8960 — Net Investment Income Tax |
| `YYYY 8949 <entity>.pdf` | Form 8949 — transaction detail |
| `YYYY 1041-V <entity>.pdf` | Form 1041-V — payment voucher |

## Prerequisites

- Python: `/c/ProgramData/miniconda3/python` (Windows — do not use `python3`)
- `pypdf` installed in that environment
- Brokerage year-end CSV placed at the path in `config/2025.json` → `paths.csv_input`

## Usage

### Via Claude Code skill

```
/fill-1041
```

Runs with all defaults from `config/2025.json`.

### Direct

```bash
cd /c/Users/TrentFoley/Source/dynasty-trust-taxes
/c/ProgramData/miniconda3/python fill_1041.py
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--dry-run` | Print all computed values without writing any files |
| `--year YYYY` | Use `config/YYYY.json` (default: `2025`) |
| `--csv PATH` | Override CSV input path |
| `--output-dir PATH` | Override output directory |

## Config files

- `config/2025.json` — trust info, tax brackets, thresholds, and file paths
- `config/2025_fields.json` — AcroForm field ID catalog used by `fill_pdf.py`

## Mailing the return (Texas)

Mail the signed return, check, and detached 1041-V voucher (loose — do not staple) to:

**With payment:**
> Department of the Treasury
> Internal Revenue Service
> Ogden, UT 84201-**0148**

Make the check payable to **United States Treasury** with `87-6893299 2025 Form 1041` on the memo line.
