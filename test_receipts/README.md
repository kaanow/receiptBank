# Test receipts for OCR

Drop receipt images or PDFs here for local OCR testing.

**Expected vs actual:** See `ANALYSIS.md` and `expected.json`. Run from repo root:
```bash
python backend/scripts/analyze_test_receipts.py          # compare parser to expected
python backend/scripts/analyze_test_receipts.py --save-ocr   # same + save raw OCR to ocr/*.txt
```
With tesseract (or Docker: `./backend/scripts/run_ocr_receipts_docker.sh`) you get real OCR; then `--save-ocr` fills `ocr/` and `pytest backend/tests/test_ocr.py` will run regression tests against `expected.json`.

**Quick one-file extract:** From repo root:
```bash
cd backend && python -c "
from pathlib import Path
from app.ocr import extract_receipt_data
path = Path('../test_receipts').glob('*').__next__()
content = path.read_bytes()
mime = 'image/jpeg' if path.suffix.lower() in ('.jpg','.jpeg') else 'image/png' if path.suffix.lower()=='.png' else 'application/pdf'
d = extract_receipt_data(content, mime)
print(d)
"
```
