#!/usr/bin/env python3
"""
Run the same pipeline as the web app on receipt images: HEIC→PNG then OCR + extract.
Usage: from repo root, python backend/scripts/run_ocr_on_receipts.py [path_or_dir]
  If no path given, runs on all images in test_receipts/.
  Requires tesseract installed (e.g. brew install tesseract) or run inside app Docker image.
"""
import io
import sys
from pathlib import Path

backend = Path(__file__).resolve().parent.parent
if str(backend) not in sys.path:
    sys.path.insert(0, str(backend))

from app.ocr import _image_to_text, extract_receipt_data, heic_to_png_bytes


def process_file(path: Path) -> None:
    """Same as web: HEIC→PNG if needed, then _image_to_text + extract_receipt_data."""
    raw = path.read_bytes()
    if path.suffix.lower() == ".heic":
        png = heic_to_png_bytes(raw)
        if not png:
            print(f"[{path.name}] HEIC decode failed\n")
            return
        content, mime = png, "image/png"
    else:
        content, mime = raw, "image/jpeg"

    text = _image_to_text(content, mime)
    data = extract_receipt_data(content, mime)

    print(f"=== {path.name} ===")
    print("RAW OCR:")
    print(text if text.strip() else "(empty)")
    print()
    print("PARSED:", data)
    print()


def main():
    if len(sys.argv) > 1:
        p = Path(sys.argv[1])
        if p.is_file():
            process_file(p)
            return 0
        if p.is_dir():
            test_dir = p
        else:
            print(f"Not found: {p}")
            return 1
    else:
        test_dir = backend.parent / "test_receipts"
        if not test_dir.exists():
            print(f"Not found: {test_dir}")
            return 1

    exts = ("*.jpg", "*.jpeg", "*.png", "*.heic", "*.HEIC")
    paths = []
    for e in exts:
        paths.extend(test_dir.glob(e))
    paths = sorted(set(paths))
    if not paths:
        print("No images found")
        return 1

    for path in paths:
        process_file(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
