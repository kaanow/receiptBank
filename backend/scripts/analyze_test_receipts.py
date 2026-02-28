#!/usr/bin/env python3
"""
Compare test receipt parser output to expected.json. Prefers actual results from our
web tool: if test_receipts/ocr/<filename>.json exists (from fetch_ocr_from_web_tool.py),
use that; otherwise run OCR locally. Writes test_receipts/ANALYSIS.md.
Usage: from repo root, python backend/scripts/analyze_test_receipts.py [--save-ocr]
  --save-ocr  When running local OCR, also write raw text to test_receipts/ocr/<stem>.txt
Exit: 0 if all files with expectations match; 1 if any mismatch.
"""
import json
import sys
from pathlib import Path
from typing import Optional, Tuple

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


def load_web_tool_result(ocr_dir: Path, filename: str) -> Optional[Tuple[str, dict]]:
    """If ocr/<filename>.json exists (from our debug endpoint), return (raw_text, parsed)."""
    j = ocr_dir / f"{filename}.json"
    if not j.is_file():
        return None
    with open(j) as f:
        data = json.load(f)
    raw = data.get("raw_text") or ""
    parsed = dict(data.get("parsed") or {})
    if parsed.get("date") and not isinstance(parsed["date"], str):
        parsed["date"] = parsed["date"].isoformat()[:10] if hasattr(parsed["date"], "isoformat") else str(parsed["date"])[:10]
    return raw, normalize_parsed(parsed)


def run_one_local(path: Path, repo_root: Path, save_ocr: bool) -> Tuple[str, str, dict, Optional[str]]:
    """Run pipeline locally; return (name, raw_text, parsed, error)."""
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
        (ocr_dir / f"{path.stem}.txt").write_text(text, encoding="utf-8")

    return path.name, text, parsed, None


def main():
    save_ocr = "--save-ocr" in sys.argv
    repo_root = backend.parent
    test_dir = repo_root / "test_receipts"
    ocr_dir = test_dir / "ocr"
    expected = load_expected(repo_root)

    exts = ("*.jpg", "*.jpeg", "*.png", "*.heic", "*.HEIC")
    paths = []
    for e in exts:
        paths.extend(test_dir.glob(e))
    paths = sorted(set(p for p in paths if p.is_file()))

    if not paths:
        print("No images in test_receipts/")
        return 1

    rows = []
    all_ok = True
    for path in paths:
        name = path.name
        exp = expected.get(name)
        if name.startswith("_"):
            continue
        web = load_web_tool_result(ocr_dir, name)
        if web:
            raw_text, parsed = web
            source = "web tool"
        else:
            name_out, raw_text, parsed, err = run_one_local(path, repo_root, save_ocr)
            if err:
                print(f"  {name}: ERROR {err}")
                if exp is not None:
                    all_ok = False
                rows.append((name, raw_text[:300], parsed, exp, False, err))
                continue
            source = "local OCR"

        if exp is None:
            print(f"  {name}: ({source}) (no expected) {parsed}")
            rows.append((name, raw_text[:300], parsed, exp, True, None))
            continue

        ok = True
        if exp.get("vendor") is not None and parsed.get("vendor") != exp["vendor"]:
            ok = False
        if exp.get("date") is not None and parsed.get("date") != exp["date"]:
            ok = False
        if exp.get("amount") is not None and parsed.get("amount") != exp["amount"]:
            ok = False
        for key in ("tax_gst", "tax_pst", "amount_subtotal"):
            if exp.get(key) is not None and parsed.get(key) != exp.get(key):
                ok = False
        if not ok:
            all_ok = False
        print(f"  {name}: {'OK' if ok else 'FAIL'}  ({source})  expected={exp}  got={parsed}")
        rows.append((name, raw_text[:300], parsed, exp, ok, None))

    if save_ocr:
        print("(OCR saved to test_receipts/ocr/)")

    # Write ANALYSIS.md
    analysis_path = repo_root / "test_receipts" / "ANALYSIS.md"
    lines = [
        "# Test receipt analysis",
        "",
        "Actual parser output comes from **our web tool** (Debug OCR page or `POST /debug/ocr-probe`).",
        "Run `DEBUG_OCR_SECRET=... python backend/scripts/fetch_ocr_from_web_tool.py` with the backend up to refresh `ocr/*.json`, then run this script.",
        "",
        "| File | Raw OCR (excerpt) | Parsed (from web tool) | Expected | Match |",
        "|------|-------------------|------------------------|----------|-------|",
    ]
    for name, raw_excerpt, parsed, exp, match, err in rows:
        raw_display = (raw_excerpt or "(empty)").replace("|", "\\|").replace("\n", " ")
        if len(raw_display) > 120:
            raw_display = raw_display[:117] + "..."
        p = json.dumps(parsed) if parsed else "{}"
        e = json.dumps(exp) if exp else "—"
        status = "✓" if match else ("✗ " + (err or ""))
        lines.append(f"| {name} | {raw_display} | {p} | {e} | {status} |")
    lines.append("")
    analysis_path.parent.mkdir(parents=True, exist_ok=True)
    analysis_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {analysis_path}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
