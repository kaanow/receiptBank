# Receipt testing

## Run OCR on the server (no login)

Run the **live server’s** OCR pipeline without a test account. No secret required.

**Temporary use:** This endpoint is for receipt-testing phases. When testing is complete, suspend it (see below). Re-enable when you have more receipt/OCR work to test.

```bash
curl -s -X POST "https://YOUR_SERVER/api/expenses/extract-test" \
  -F "file=@/path/to/receipt.jpg"
```

Response: `{"raw_text": "...", "parsed": { ... }}` (same shape as extract-debug).

Script:

```bash
python backend/scripts/fetch_ocr_from_server.py
# or one file:
python backend/scripts/fetch_ocr_from_server.py /path/to/receipt.jpg
```
Writes `test_receipts/ocr/<filename>.json`. Override server: `RECEIPTBANK_BASE_URL=https://...`

**Suspend when not testing:** The route is normally **commented out** in `backend/app/routers/expenses.py` (search for `extract-test`). Uncomment to re-enable when you need server-side OCR without login; comment out again when done. See also `.cursor/rules/extract-test-endpoint.mdc`.

---

## Run OCR locally (same code, no server)

Run the **same OCR pipeline** in-process. No server, no login, no account.

**Dependencies:** Backend Python deps (`cd backend && pip install -r requirements.txt`) and **tesseract** on PATH (e.g. `brew install tesseract`). Without tesseract, `raw_text` is empty.

- **One file:** `cd backend && python scripts/run_receipt_ocr.py /path/to/image.jpg`  
  Writes `test_receipts/ocr/<filename>.json`.
- **All images in test_receipts/:** `cd backend && python scripts/run_receipt_ocr.py`

## Compare to expectations

1. **Run the pipeline** (all images in test_receipts/): from repo root, `cd backend && python scripts/run_receipt_ocr.py`.

2. **Compare and report**:
   ```bash
   python backend/scripts/analyze_test_receipts.py
   ```
   Reads `ocr/*.json`, compares parsed to `test_receipts/expected.json`, writes `test_receipts/ANALYSIS.md`.

No login, no secret, no live site. Just run the scripts.

## Task checklist (multi-step receipt run)

- [ ] **Run OCR**: `cd backend && python scripts/run_receipt_ocr.py`
- [ ] **Analyze**: `python backend/scripts/analyze_test_receipts.py`
- [ ] **Review** `test_receipts/ANALYSIS.md` (one receipt at a time if discussing)
- [ ] **Update** `test_receipts/expected.json` if we changed expectations
- [ ] **Commit and push**
