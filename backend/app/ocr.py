"""
Extract structured data from receipt image/PDF text using regex and heuristics.
Uses pytesseract for OCR; callers pass in raw image bytes or PDF bytes.
HEIC: requires pillow-heif; on Linux, libheif libraries may be needed for decode.
"""
import io
import re
from datetime import datetime
from typing import Optional, Tuple

try:
    import pytesseract
    from PIL import Image, ImageFilter
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

try:
    import cv2
    import numpy as np
    HAS_RECEIPT_CROP = True
except ImportError:
    HAS_RECEIPT_CROP = False


def _is_heic_bytes(content: bytes) -> bool:
    """Detect HEIC/HEIF by ISO base media ftyp box (bytes 4-7 'ftyp', 8-11 brand 'heic' or 'mif1')."""
    if len(content) < 12:
        return False
    return content[4:8] == b"ftyp" and content[8:12] in (b"heic", b"mif1", b"heix", b"hevx", b"msf1")


def heic_to_png_bytes(image_bytes: bytes) -> Optional[bytes]:
    """Convert HEIC to PNG bytes. Use this once at ingestion; use PNG for OCR, preview, and storage. Returns None if not HEIC or decode fails."""
    if not HAS_HEIF or not _is_heic_bytes(image_bytes):
        return None
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode not in ("L", "RGB"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None


def heic_to_png_data_url(image_bytes: bytes) -> Optional[str]:
    """Return a data URL for PNG preview of HEIC. None if not HEIC or decode fails. Prefer heic_to_png_bytes + png_to_data_url when you already have PNG bytes."""
    import base64
    png = heic_to_png_bytes(image_bytes)
    return png_to_data_url(png) if png else None


def png_to_data_url(png_bytes: bytes) -> str:
    """Build a data URL for PNG bytes (for preview in HTML)."""
    import base64
    return "data:image/png;base64," + base64.standard_b64encode(png_bytes).decode("ascii")


def _order_quad_points(pts: "np.ndarray") -> "np.ndarray":
    """Order 4 points as [top-left, top-right, bottom-right, bottom-left] for perspective transform."""
    pts = np.array(pts, dtype=np.float32).reshape(4, 2)
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    top_left = pts[np.argmin(s)]
    bottom_right = pts[np.argmax(s)]
    top_right = pts[np.argmin(diff)]
    bottom_left = pts[np.argmax(diff)]
    return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)


def _crop_receipt_to_rect(pil_image: Image.Image) -> Optional[Image.Image]:
    """
    Detect a roughly rectangular receipt in the image (central document assumption),
    apply perspective transform to get a top-down rectangle, return the cropped image.
    Returns None if no suitable contour found (e.g. already flat receipt or no clear edges).
    """
    if not HAS_RECEIPT_CROP:
        return None
    try:
        img_arr = np.array(pil_image)
        if img_arr.ndim == 2:
            gray = img_arr
        else:
            gray = cv2.cvtColor(img_arr, cv2.COLOR_RGB2GRAY)
        h, w = gray.shape
        if h < 50 or w < 50:
            return None
        blurred = cv2.GaussianBlur(gray, (5, 5), 1)
        edged = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        area_thresh = (w * h) * 0.005  # at least 0.5% of image (was 3%; relaxed for full-frame receipts)
        best_quad = None
        best_area = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < area_thresh:
                continue
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
            if len(approx) != 4:
                continue
            rect_area = cv2.contourArea(approx)
            if rect_area < best_area:
                continue
            x, y, rw, rh = cv2.boundingRect(approx)
            aspect = max(rw, rh) / (min(rw, rh) + 1e-6)
            if aspect > 8 or aspect < 0.15:  # receipt-like aspect
                continue
            cx = x + rw / 2
            cy = y + rh / 2
            if cx < w * 0.1 or cx > w * 0.9 or cy < h * 0.1 or cy > h * 0.9:
                continue
            best_quad = approx
            best_area = rect_area
        if best_quad is None:
            # No document contour found (common when receipt fills the frame). Fallback: margin crop
            # to remove border noise and slightly normalize; helps OCR on full-frame receipts.
            aspect = w / (h + 1e-6)
            if 0.15 <= aspect <= 6.0 and w >= 100 and h >= 100:
                margin_pct = 0.02
                x1 = int(w * margin_pct)
                y1 = int(h * margin_pct)
                x2 = int(w * (1 - margin_pct))
                y2 = int(h * (1 - margin_pct))
                if x2 > x1 and y2 > y1:
                    cropped = img_arr[y1:y2, x1:x2]
                    return Image.fromarray(cropped)
            return None
        src_pts = _order_quad_points(best_quad)
        tw = max(
            np.linalg.norm(src_pts[1] - src_pts[0]),
            np.linalg.norm(src_pts[2] - src_pts[3]),
        )
        th = max(
            np.linalg.norm(src_pts[3] - src_pts[0]),
            np.linalg.norm(src_pts[2] - src_pts[1]),
        )
        tw, th = int(round(tw)), int(round(th))
        if tw < 20 or th < 20:
            return None
        dst_pts = np.array(
            [[0, 0], [tw - 1, 0], [tw - 1, th - 1], [0, th - 1]],
            dtype=np.float32,
        )
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped = cv2.warpPerspective(
            img_arr, M, (tw, th),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )
        if warped.ndim == 2:
            out = Image.fromarray(warped)
        else:
            out = Image.fromarray(warped)
        return out
    except Exception:
        return None


