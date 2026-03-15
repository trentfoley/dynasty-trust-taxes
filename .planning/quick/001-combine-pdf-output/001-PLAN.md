---
phase: quick
plan: 001
type: execute
wave: 1
depends_on: []
files_modified:
  - fill_1041.py
autonomous: true
requirements: [QUICK-001]
must_haves:
  truths:
    - "Running fill_1041.py produces a single combined PDF in addition to the individual form PDFs"
    - "The combined PDF contains all forms in the correct order (1041, Schedule D, 8949, 8960, 1041-V)"
    - "Individual form PDFs are still generated for reference"
  artifacts:
    - path: "fill_1041.py"
      provides: "combine_pdfs function and integration into main()"
      contains: "combine_pdfs"
  key_links:
    - from: "fill_1041.py:main"
      to: "fill_1041.py:combine_pdfs"
      via: "called after all individual PDFs are written"
      pattern: "combine_pdfs"
---

<objective>
After all individual form PDFs are filled, combine them into a single output PDF per trust.

Purpose: Simplify printing and filing by producing one combined PDF instead of requiring the user to open and print 2-5 separate files.
Output: A new `combine_pdfs()` function in fill_1041.py that merges all generated PDFs into a single file.
</objective>

<execution_context>
@C:/Users/TrentFoley/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/TrentFoley/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@fill_1041.py
@fill_pdf.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add combine_pdfs function and integrate into main()</name>
  <files>fill_1041.py</files>
  <action>
Add a `combine_pdfs()` function near the existing `fill_form()` helper (around line 1076) that:

1. Takes a list of PDF file paths (in desired page order) and an output path.
2. Uses `pypdf.PdfWriter` with `.append()` to merge all PDFs into one.
3. Writes the combined PDF to the output path.

```python
def combine_pdfs(pdf_paths, output_path):
    """Merge multiple filled PDFs into a single combined PDF.

    Args:
        pdf_paths: list of Path objects to filled PDFs, in desired order
        output_path: Path for the combined output PDF
    """
    from pypdf import PdfWriter
    writer = PdfWriter()
    for path in pdf_paths:
        writer.append(str(path))
    with open(output_path, "wb") as fh:
        writer.write(fh)
    print(f"Combined PDF written to: {output_path}")
```

Then in `main()`, after step 11 (all individual PDFs are written, around line 1314) and before step 12 (print summary), add:

1. Build an ordered list of the individual PDF paths that were actually generated. The order should be: form_1041, schedule_d, form_8949, form_8960, form_1041v — skipping any that were not generated for this trust.
2. Define the combined output path as: `output_dir / f"{year} Combined {entity_name}.pdf"`
3. Call `combine_pdfs(ordered_paths, combined_path)`.
4. Add the combined path to output_paths so it appears in the print_summary output.

The ordered list construction should look like:
```python
# Combine all filled PDFs into a single file
form_order = ["form_1041", "schedule_d", "form_8949", "form_8960", "form_1041v"]
filled_pdfs = [output_paths[k] for k in form_order if k in output_paths]
combined_path = output_dir / f"{year} Combined {entity_name}.pdf"
combine_pdfs(filled_pdfs, combined_path)
output_paths["combined"] = combined_path
```

Important: This must come AFTER the 1041-V voucher is filled (line ~1314) and AFTER the amended statement is written (line ~1343), but BEFORE the print_summary call. The amended return statement (.txt) should NOT be included in the combined PDF (it is not a PDF).

Do NOT remove individual PDF generation — keep both individual and combined outputs.
  </action>
  <verify>
    <automated>cd C:/Users/TrentFoley/Source/dynasty-trust-taxes && /c/ProgramData/miniconda3/python fill_1041.py --trust trent --year 2025 && test -f "output/trent/2025 Combined Trent Foley Childrens 2021 Super Dynasty Trust.pdf" && /c/ProgramData/miniconda3/python -c "from pypdf import PdfReader; r = PdfReader('output/trent/2025 Combined Trent Foley Childrens 2021 Super Dynasty Trust.pdf'); print(f'Pages: {len(r.pages)}'); assert len(r.pages) > 5, f'Expected >5 pages, got {len(r.pages)}'" && /c/ProgramData/miniconda3/python fill_1041.py --trust chris --year 2025 && test -f "output/chris/2025 Combined Christopher Foley Childrens 2021 Super Dynasty Trust.pdf" && /c/ProgramData/miniconda3/python -c "from pypdf import PdfReader; r = PdfReader('output/chris/2025 Combined Christopher Foley Childrens 2021 Super Dynasty Trust.pdf'); print(f'Pages: {len(r.pages)}'); assert len(r.pages) >= 2, f'Expected >=2 pages, got {len(r.pages)}'"</automated>
  </verify>
  <done>
    - fill_1041.py --trust trent produces "2025 Combined Trent Foley Childrens 2021 Super Dynasty Trust.pdf" containing all 5 forms (1041 + Sched D + 8949 + 8960 + 1041-V)
    - fill_1041.py --trust chris produces "2025 Combined Christopher Foley Childrens 2021 Super Dynasty Trust.pdf" containing 2 forms (1041 + 1041-V)
    - Individual form PDFs are still generated alongside the combined PDF
    - Combined PDF page count equals sum of individual PDF page counts
  </done>
</task>

</tasks>

<verification>
- Run for both trusts and verify combined PDFs exist
- Verify combined PDF page count matches sum of individual forms
- Verify individual PDFs still exist (not removed)
- Open combined PDF manually to confirm all forms render correctly
</verification>

<success_criteria>
- Single combined PDF generated per trust containing all applicable forms in correct order
- Individual form PDFs preserved
- Both trent and chris trusts produce correct combined output
- No regression in existing form generation
</success_criteria>

<output>
After completion, create `.planning/quick/001-combine-pdf-output/001-SUMMARY.md`
</output>
