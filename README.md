# ReceiptBank

Mobile-friendly expense and receipt tracker: upload receipt images/PDFs, auto-extract data (OCR), tag by account/job, run reports (tax and monthly) with optional receipt bundles. Multi-user with grantable access. CAD only; BC rental categories supported.

## Setup

- **Backend**: `cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- **Frontend**: `cd frontend && npm install`
- **Database**: Postgres; set `DATABASE_URL`. Run migrations: `cd backend && alembic upgrade head`
- **Env**: Copy `backend/.env.example` to `backend/.env` and set secrets.

## Run locally

- Backend: `cd backend && uvicorn app.main:app --reload`
- Frontend: `cd frontend && npm run dev`

## CI

GitHub Actions runs on push to `main`: backend tests (pytest) and frontend tests (npm test). See `.github/workflows/ci.yml`.
