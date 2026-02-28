# Test receipt analysis

Results from the **live site** (https://r.alti2.de). No local backend. See **docs/TESTING.md** for the plan and task checklist.

| File | Raw OCR (excerpt) | Parsed | Expected | Match |
|------|-------------------|--------|----------|-------|
| Ferry.HEIC | (no ocr/*.json — run fetch_ocr_from_web_tool.py) | {} | {"vendor": "BC Ferries", "date": "2026-01-01", "amount": 20.0, "amount_subtotal": null, "tax_gst": null, "tax_pst": null} | ✗ fetch first |
| IMG_6892.HEIC | (empty) | {} | — | ✓ |
| Tess tools - air sprayer.HEIC | (empty) | {} | — | ✓ |
| fuel_20260123-1612.jpg | (empty) | {"vendor": "Unknown", "date": null, "amount": null, "amount_subtotal": null, "tax_gst": null, "tax_pst": null} | {"vendor": "PETRO-CANADA", "date": "2026-01-23", "amount": 77.17, "amount_subtotal": null, "tax_gst": 3.67, "tax_pst": null} | ✗  |
