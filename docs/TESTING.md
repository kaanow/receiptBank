# Receipt testing

Run the **same OCR pipeline the app uses** (in-process, no server, no credentials). Then compare to expectations.

## How it works

1. **Run the pipeline** on each image in `test_receipts/`:
   ```bash
   python backend/scripts/run_receipt_ocr.py
   ```
   Uses app code: HEIC→PNG (if needed), tesseract, parser. Writes `test_receipts/ocr/<filename>.json` (raw_text + parsed). Needs tesseract installed (e.g. `brew install tesseract`) for non-empty OCR.

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
