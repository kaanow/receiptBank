# Receipt testing

Run the **same OCR pipeline the app uses** (in-process). No server, no login, no account.

## What’s the live site’s OCR output for a local image?

Use the same code the live site runs: `run_receipt_ocr.py`. It produces the same `raw_text` and `parsed` (aside from tesseract/env differences).

- **One file:** `python backend/scripts/run_receipt_ocr.py /path/to/image.jpg`  
  Writes `test_receipts/ocr/<filename>.json`.
- **All images in test_receipts/:** `python backend/scripts/run_receipt_ocr.py`

Needs tesseract installed (e.g. `brew install tesseract`) for non-empty OCR.

## Compare to expectations

1. **Run the pipeline** (all images in test_receipts/):
   ```bash
   python backend/scripts/run_receipt_ocr.py
   ```
   Writes `test_receipts/ocr/<filename>.json` (raw_text + parsed).

2. **Compare and report**:
   ```bash
   python backend/scripts/analyze_test_receipts.py
   ```
   Reads `ocr/*.json`, compares parsed to `test_receipts/expected.json`, writes `test_receipts/ANALYSIS.md`.

No login, no secret, no live site. Just run the scripts.

## Task checklist (multi-step receipt run)

- [ ] **Run OCR**: `python backend/scripts/run_receipt_ocr.py`
- [ ] **Analyze**: `python backend/scripts/analyze_test_receipts.py`
- [ ] **Review** `test_receipts/ANALYSIS.md` (one receipt at a time if discussing)
- [ ] **Update** `test_receipts/expected.json` if we changed expectations
- [ ] **Commit and push**
