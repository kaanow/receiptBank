#!/usr/bin/env python3
"""
Compare test receipt parser output to expected.json using only results from the
live-site web tool (test_receipts/ocr/*.json from fetch_ocr_from_web_tool.py).
No local OCR. Writes test_receipts/ANALYSIS.md.
See docs/TESTING.md for the full plan.
Usage: from repo root, python backend/scripts/analyze_test_receipts.py
Exit: 0 if all files with expectations have ocr/*.json and match; 1 otherwise.
"""
import json
import sys
from pathlib import Path
from typing import Optional, Tuple

backend = Path(__file__).resolve().parent.parent
repo_root = backend.parent


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
    """If ocr/<filename>.json exists (from live-site debug endpoint), return (raw_text, parsed)."""
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


def main():
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
        if name.startswith("_"):
            continue
        exp = expected.get(name)
        web = load_web_tool_result(ocr_dir, name)
        if not web:
            raw_text, parsed = "", {}
            if exp is not None:
                print(f"  {name}: SKIP (fetch from live site first)  expected={exp}")
                all_ok = False
                rows.append((name, "(no ocr/*.json — run fetch_ocr_from_web_tool.py)", parsed, exp, False, "fetch first"))
            else:
                print(f"  {name}: (no expected, no data)")
                rows.append((name, "", parsed, exp, True, None))
            continue

        raw_text, parsed = web
        if exp is None:
            print(f"  {name}: (no expected) {parsed}")
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
        print(f"  {name}: {'OK' if ok else 'FAIL'}  expected={exp}  got={parsed}")
        rows.append((name, raw_text[:300], parsed, exp, ok, None))

    analysis_path = repo_root / "test_receipts" / "ANALYSIS.md"
    lines = [
        "# Test receipt analysis",
        "",
        "Results from the **live site** (https://r.alti2.de). No local backend. See **docs/TESTING.md** for the plan and task checklist.",
        "",
        "| File | Raw OCR (excerpt) | Parsed | Expected | Match |",
        "|------|-------------------|--------|----------|-------|",
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
