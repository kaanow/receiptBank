# Test receipts for OCR

Drop receipt images here. Run the app's OCR pipeline (no server, no credentials):

```bash
python backend/scripts/run_receipt_ocr.py   # writes test_receipts/ocr/*.json
python backend/scripts/analyze_test_receipts.py   # compares to expected.json, writes ANALYSIS.md
```

See **docs/TESTING.md** for the task checklist.
