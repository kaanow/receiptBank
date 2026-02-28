#!/usr/bin/env python3
"""
Run the app's OCR pipeline (same code as the live site). No server, no login, no account.
Writes test_receipts/ocr/<filename>.json with raw_text and parsed.

Dependencies:
- Backend Python deps: run from backend venv or a Python with pip install -r backend/requirements.txt.
- Tesseract binary on PATH (e.g. brew install tesseract). Without it, raw_text is empty.
- HEIC: pillow-heif (+ libheif on Linux). PDF: pdf2image (+ poppler).

  cd backend && python scripts/run_receipt_ocr.py
    → all images in test_receipts/
  cd backend && python scripts/run_receipt_ocr.py /path/to/image.jpg
    → that one file, writes test_receipts/ocr/<filename>.json
"""
import json
import shutil
import sys
from pathlib import Path

backend = Path(__file__).resolve().parent.parent
if str(backend) not in sys.path:
    sys.path.insert(0, str(backend))

from app.ocr import _image_to_text, extract_receipt_data, heic_to_png_bytes

repo_root = backend.parent
test_dir = repo_root / "test_receipts"
ocr_dir = test_dir / "ocr"
ocr_dir.mkdir(parents=True, exist_ok=True)


def process(path: Path) -> None:
    raw = path.read_bytes()
    if path.suffix.lower() == ".heic":
        png = heic_to_png_bytes(raw)
        if not png:
            print(f"  {path.name}: HEIC decode failed")
            return
        content, mime = png, "image/png"
    else:
        mime = "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
        content = raw

    raw_text = _image_to_text(content, mime)
    parsed = extract_receipt_data(content, mime)
    p = dict(parsed)
    if p.get("date") and hasattr(p["date"], "isoformat"):
        p["date"] = p["date"].isoformat()
    out = {"raw_text": raw_text, "parsed": p}
    out_path = ocr_dir / f"{path.name}.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"  {path.name} -> {out_path}  (raw: {len(raw_text)} chars)")


def main():
    if not shutil.which("tesseract"):
        print("Tesseract not found on PATH (e.g. brew install tesseract). OCR will be empty.")
    if len(sys.argv) > 1:
        p = Path(sys.argv[1]).resolve()
        if not p.is_file():
            print(f"Not a file: {p}")
            sys.exit(1)
        process(p)
        return

    exts = ("*.jpg", "*.jpeg", "*.png", "*.heic", "*.HEIC")
    paths = []
    for e in exts:
        paths.extend(test_dir.glob(e))
    paths = sorted(set(p for p in paths if p.is_file()))
    if not paths:
        print("No images in test_receipts/")
        sys.exit(1)
    for path in paths:
        process(path)
    print("Done. Run python backend/scripts/analyze_test_receipts.py to compare.")


if __name__ == "__main__":
    main()
