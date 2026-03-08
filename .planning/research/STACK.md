# Stack Research

**Domain:** Python CLI tool — brokerage CSV/XML ingestion, trust tax computation, IRS AcroForm PDF filling
**Researched:** 2026-03-08
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.13.x | Runtime | Current stable release (3.13.7 as of Aug 2025); all target libraries support it; ships with `csv`, `xml.etree.ElementTree`, and `decimal` in stdlib. Windows installer from python.org is sufficient — no exotic tooling required. |
| pypdf | 6.7.5 | Read AcroForm field names; write filled PDF | Actively maintained successor to the deprecated PyPDF2. Pure Python, no native dependencies, works on Windows without anything extra. `PdfWriter.update_page_form_field_values()` covers the exact use-case: read blank IRS form, fill field dict, write output. Latest release: March 2, 2026. |
| `decimal` (stdlib) | built-in | All monetary arithmetic | IRS arithmetic rules require exact decimal rounding. Python's `decimal.Decimal` with `ROUND_HALF_UP` and string initialization eliminates float precision bugs. No install needed. |
| `csv` (stdlib) | built-in | Parse brokerage CSV | The brokerage CSV is a simple structured file — stdlib `csv.DictReader` is sufficient. No dependency overhead; handles quoted fields, varied delimiters. |
| `xml.etree.ElementTree` (stdlib) | built-in | Parse brokerage XML (fallback) | XML version of the brokerage statement is a backup. ElementTree handles straightforward financial XML without XPath complexity. No install needed. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| uv | latest (0.5.x+) | Virtualenv + dependency locking on Windows | Use `uv` instead of pip + venv. Single binary install via PowerShell, 10–100x faster installs, lockfile support. Ensures reproducible environment year-over-year when you revisit this tool. |
| pytest | 8.x | Unit testing of tax computation logic | Use to verify Schedule D capital gain aggregation, Schedule G bracket math, and field-value mapping — especially critical when tax brackets change year to year. |
| lxml | 5.x | XML parsing with XPath (optional upgrade) | Only add if the brokerage XML turns out to have a complex namespace structure that requires XPath 1.0 queries. Not needed for the current CSV-primary approach. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | Virtualenv, package install, lockfile | `uv init`, `uv add pypdf pytest`, `uv run python fill.py` — replaces pip + venv entirely on Windows |
| VS Code + Pylance | Editor + type checking | Works natively on Windows; Pylance provides inline type hints for the pypdf API which has complex overloads |
| `python -m pypdf` CLI (built-in) | Inspect AcroForm field names in the blank IRS PDF | `python -m pypdf show f1041.pdf --fields` lists every AcroForm field name — essential first step before writing any fill logic |

## Installation

```bash
# Install uv (run once in PowerShell as user — no admin required)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Initialize project and create virtualenv
uv init dynasty-trust-taxes
cd dynasty-trust-taxes
uv python pin 3.13

# Core dependency
uv add pypdf

# Dev dependencies
uv add --dev pytest

# Run the tool
uv run python src/fill_1041.py

# Lock for reproducibility (commit uv.lock to git)
# uv lock is run automatically on uv add
```

No compilation, no system libraries, no admin rights required. All packages are pure Python wheels on Windows.

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| pypdf 6.x | PyPDFForm 4.x | If you need higher-level dict-based API and don't want to manage multi-page field iteration manually. PyPDFForm 4.5.0 (Jan 2026) abstracts the page loop. Tradeoff: less control over `auto_regenerate` and flatten behavior on IRS PDFs. |
| pypdf 6.x | pikepdf | If IRS PDF has encrypted fields or needs low-level PDF object surgery. pikepdf wraps libqpdf (C library) so requires a native build — adds Windows complexity. Overkill for straightforward AcroForm filling. |
| stdlib `csv` | pandas / polars | If the brokerage CSV were large (10k+ rows) or required complex joins. For a single-account annual statement with ~300 transactions, stdlib `csv.DictReader` is simpler and has zero dependencies. |
| stdlib `decimal` | `mpmath` or `fractions` | `mpmath` is for arbitrary-precision floating point (scientific use); `fractions` is for exact rational arithmetic. Neither matches IRS rounding semantics. `decimal` with `ROUND_HALF_UP` is the standard for financial/tax work. |
| uv | pip + venv | If the team is already on pip workflows and doesn't need lockfiles. pip works fine; uv is just faster and safer for year-over-year reproducibility. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| PyPDF2 / PyPDF3 / PyPDF4 | Officially deprecated; development moved entirely to `pypdf`. Last PyPDF2 commit was 2023. Security issues unfixed. | `pypdf` 6.x |
| pdfrw | Removed from Debian in 2024 as unmaintained and RC-buggy. Broken on Python 3.7+. | `pypdf` 6.x |
| `fillpdf` | Thin wrapper over a fork of the dead `pdfrw`. Inherits its bugs and is not actively developed. | `pypdf` 6.x |
| `float` for any dollar amount | Binary floating point cannot represent 0.1 exactly. `0.1 + 0.2 == 0.30000000000000004`. For tax math this is not acceptable. | `decimal.Decimal('0.1')` |
| IronPDF / pdfFiller (Python bindings) | Commercial SDKs with license costs, network calls, or platform-specific native libs. Violates the "no external services, runs locally" constraint in PROJECT.md. | `pypdf` 6.x |
| pdftk (command-line tool) | Requires a separate Java/GCC-based install. Fine for one-off use but adds a non-Python dependency that breaks the "nothing exotic on Windows" goal. | `pypdf` 6.x (pure Python) |

