from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
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
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    path="/",
    same_site="lax",
    https_only=settings.session_cookie_secure,
)

app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(expenses.router)
app.include_router(reports.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/heic")
def health_heic():
    """Public diagnostic: whether HEIC decode is available (for debugging live deploy)."""
    from app.ocr import HAS_HEIF
    return {"has_heif": HAS_HEIF, "message": "HEIC decode available" if HAS_HEIF else "HEIC not available (install libheif)"}


def _debug_ocr_allowed(request: Request) -> bool:
    if not getattr(settings, "debug_ocr_secret", None):
        return False
    return request.headers.get("X-Debug-Secret") == settings.debug_ocr_secret


@app.post("/debug/ocr-probe")
async def debug_ocr_probe(request: Request, file: UploadFile = File(...)):
    """
    Troubleshooting: run OCR + extract on an uploaded file. No auth required but
    X-Debug-Secret header must match DEBUG_OCR_SECRET env. If DEBUG_OCR_SECRET is unset, 404.
    Returns { "raw_text": "...", "parsed": { ... } } for debugging.
    """
    if not _debug_ocr_allowed(request):
        if not getattr(settings, "debug_ocr_secret", None):
            return JSONResponse(status_code=404, content={"detail": "debug OCR not enabled"})
        return JSONResponse(status_code=403, content={"detail": "invalid or missing X-Debug-Secret"})
    from app.ocr import _image_to_text, extract_receipt_data, heic_to_png_bytes, HAS_HEIF
    from app.routers.expenses import _normalize_receipt_content_type, ALLOWED_MIME

    content = await file.read()
    content_type = file.content_type or "application/octet-stream"
    content_type = _normalize_receipt_content_type(content_type, content, file.filename)
    if content_type not in ALLOWED_MIME:
        return JSONResponse(status_code=400, content={"detail": "file type not allowed"})
    if content_type == "image/heic" and not HAS_HEIF:
        return JSONResponse(status_code=503, content={"detail": "HEIC not available"})
    if content_type == "image/heic":
        png = heic_to_png_bytes(content)
        if not png:
            return JSONResponse(status_code=503, content={"detail": "HEIC decode failed"})
        content, content_type = png, "image/png"
    raw_text = _image_to_text(content, content_type)
    parsed = extract_receipt_data(content, content_type)
    p = dict(parsed)
    if p.get("date"):
        p["date"] = p["date"].isoformat()
    return {"raw_text": raw_text, "parsed": p}


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
