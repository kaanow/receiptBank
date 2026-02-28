#!/usr/bin/env python3
"""
Fetch OCR + parsed from the live site: log in with email/password (session), then POST each image to /api/expenses/extract-debug.
Saves test_receipts/ocr/<filename>.json.

Create a test account on the site, then:
  RECEIPTBANK_TEST_EMAIL=you@example.com RECEIPTBANK_TEST_PASSWORD=xxx python backend/scripts/fetch_ocr_via_login.py

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

backend = Path(__file__).resolve().parent.parent
repo_root = backend.parent
test_dir = repo_root / "test_receipts"
ocr_dir = test_dir / "ocr"
base_url = os.environ.get("RECEIPTBANK_BASE_URL", "https://r.alti2.de").rstrip("/")
email = os.environ.get("RECEIPTBANK_TEST_EMAIL")
password = os.environ.get("RECEIPTBANK_TEST_PASSWORD")
if not email or not password:
    print("Set RECEIPTBANK_TEST_EMAIL and RECEIPTBANK_TEST_PASSWORD (use a test account on the site)", file=sys.stderr)
    sys.exit(1)

ocr_dir.mkdir(parents=True, exist_ok=True)
exts = ("*.jpg", "*.jpeg", "*.png", "*.heic", "*.HEIC")
paths = []
for e in exts:
    paths.extend(test_dir.glob(e))
paths = sorted(set(p for p in paths if p.is_file()))
if not paths:
    print("No images in test_receipts/")
    sys.exit(1)

# Login then extract-debug with session cookie
client = httpx.Client(base_url=base_url, timeout=120.0, follow_redirects=True)
try:
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    r.raise_for_status()
except Exception as e:
    print(f"Login FAIL: {e}", file=sys.stderr)
    sys.exit(1)

for path in paths:
    name = path.name
    out_path = ocr_dir / f"{name}.json"
    try:
        with open(path, "rb") as f:
            content = f.read()
        r = client.post(
            "/api/expenses/extract-debug",
            files={"file": (name, content, "application/octet-stream")},
        )
        r.raise_for_status()
        data = r.json()
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
        raw_len = len(data.get("raw_text") or "")
        print(f"  {name} -> {out_path.name}  (raw: {raw_len} chars)")
    except Exception as e:
        print(f"  {name} FAIL: {e}", file=sys.stderr)

client.close()
print("Done. Run python backend/scripts/analyze_test_receipts.py to compare.")
