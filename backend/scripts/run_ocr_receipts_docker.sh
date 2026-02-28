#!/bin/sh
# Optional / deprecated for testing: run OCR on test_receipts inside Docker (HEIC→PNG then tesseract).
# Receipt testing uses the live site: fetch_ocr_from_web_tool.py → analyze_test_receipts.py (see docs/TESTING.md).
# From repo root: ./backend/scripts/run_ocr_receipts_docker.sh
set -e
echo "Building image (has tesseract + libheif)..."
docker build -t receiptbank:ocr .
echo ""
echo "Running OCR on test_receipts (HEIC→PNG same as web)..."
docker run --rm -v "$(pwd)/test_receipts:/data:ro" receiptbank:ocr \
  python -c "
import sys
from pathlib import Path
sys.path.insert(0, '/app')
from app.ocr import _image_to_text, extract_receipt_data, heic_to_png_bytes

test_dir = Path('/data')
for ext in ['*.HEIC', '*.heic', '*.jpg', '*.jpeg', '*.png']:
    for path in sorted(test_dir.glob(ext)):
        if path.name.startswith('cropped') or 'README' in path.name:
            continue
        raw = path.read_bytes()
        if path.suffix.lower() == '.heic':
            png = heic_to_png_bytes(raw)
            if not png:
                print(f'[{path.name}] HEIC decode failed')
                continue
            content, mime = png, 'image/png'
        else:
            content, mime = raw, 'image/jpeg'
        text = _image_to_text(content, mime)
        data = extract_receipt_data(content, mime)
        print('===', path.name, '===')
        print('RAW OCR:')
        print(text[:1200] if text.strip() else '(empty)')
        print()
        print('PARSED:', data)
        print()
"
echo "Done."
