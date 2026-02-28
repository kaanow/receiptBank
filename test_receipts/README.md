# Test receipts for OCR

Drop receipt images or PDFs here. **Receipt testing uses the live site only** (no local backend). See **docs/TESTING.md** for the plan and task checklist.

**Fetch and analyze (live site):**
```bash
DEBUG_OCR_SECRET=your-secret python backend/scripts/fetch_ocr_from_web_tool.py   # writes test_receipts/ocr/*.json
python backend/scripts/analyze_test_receipts.py   # compares to expected.json, writes ANALYSIS.md
```
See `ANALYSIS.md` for the comparison table.
