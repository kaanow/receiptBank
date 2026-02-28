# Receipt testing (live site only)

There is **no local backend** on this machine. All receipt OCR and parser testing runs against the **live site** (https://r.alti2.de).

## Prerequisites

- Live site deployed with `POST /debug/ocr-probe` and **DEBUG_OCR_SECRET** set in server env.
- You know the value of DEBUG_OCR_SECRET (same as on the server).

## Plan (run in order)

| Step | Action | Command / outcome |
|------|--------|-------------------|
| 1 | Fetch OCR + parsed from live site | `DEBUG_OCR_SECRET=<secret> python backend/scripts/fetch_ocr_from_web_tool.py` → writes `test_receipts/ocr/*.json` |
| 2 | Compare to expected, write report | `python backend/scripts/analyze_test_receipts.py` → writes `test_receipts/ANALYSIS.md`, exit 0 = all match |
| 3 | Review | Open `test_receipts/ANALYSIS.md`; discuss any FAILs |
| 4 | Update expectations if needed | Edit `test_receipts/expected.json`; re-run step 2 to confirm |
| 5 | Commit and push | `git add -A && git commit -m "..." && git push` |

If fetch returns **404**: the debug route is not enabled on the server. Ensure the deploy includes the `/debug/ocr-probe` route and that **DEBUG_OCR_SECRET** is set in production env.

If fetch returns **403**: wrong or missing `X-Debug-Secret`. Use the same value as on the server.

**Let the assistant run tests without you:** Set `DEBUG_OCR_SECRET` in production and share that value once. The assistant can then run `fetch_ocr_from_web_tool.py` against the live site to get real OCR for all images (no login, no manual uploads).

---

## Task checklist (multi-step receipt run)

Use this after a context switch to get back on task:

- [ ] **Fetch** from live site: `DEBUG_OCR_SECRET=... python backend/scripts/fetch_ocr_from_web_tool.py`
- [ ] **Analyze**: `python backend/scripts/analyze_test_receipts.py`
- [ ] **Review** `test_receipts/ANALYSIS.md` (one receipt at a time if discussing)
- [ ] **Update** `test_receipts/expected.json` if we changed expectations
- [ ] **Commit and push** (include ANALYSIS.md and ocr/*.json if updated)