def _preprocess_for_ocr(img: "Image.Image") -> "Image.Image":
    """Resize up if small, convert to grayscale, sharpen. Improves tesseract accuracy."""
    w, h = img.size
    min_dim = min(w, h)
    # Tesseract prefers ~300 DPI; upscale if small (e.g. phone photo downscaled)
    if min_dim < 1200:
        scale = 2400 / min_dim
        new_w = max(400, int(w * scale))
        new_h = max(400, int(h * scale))
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    if img.mode != "L":
        img = img.convert("L")
    img = img.filter(ImageFilter.SHARPEN)
    return img


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
                prepped = _preprocess_for_ocr(img)
                text_parts.append(pytesseract.image_to_string(prepped))
            return "\n".join(text_parts)
        if mime_type == "image/heic" and not HAS_HEIF:
            return ""
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode not in ("L", "RGB"):
            img = img.convert("RGB")
        # Pytesseract only supports PNG, JPEG, etc.; HEIC opener yields HeifImageFile with unsupported format
        if getattr(img, "format", None) and str(img.format).upper() not in ("PNG", "JPEG", "JPG", "GIF", "BMP", "TIFF", "PBM"):
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            img = Image.open(buf)
        cropped = _crop_receipt_to_rect(img)
        # Multiple passes: preprocessed full, preprocessed crop (if different), preprocessed bottom region (totals often there)
        texts = []
        prepped_full = _preprocess_for_ocr(img)
        texts.append(pytesseract.image_to_string(prepped_full))
        if cropped is not None and cropped.size != img.size:
            prepped_crop = _preprocess_for_ocr(cropped)
            texts.append(pytesseract.image_to_string(prepped_crop))
        w, h = img.size
        if h > 200:
            bottom = img.crop((0, int(h * 0.55), w, h))
            prepped_bottom = _preprocess_for_ocr(bottom)
            texts.append(pytesseract.image_to_string(prepped_bottom))
        combined = "\n".join(t.strip() for t in texts if t.strip())
        return combined
    except Exception as e:
        if mime_type == "image/heic":
            # Only surface as HEIC decode failure if the error is from open/save, not from tesseract
            from pytesseract import TesseractNotFoundError
            if not isinstance(e, TesseractNotFoundError) and "tesseract" not in str(e).lower():
                raise RuntimeError(f"HEIC decode failed: {e}") from e
        return ""


# Regex patterns for Canadian receipts (GST, PST common)
DATE_PATTERNS = [
    re.compile(r"\b(20\d{2})[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])\b"),
    re.compile(r"\b(0?[1-9]|[12]\d|3[01])[-/](0?[1-9]|1[0-2])[-/](20\d{2})\b"),
    re.compile(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),?\s+(20\d{2})\b", re.I),
    re.compile(r"\b(0?[1-9]|[12]\d|3[01])[-/](0?[1-9]|1[0-2])[-/](\d{2})\b"),
    re.compile(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b"),
]
MONEY_DECIMAL = re.compile(r"\$?\s*(\d{1,3}(?:,\d{3})*\.\d{2}|\d+\.\d{2})\b")
MONEY_DOLLAR_INT = re.compile(r"\$\s*(\d{1,3}(?:,\d{3})*|\d+)\b")
TOTAL_LABELS = re.compile(
    r"(?:total|amount\s+due|balance\s+due|grand\s+total|subtotal|sum)\s*:?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+(?:\.\d{2})?)",
    re.I,
)
# Total Prepaid / Reservation fee (BC Ferries etc.)
TOTAL_PREPAID_PATTERN = re.compile(
    r"(?:total\s+prepaid|reservation\s+fee)\s*:?\s*\$?\s*(\d{1,3}(?:,\d{3})*\.\d{2}|\d+\.\d{2})",
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
    # Remove balance/prepaid-card lines so we don't treat remaining balance as the expense total.
    filtered_lines = []
    for ln in text.splitlines():
        if re.search(r"\bbalance\b", ln, re.I):
            continue
        filtered_lines.append(ln)
    filtered_text = "\n".join(filtered_lines)

    candidates = []
    for m in TOTAL_LABELS.finditer(filtered_text):
        label = m.group(0).lower()
        if "subtotal" in label or "balance" in label:
            continue
        amt = _parse_amount(m.group(1))
        if amt is not None and amt > 0:
            candidates.append(amt)
    for m in TOTAL_PREPAID_PATTERN.finditer(filtered_text):
        amt = _parse_amount(m.group(1))
        if amt is not None and amt > 0:
            candidates.append(amt)
    if candidates:
        preferred = [a for a in candidates if a < 1000]
        return (preferred[-1] if preferred else candidates[-1])
    amounts = MONEY_DECIMAL.findall(filtered_text)
    parsed = [_parse_amount(a) for a in amounts if _parse_amount(a)]
    if parsed:
        under_1k = [a for a in parsed if 0 < a < 1000]
        return max(under_1k) if under_1k else max(parsed)
    amounts_int = MONEY_DOLLAR_INT.findall(filtered_text)
    parsed_int = [_parse_amount(a) for a in amounts_int if _parse_amount(a)]
    if parsed_int:
        under_1k = [a for a in parsed_int if 0 < a < 1000]
        return max(under_1k) if under_1k else max(parsed_int)
    return None


def _extract_tax(text: str, pattern: re.Pattern, max_reasonable: Optional[float] = 100.0) -> Optional[float]:
    m = pattern.search(text)
    if m:
        amt = _parse_amount(m.group(1))
        if amt is not None and (max_reasonable is None or amt <= max_reasonable):
            return amt
    return None


def _extract_vendor(text: str) -> str:
    text_lower = text.lower()
    if "ferries" in text_lower or "bcf " in text_lower or "ene bay" in text_lower or "bc ferries" in text_lower:
        return "BC Ferries"
    if "langdale" in text_lower and ("horseshoe" in text_lower or "bay" in text_lower):
        return "BC Ferries"
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
