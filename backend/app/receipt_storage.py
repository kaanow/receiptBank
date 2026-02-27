import os
import re
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.models import Account, Expense


def slugify(s: str, max_len: int = 40) -> str:
    """Lowercase, replace spaces with -, remove non-alphanumeric, truncate."""
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = s.strip("-")[:max_len]
    return s or "unknown"


def build_receipt_filename(expense: Expense, account: Account, existing_count: int, ext: str) -> str:
    """Format: {date_ISO}_{account_friendly_name}_{vendor_slug}_{n}.{ext}"""
    date_str = expense.date.strftime("%Y-%m-%d") if hasattr(expense.date, "strftime") else str(expense.date)[:10]
    friendly = slugify(account.friendly_name, max_len=30)
    vendor_slug = slugify(expense.vendor, max_len=30)
    n = existing_count + 1
    return f"{date_str}_{friendly}_{vendor_slug}_{n}.{ext}"


def get_storage_dir(account_id: int, year: int) -> Path:
    base = Path(settings.file_storage_path)
    path = base / str(account_id) / str(year)
    path.mkdir(parents=True, exist_ok=True)
    return path


def receipt_stored_path(expense: Expense, account: Account, existing_count: int, original_filename: str) -> tuple[Path, str]:
    """Return (full_path, stored_relative_path) for saving a new receipt."""
    ext = Path(original_filename).suffix.lstrip(".").lower() or "bin"
    if ext not in ("pdf", "jpg", "jpeg", "png", "gif", "webp"):
        ext = "bin"
    year = expense.date.year if hasattr(expense.date, "year") else datetime.now().year
    dir_path = get_storage_dir(account.id, year)
    filename = build_receipt_filename(expense, account, existing_count, ext)
    full_path = dir_path / filename
    # Stored path for DB: relative to file_storage_path
    stored_relative = f"{account.id}/{year}/{filename}"
    return full_path, stored_relative
