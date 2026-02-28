"""
Extract structured data from receipt image/PDF text using regex and heuristics.
Uses pytesseract for OCR; callers pass in raw image bytes or PDF bytes.
"""
import io
import re
from datetime import datetime
from typing import Optional, Tuple

try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

try:
    from pdf2image import convert_from_bytes
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HAS_HEIF = True
except ImportError:
    HAS_HEIF = False


def _image_to_text(image_bytes: bytes, mime_type: str) -> str:
    if not HAS_OCR:
        return ""
    try:
        if mime_type == "application/pdf":
            if not HAS_PDF2IMAGE:
                return ""
            images = convert_from_bytes(image_bytes, first_page=1, last_page=2)
            text_parts = []
            for img in images:
                text_parts.append(pytesseract.image_to_string(img))
            return "\n".join(text_parts)
        if mime_type == "image/heic" and not HAS_HEIF:
            return ""
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode not in ("L", "RGB"):
            img = img.convert("RGB")
        return pytesseract.image_to_string(img)
    except Exception:
        return ""


# Regex patterns for Canadian receipts (GST, PST common)
DATE_PATTERNS = [
    re.compile(r"\b(20\d{2})[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])\b"),
    re.compile(r"\b(0?[1-9]|[12]\d|3[01])[-/](0?[1-9]|1[0-2])[-/](20\d{2})\b"),
    re.compile(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),?\s+(20\d{2})\b", re.I),
    re.compile(r"\b(0?[1-9]|[12]\d|3[01])[-/](0?[1-9]|1[0-2])[-/](\d{2})\b"),
    re.compile(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b"),
]
MONEY = re.compile(r"\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+(?:\.\d{2})?)\s*\$?")
TOTAL_LABELS = re.compile(
    r"(?:total|amount\s+due|balance\s+due|grand\s+total|subtotal|sum)\s*:?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+(?:\.\d{2})?)",
    re.I,
)
GST_PATTERN = re.compile(r"G\.?S\.?T\.?\s*(?:#?\s*\d*)?\s*:?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+(?:\.\d{2})?)", re.I)
GST_INCLUDED_PATTERN = re.compile(r"GST\s+INCLUDED\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+(?:\.\d{2})?)", re.I)
PST_PATTERN = re.compile(r"P\.?S\.?T\.?\s*(?:#?\s*\d*)?\s*:?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+(?:\.\d{2})?)", re.I)
HST_PATTERN = re.compile(r"HST\s*(?:#?\s*\d*)?\s*:?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+(?:\.\d{2})?)", re.I)


def _parse_amount(s: str) -> Optional[float]:
    s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def _extract_date(text: str) -> Optional[datetime]:
    for pat in DATE_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        g = m.groups()
        try:
            if len(g) == 3 and g[0].isdigit() and int(g[0]) > 1900:
                y, mo, d = int(g[0]), int(g[1]), int(g[2])
                if mo > 12:
                    mo = mo % 10 if mo % 10 in range(1, 13) else (mo // 10 if mo // 10 in range(1, 13) else 1)
                if d > 31:
                    d = min(31, d % 10 if d % 10 else d // 10)
                return datetime(y, mo, d)
            if len(g) == 3 and g[2].isdigit():
                y = int(g[2])
                if y < 100:
                    y += 2000 if y < 50 else 1900
                return datetime(y, int(g[1]), int(g[0]))
            if len(g) == 3 and not g[0].isdigit():
                months = "jan feb mar apr may jun jul aug sep oct nov dec".split()
                mo = months.index(g[0].lower()[:3]) + 1
                return datetime(int(g[2]), mo, int(g[1]))
        except (ValueError, IndexError):
            continue
    return None


def _extract_total(text: str) -> Optional[float]:
    candidates = []
    for m in TOTAL_LABELS.finditer(text):
        label = m.group(0).lower()
        if "subtotal" in label:
            continue
        amt = _parse_amount(m.group(1))
        if amt is not None and amt > 0:
            candidates.append(amt)
    if candidates:
        return candidates[-1]
    amounts = MONEY.findall(text)
    if amounts:
        parsed = [_parse_amount(a) for a in amounts if _parse_amount(a)]
        if parsed:
            return max(parsed)
    return None


def _extract_tax(text: str, pattern: re.Pattern, max_reasonable: Optional[float] = 100.0) -> Optional[float]:
    m = pattern.search(text)
    if m:
        amt = _parse_amount(m.group(1))
        if amt is not None and (max_reasonable is None or amt <= max_reasonable):
            return amt
    return None


def _extract_vendor(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for i, line in enumerate(lines[:8]):
        if len(line) > 3 and len(line) < 80:
            if not re.match(r"^\d", line) and not re.match(r"^(total|subtotal|date|gst|pst|hst)", line, re.I):
                raw = line
                if "CANADA" in raw.upper() and ("Po" in raw or "tage" in raw or "PETRO" in raw.upper() or "PETR" in raw.upper()):
                    return "PETRO-CANADA"
                if "PETRO" in raw.upper() and "CANADA" in raw.upper():
                    return "PETRO-CANADA"
                return raw
    return "Unknown"


def extract_receipt_data(image_bytes: bytes, mime_type: str) -> dict:
    """
    Run OCR and parse text into structured fields.
    Returns dict with keys: date, amount, amount_subtotal, tax_gst, tax_pst, vendor.
    Values may be None if not detected.
    """
    text = _image_to_text(image_bytes, mime_type)
    if not text.strip():
        return {
            "date": None,
            "amount": None,
            "amount_subtotal": None,
            "tax_gst": None,
            "tax_pst": None,
            "vendor": "Unknown",
        }
    total = _extract_total(text)
    gst = _extract_tax(text, GST_PATTERN)
    if gst is None:
        gst = _extract_tax(text, GST_INCLUDED_PATTERN)
    pst = _extract_tax(text, PST_PATTERN, max_reasonable=100.0)
    hst = _extract_tax(text, HST_PATTERN)
    # Sanity: tax must not exceed total; if it does, treat as OCR error and drop it
    if total is not None:
        if gst is not None and gst > total:
            gst = None
        if pst is not None and pst > total:
            pst = None
        if hst is not None and hst > total:
            hst = None
    subtotal = None
    if total is not None and (gst is not None or pst is not None or hst is not None):
        tax_sum = (gst or 0) + (pst or 0) + (hst or 0)
        subtotal = round(total - tax_sum, 2) if total >= tax_sum else total
    elif total is not None:
        subtotal = total
    date_val = _extract_date(text)
    return {
        "date": date_val,
        "amount": total,
        "amount_subtotal": subtotal,
        "tax_gst": gst if gst is not None else (hst if hst is not None else None),
        "tax_pst": pst,
        "vendor": _extract_vendor(text),
    }
