#!/usr/bin/env python3
"""
Print raw OCR text for a receipt image/PDF. Requires tesseract installed locally.
Usage: python -m app.ocr_raw [path]
  path: path to image or PDF (default: ../test_receipts/first image found)
"""
import sys
from pathlib import Path

# Add backend to path if run from repo root
if __name__ == "__main__":
    backend = Path(__file__).resolve().parent.parent
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))

from app.ocr import _image_to_text, HAS_OCR

def main():
    if not HAS_OCR:
        print("pytesseract not installed")
        sys.exit(1)
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        test_dir = Path(__file__).resolve().parent.parent.parent / "test_receipts"
        paths = (
            list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.jpeg"))
            + list(test_dir.glob("*.png")) + list(test_dir.glob("*.heic")) + list(test_dir.glob("*.HEIC"))
            + list(test_dir.glob("*.pdf"))
        )
        if not paths:
            print("No image/PDF in test_receipts/ and no path given")
            sys.exit(1)
        path = paths[0]
    if not path.exists():
        print(f"Not found: {path}")
        sys.exit(1)
    content = path.read_bytes()
    mime = "application/pdf" if path.suffix.lower() == ".pdf" else ("image/heic" if path.suffix.lower() == ".heic" else "image/jpeg")
    text = _image_to_text(content, mime)
    print(f"--- RAW OCR TEXT: {path.name} ---")
    print(text)
    print("--- END ---")

if __name__ == "__main__":
    main()
