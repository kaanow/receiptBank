#!/usr/bin/env python3
"""
Run the app's OCR pipeline on test_receipts (same code as upload flow).
No server, no login, no credentials. Writes test_receipts/ocr/<filename>.json.
From repo root: python backend/scripts/run_receipt_ocr.py
"""
import json
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

exts = ("*.jpg", "*.jpeg", "*.png", "*.heic", "*.HEIC")
paths = []
for e in exts:
    paths.extend(test_dir.glob(e))
paths = sorted(set(p for p in paths if p.is_file()))
if not paths:
    print("No images in test_receipts/")
    sys.exit(1)

for path in paths:
    raw = path.read_bytes()
    if path.suffix.lower() == ".heic":
        png = heic_to_png_bytes(raw)
        if not png:
            print(f"  {path.name}: HEIC decode failed")
            continue
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
    print(f"  {path.name} -> {out_path.name}  (raw: {len(raw_text)} chars)")

print("Done. Run python backend/scripts/analyze_test_receipts.py to compare.")
