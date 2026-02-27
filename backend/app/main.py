from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
import os

from app.config import settings
from app.routers import accounts, auth, expenses, reports

app = FastAPI(
    title="ReceiptBank API",
    description="Expense and receipt tracker API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)

app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(expenses.router)
app.include_router(reports.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"service": "ReceiptBank API", "docs": "/docs"}


# Serve frontend SPA at /app (when static files are present)
_STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")
_INDEX_HTML = os.path.join(_STATIC_DIR, "index.html")
if os.path.isfile(_INDEX_HTML):
    app.mount("/app/assets", StaticFiles(directory=os.path.join(_STATIC_DIR, "assets")), name="assets")

    @app.get("/app")
    @app.get("/app/")
    def _spa_root():
        return FileResponse(_INDEX_HTML)

    @app.get("/app/{path:path}")
    def _spa_catchall(path: str):
        return FileResponse(_INDEX_HTML)
