#!/usr/bin/env python3
"""
Run OCR + extract on test_receipts and compare to test_receipts/expected.json.
Usage: from repo root, python backend/scripts/analyze_test_receipts.py [--save-ocr]
  --save-ocr  Write raw OCR text to test_receipts/ocr/<basename>.txt for regression tests.
Exit: 0 if all files with expectations match; 1 if any mismatch or no tesseract.
"""
import json
import sys
from pathlib import Path

backend = Path(__file__).resolve().parent.parent
if str(backend) not in sys.path:
    sys.path.insert(0, str(backend))

from app.ocr import _image_to_text, extract_receipt_data, heic_to_png_bytes


def normalize_parsed(data: dict) -> dict:
    """To compare: date as YYYY-MM-DD string or null, same keys as expected.json."""
    out = {
        "vendor": data.get("vendor") or "Unknown",
        "date": None,
        "amount": data.get("amount"),
        "amount_subtotal": data.get("amount_subtotal"),
        "tax_gst": data.get("tax_gst"),
        "tax_pst": data.get("tax_pst"),
    }
    d = data.get("date")
    if d is not None:
        out["date"] = d.isoformat()[:10] if hasattr(d, "isoformat") else str(d)[:10]
    return out


def load_expected(repo_root: Path) -> dict:
    p = repo_root / "test_receipts" / "expected.json"
    if not p.exists():
        return {}
    with open(p) as f:
        return json.load(f)


def run_one(path: Path, repo_root: Path, save_ocr: bool) -> tuple:
    """Run pipeline; return (basename, raw_text, parsed_dict, error)."""
    raw = path.read_bytes()
    if path.suffix.lower() == ".heic":
        png = heic_to_png_bytes(raw)
        if not png:
            return path.name, "", {}, "HEIC decode failed"
        content, mime = png, "image/png"
    else:
        mime = "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
        content = raw

    text = _image_to_text(content, mime)
    data = extract_receipt_data(content, mime)
    parsed = normalize_parsed(data)

    if save_ocr:
        ocr_dir = repo_root / "test_receipts" / "ocr"
        ocr_dir.mkdir(exist_ok=True)
        txt_path = ocr_dir / f"{path.stem}.txt"
        txt_path.write_text(text, encoding="utf-8")

    return path.name, text, parsed, None


def main():
    save_ocr = "--save-ocr" in sys.argv
    repo_root = backend.parent
    test_dir = repo_root / "test_receipts"
    expected = load_expected(repo_root)

    exts = ("*.jpg", "*.jpeg", "*.png", "*.heic", "*.HEIC")
    paths = []
    for e in exts:
        paths.extend(test_dir.glob(e))
    paths = sorted(set(p for p in paths if p.is_file() and p.name != "README.md"))

    if not paths:
        print("No images in test_receipts/")
        return 1

    all_ok = True
    for path in paths:
        name, raw_text, parsed, err = run_one(path, repo_root, save_ocr)
        exp = expected.get(name)
        if err:
            print(f"  {name}: ERROR {err}")
            if exp is not None:
                all_ok = False
            continue
        if exp is None:
            print(f"  {name}: (no expected) parsed={parsed}")
            continue
        exp_date = exp.get("date")
        exp_amount = exp.get("amount")
        exp_vendor = exp.get("vendor")
        ok = True
        if exp_vendor is not None and parsed.get("vendor") != exp_vendor:
            ok = False
        if exp_date is not None and parsed.get("date") != exp_date:
            ok = False
        if exp_amount is not None and parsed.get("amount") != exp_amount:
            ok = False
        for key in ("tax_gst", "tax_pst", "amount_subtotal"):
            if exp.get(key) is not None and parsed.get(key) != exp.get(key):
                ok = False
        if ok:
            print(f"  {name}: OK  {parsed}")
        else:
            print(f"  {name}: FAIL  expected={exp}  got={parsed}")
            all_ok = False

    if save_ocr:
        print("(OCR saved to test_receipts/ocr/)")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
