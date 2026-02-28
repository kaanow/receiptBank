# Test receipt analysis

Actual parser output comes from **our web tool on the live site** (Debug OCR page or `POST /debug/ocr-probe` at https://r.alti2.de). There is no local backend; run fetch against the live site.

| File | Raw OCR (excerpt) | Parsed (from web tool) | Expected | Match |
|------|-------------------|------------------------|----------|-------|
| Ferry.HEIC | (empty) | {"vendor": "Unknown", "date": null, "amount": null, "amount_subtotal": null, "tax_gst": null, "tax_pst": null} | {"vendor": "BC Ferries", "date": "2026-01-01", "amount": 20.0, "amount_subtotal": null, "tax_gst": null, "tax_pst": null} | ✗  |
| IMG_6892.HEIC | (empty) | {"vendor": "Unknown", "date": null, "amount": null, "amount_subtotal": null, "tax_gst": null, "tax_pst": null} | — | ✓ |
| Tess tools - air sprayer.HEIC | (empty) | {"vendor": "Unknown", "date": null, "amount": null, "amount_subtotal": null, "tax_gst": null, "tax_pst": null} | — | ✓ |
| fuel_20260123-1612.jpg | (empty) | {"vendor": "Unknown", "date": null, "amount": null, "amount_subtotal": null, "tax_gst": null, "tax_pst": null} | {"vendor": "PETRO-CANADA", "date": "2026-01-23", "amount": 77.17, "amount_subtotal": null, "tax_gst": 3.67, "tax_pst": null} | ✗  |
