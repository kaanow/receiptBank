#!/usr/bin/env python3
"""
Run receipt crop detection on images in test_receipts and report/save results.
Usage: from repo root, python backend/scripts/test_receipt_crop.py
"""
import io
import sys
from pathlib import Path

# Add backend to path
backend = Path(__file__).resolve().parent.parent
if str(backend) not in sys.path:
    sys.path.insert(0, str(backend))

from PIL import Image

from app.ocr import _crop_receipt_to_rect, heic_to_png_bytes, HAS_RECEIPT_CROP


def main():
    test_dir = backend.parent / "test_receipts"
    if not test_dir.exists():
        print(f"Not found: {test_dir}")
        return 1
    out_dir = test_dir / "cropped"
    out_dir.mkdir(exist_ok=True)

    exts = ("*.jpg", "*.jpeg", "*.png", "*.heic", "*.HEIC")
    paths = []
    for e in exts:
        paths.extend(test_dir.glob(e))
    paths = sorted(set(paths))
    if not paths:
        print("No images in test_receipts")
        return 1

    print(f"HAS_RECEIPT_CROP: {HAS_RECEIPT_CROP}")
    print()

    for path in paths:
        try:
            raw = path.read_bytes()
            if path.suffix.lower() == ".heic":
                png = heic_to_png_bytes(raw)
                if not png:
                    print(f"{path.name}: HEIC decode failed")
                    continue
                img = Image.open(io.BytesIO(png))
            else:
                img = Image.open(path)
            if img.mode not in ("L", "RGB"):
                img = img.convert("RGB")
        except Exception as e:
            print(f"{path.name}: open failed {e}")
            continue

        w, h = img.size
        cropped = _crop_receipt_to_rect(img)
        if cropped is not None:
            cw, ch = cropped.size
            out_path = out_dir / f"{path.stem}_cropped.png"
            cropped.save(out_path)
            print(f"{path.name}: {w}x{h} -> CROPPED {cw}x{ch} -> {out_path.name}")
        else:
            print(f"{path.name}: {w}x{h} -> no crop")

    return 0


if __name__ == "__main__":
    sys.exit(main())
