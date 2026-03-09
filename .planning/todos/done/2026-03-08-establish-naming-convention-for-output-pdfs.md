---
created: 2026-03-08T22:10:43.392Z
title: Establish naming convention for output PDFs
area: general
files:
  - fill_1041.py
---

## Problem

Output PDFs currently use hardcoded names like `2025_1041_filled.pdf`. There is no consistent naming convention across forms or years. The desired convention is `<YYYY> <form> <entity name>.pdf` (e.g., `2025 1041 Trent Foley Childrens 2021 Super Dynasty Trust.pdf`).

## Solution

Update `fill_1041.py` output filename generation to follow `{year} {form} {entity_name}.pdf` pattern. Entity name should come from `config/2025.json` (trust name field). Apply consistently to all 4 output forms (1041, Schedule D, 8960, 8949).
