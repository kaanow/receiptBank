# Receipt testing (live site only)

There is **no local backend** on this machine. All receipt OCR and parser testing runs against the **live site** (https://r.alti2.de).

## How to fetch real OCR (no debug secret)

Use the **same path as the Debug OCR page**: log in with a test account, then call the extract-debug endpoint. No server-side secret required.

1. Create a **test account** on the site (register at the app).
2. Set env and run:
   ```bash
   RECEIPTBANK_TEST_EMAIL=your-test@example.com RECEIPTBANK_TEST_PASSWORD=xxx python backend/scripts/fetch_ocr_via_login.py
   ```
   Writes `test_receipts/ocr/*.json` (raw_text + parsed for each image).
3. The assistant can run this if you provide those env vars (e.g. in the chat or in a local .env the assistant can read).

Override base URL: `RECEIPTBANK_BASE_URL=https://r.alti2.de` (default).

## Alternative: debug secret

If you prefer not to use a test account, set **DEBUG_OCR_SECRET** in production and run:
`DEBUG_OCR_SECRET=<secret> python backend/scripts/fetch_ocr_from_web_tool.py`

## Plan (run in order)

| Step | Action | Command / outcome |
|------|--------|-------------------|
| 1 | Fetch OCR + parsed from live site | `fetch_ocr_via_login.py` (or `fetch_ocr_from_web_tool.py` with secret) → writes `test_receipts/ocr/*.json` |
| 2 | Compare, write report | `python backend/scripts/analyze_test_receipts.py` → writes `test_receipts/ANALYSIS.md` |
| 3 | Review | Open `test_receipts/ANALYSIS.md`; discuss per receipt |
| 4 | Update expectations if needed | Edit `test_receipts/expected.json`; re-run step 2 |
| 5 | Commit and push | `git add -A && git commit -m "..." && git push` |

---

## Task checklist (multi-step receipt run)

Use this after a context switch to get back on task:

- [ ] **Fetch** from live site: `RECEIPTBANK_TEST_EMAIL=... RECEIPTBANK_TEST_PASSWORD=... python backend/scripts/fetch_ocr_via_login.py`
- [ ] **Analyze**: `python backend/scripts/analyze_test_receipts.py`
- [ ] **Review** `test_receipts/ANALYSIS.md` (one receipt at a time if discussing)
- [ ] **Update** `test_receipts/expected.json` if we changed expectations
- [ ] **Commit and push** (include ANALYSIS.md and ocr/*.json if updated)
