# Test receipts for OCR

Drop receipt images or PDFs here for local OCR testing.

**Actual OCR from our web tool (live site):** Fetch from the live site’s `POST /debug/ocr-probe` (no local backend). Set `DEBUG_OCR_SECRET` to match the server, then:

```bash
DEBUG_OCR_SECRET=your-secret python backend/scripts/fetch_ocr_from_web_tool.py   # writes test_receipts/ocr/*.json
python backend/scripts/analyze_test_receipts.py   # compares to expected.json, writes ANALYSIS.md
```

See `ANALYSIS.md` for the comparison table (raw OCR excerpt, parsed, expected, match).

**Quick one-file extract:** From repo root:
```bash
cd backend && python -c "
from pathlib import Path
from app.ocr import extract_receipt_data
path = next(Path('../test_receipts').glob('*.*'))
content = path.read_bytes()
mime = 'image/jpeg' if path.suffix.lower() in ('.jpg','.jpeg') else 'image/png' if path.suffix.lower()=='.png' else 'application/pdf'
print(extract_receipt_data(content, mime))
"
```
