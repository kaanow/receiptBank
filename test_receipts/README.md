# Test receipts for OCR

Drop receipt images or PDFs here for local OCR testing.

**Example:** Copy your Petro-Canada receipt here (e.g. `petro-canada-2026-01-23.jpg`).  
Run from repo root:
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
