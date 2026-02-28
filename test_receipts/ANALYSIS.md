# Test receipt analysis

We compare **expected** parsed fields (human/design interpretation) with **actual** parser output from OCR.

## Expected results

See `expected.json`. Keys are filenames under `test_receipts/` (top-level only; cropped variants use same expectations as the source). `null` means “no expectations yet” or “skip comparison”.

- **Ferry.HEIC / Ferry_converted.jpg** — BC Ferries Langdale/Horseshoe Bay; reservation fee $20, date 2026-01-01.
- **fuel_20260123-1612.jpg** — Petro-Canada fuel; total $77.17, GST $3.67, date 2026-01-23; PST line is reg #, not amount.
- **IMG_6892**, **Tess tools - air sprayer** — TBD once we have stable OCR.

## Run analysis

**With tesseract** (local or Docker):

```bash
# From repo root: run OCR and compare to expected
python backend/scripts/analyze_test_receipts.py
```

That script runs the same pipeline as the app (HEIC→PNG, crop, OCR, parse), then compares `parsed` to `expected.json` and prints pass/fail per file. Optionally it can write raw OCR to `test_receipts/ocr/<basename>.txt` for regression tests.

**Without tesseract:** OCR will be empty and parsed will be `Unknown`/null; comparison will fail for files that have expectations. Run inside Docker or install tesseract (e.g. `brew install tesseract`) to get real OCR.

## Regression tests

`backend/tests/test_ocr.py` has unit tests with **mock OCR text** (e.g. BC Ferries Langdale, Petro-Canada). When we have saved OCR text in `test_receipts/ocr/*.txt`, we can add tests that inject that text and assert parsed matches `expected.json` so CI doesn’t need tesseract.
