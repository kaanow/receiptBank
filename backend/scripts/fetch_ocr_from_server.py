#!/usr/bin/env python3
"""
Fetch OCR + parsed from the live server without login. Uses POST /api/expenses/extract-test.
Saves test_receipts/ocr/<filename>.json.

Usage:

  python backend/scripts/fetch_ocr_from_server.py
    → all images in test_receipts/
  python backend/scripts/fetch_ocr_from_server.py /path/to/image.jpg
    → that one file

Override base URL: RECEIPTBANK_BASE_URL=https://r.alti2.de (default).
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

repo_root = Path(__file__).resolve().parent.parent.parent
test_dir = repo_root / "test_receipts"
ocr_dir = test_dir / "ocr"
base_url = os.environ.get("RECEIPTBANK_BASE_URL", "https://r.alti2.de").rstrip("/")

ocr_dir.mkdir(parents=True, exist_ok=True)


def process(path: Path, client: httpx.Client) -> None:
    name = path.name
    out_path = ocr_dir / f"{name}.json"
    try:
        with open(path, "rb") as f:
            content = f.read()
        r = client.post(
            f"{base_url}/api/expenses/extract-test",
            files={"file": (name, content, "application/octet-stream")},
        )
        if r.status_code >= 400:
            try:
                err = r.json()
                msg = err.get("detail", r.text) or r.text
            except Exception:
                msg = r.text or str(r.status_code)
            print(f"  {name} FAIL: {r.status_code} {msg}", file=sys.stderr)
            return
        r.raise_for_status()
        data = r.json()
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
        raw_len = len(data.get("raw_text") or "")
        print(f"  {name} -> {out_path.name}  (raw: {raw_len} chars)")
    except Exception as e:
        print(f"  {name} FAIL: {e}", file=sys.stderr)


def main():
    if len(sys.argv) > 1:
        for p in sys.argv[1:]:
            path = Path(p).resolve()
            if not path.is_file():
                print(f"Not a file: {path}", file=sys.stderr)
                continue
            with httpx.Client(timeout=120.0) as client:
                process(path, client)
        return

    exts = ("*.jpg", "*.jpeg", "*.png", "*.heic", "*.HEIC")
    paths = []
    for e in exts:
        paths.extend(test_dir.glob(e))
    paths = sorted(set(p for p in paths if p.is_file()))
    if not paths:
        print("No images in test_receipts/")
        sys.exit(1)
    with httpx.Client(timeout=120.0) as client:
        for path in paths:
            process(path, client)
    print("Done. Run python backend/scripts/analyze_test_receipts.py to compare.")


if __name__ == "__main__":
    main()
