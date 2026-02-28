#!/usr/bin/env python3
"""
Fetch actual OCR + parsed results from our web tool (POST /debug/ocr-probe) for each
test receipt image. Saves one JSON per image to test_receipts/ocr/<filename>.json.
Uses the **live site** by default (no local backend on this machine).

  DEBUG_OCR_SECRET=your-secret   # must be set on the server and here
  python backend/scripts/fetch_ocr_from_web_tool.py
  # Override: DEBUG_OCR_BASE_URL=https://other.example.com
"""
import json
import os
import sys
from pathlib import Path

try:
    import httpx
except ImportError:
    print("pip install httpx", file=sys.stderr)
    sys.exit(1)

backend = Path(__file__).resolve().parent.parent
repo_root = backend.parent
test_dir = repo_root / "test_receipts"
ocr_dir = test_dir / "ocr"
base_url = os.environ.get("DEBUG_OCR_BASE_URL", "https://r.alti2.de").rstrip("/")
secret = os.environ.get("DEBUG_OCR_SECRET")
if not secret:
    print("Set DEBUG_OCR_SECRET", file=sys.stderr)
    sys.exit(1)

ocr_dir.mkdir(parents=True, exist_ok=True)
exts = ("*.jpg", "*.jpeg", "*.png", "*.heic", "*.HEIC")
paths = []
for e in exts:
    paths.extend(test_dir.glob(e))
paths = sorted(set(p for p in paths if p.is_file()))

for path in paths:
    name = path.name
    out_path = ocr_dir / f"{name}.json"
    url = f"{base_url}/debug/ocr-probe"
    try:
        with open(path, "rb") as f:
            r = httpx.post(
                url,
                headers={"X-Debug-Secret": secret},
                files={"file": (name, f.read(), "application/octet-stream")},
                timeout=120.0,
            )
        r.raise_for_status()
        data = r.json()
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
        raw_len = len(data.get("raw_text") or "")
        print(f"  {name} -> {out_path.name}  (raw: {raw_len} chars)")
    except Exception as e:
        print(f"  {name} FAIL: {e}", file=sys.stderr)

print("Done. Run python backend/scripts/analyze_test_receipts.py to compare to expected.json")