## Stack Patterns by Variant

**If the blank IRS PDF uses XFA forms instead of AcroForms:**
- XFA (XML Forms Architecture) is a different format used in some older IRS PDFs. pypdf cannot fill XFA fields.
- Detect with: `PdfReader("f1041.pdf").trailer["/Root"]["/AcroForm"]` — if it contains `/XFA`, you have an XFA form.
- Mitigation: IRS has been migrating away from XFA; the 2025 Form 1041 is expected to be AcroForm. Verify on first run with `python -m pypdf show f1041.pdf --fields`.
- If XFA: use `pdfjinja` or manually extract XFA XML and rewrite it — significantly more complex.

**If a future year's brokerage export switches to OFX/QFX format:**
- Use the `ofxparse` library (pure Python) instead of stdlib `csv`.
- API: `ofxparse.OfxParser.parse(open('statement.ofx'))` returns typed transaction objects.

**If tax computation logic grows to cover multiple trusts:**
- Promote the tax-bracket config (currently inline dicts) to YAML files loaded with `tomllib` (stdlib in Python 3.11+) or `PyYAML`.
- Keep computation logic pure functions with no I/O for easy unit testing.

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| pypdf 6.7.5 | Python 3.9–3.14 | Fully compatible with Python 3.13.x. No known issues on Windows. |
| pytest 8.x | Python 3.8+ | Compatible with Python 3.13.x. |
| lxml 5.x | Python 3.6+ | Requires C compiler or pre-built wheel. Pre-built wheels for Windows available on PyPI — `uv add lxml` will pull the wheel automatically. |
| uv 0.5+ | Python 3.8–3.14 | Windows native binary; no Python required for installation. |

## Key Implementation Notes

### Discovering AcroForm Field Names (Do This First)

Before writing any fill logic, enumerate the exact field names in the blank IRS PDF:

```python
from pypdf import PdfReader

reader = PdfReader("forms/f1041.pdf")
fields = reader.get_fields()
for name, field in fields.items():
    print(name, field.get("/FT"), field.get("/V"))
```

IRS field names are not human-readable (e.g., `topmostSubform[0].Page1[0].f1_01[0]`) — you must map them empirically from the blank form, not guess from form labels.

### Filling AcroForm Fields (Core Pattern)

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("forms/f1041.pdf")
writer = PdfWriter()
writer.append(reader)

# Fill each page separately; IRS Form 1041 spans multiple pages
for page in writer.pages:
    writer.update_page_form_field_values(
        page,
        field_values,        # dict of {acroform_field_name: str_value}
        auto_regenerate=False,  # prevents "save changes" dialog in Acrobat
    )

with open("output/1041_filled.pdf", "wb") as f:
    writer.write(f)
```

### Decimal Arithmetic Pattern

```python
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")

# Always initialize from strings, never from floats
ordinary_dividends = Decimal("903.82")
interest = Decimal("0.12")
lt_gain = Decimal("104109.76")

total_income = (ordinary_dividends + interest + lt_gain).quantize(CENT, rounding=ROUND_HALF_UP)
```

## Sources

- pypdf 6.7.5 documentation (forms page) — https://pypdf.readthedocs.io/en/stable/user/forms.html — HIGH confidence
- pypdf 6.7.5 PyPI release page — https://pypi.org/project/pypdf/ — HIGH confidence (verified March 2, 2026 release)
- PyPDFForm 4.5.0 PyPI — https://pypi.org/project/PyPDFForm/ — HIGH confidence (verified Jan 1, 2026 release)
- pdfrw removal from Debian — https://bugs.debian.org/958362 — HIGH confidence (official Debian bug tracker)
- Python decimal module stdlib docs — https://docs.python.org/3/library/decimal.html — HIGH confidence
- uv documentation — https://docs.astral.sh/uv/ — HIGH confidence
- WebSearch: "Python PDF ecosystem 2024 2025" — MEDIUM confidence (corroborated by official docs)
- WebSearch: "pdfrw abandoned 2024" — HIGH confidence (corroborated by Debian bug tracker)

---
*Stack research for: Dynasty Trust Tax Form Filler (IRS Form 1041)*
*Researched: 2026-03-08*
