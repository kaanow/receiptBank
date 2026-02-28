# ReceiptBank

Mobile-friendly expense and receipt tracker: upload receipt images/PDFs, auto-extract data (OCR), tag by account/job, run reports (tax and monthly) with optional receipt bundles. Multi-user with grantable access. CAD only; BC rental categories supported. **UI: dark mode only.**

## Setup

- **Backend**: `cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- **Frontend**: `cd frontend && npm install` (run once to generate `package-lock.json`, then commit it for CI).
- **Database**: Postgres; set `DATABASE_URL`. Run migrations: `cd backend && alembic upgrade head`
- **Env**: Copy `backend/.env.example` to `backend/.env` and set secrets.

## Run locally (development)

- Backend: `cd backend && uvicorn app.main:app --reload`
- Frontend: `cd frontend && npm run dev`

**Receipt testing** does not use a local backend. It runs against the live site. See **docs/TESTING.md** for the plan and task checklist.

## CI

GitHub Actions runs on push to `main`: backend tests (pytest) and frontend tests (npm test). See `.github/workflows/ci.yml`.

## Project rules

The `.cursor/` folder (including `.cursor/rules/`) is committed so that pulling the repo preserves rules and conventions; include it in commits when you change it.

## Troubleshooting OCR

Receipt testing: run `python backend/scripts/run_receipt_ocr.py` then `analyze_test_receipts.py`. See **docs/TESTING.md**.
