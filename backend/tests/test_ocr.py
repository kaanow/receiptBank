from app.ocr import extract_receipt_data, _image_to_text, HAS_HEIF, _is_heic_bytes, _crop_receipt_to_rect, HAS_RECEIPT_CROP


def test_extract_vendor_petro_canada_fix():
    text = "tage Po- CANADA\n123 Main St\nTotal $77.17"
    from app import ocr
    old_fn = ocr._image_to_text
    try:
        ocr._image_to_text = lambda b, m: text
        data = extract_receipt_data(b"fake", "image/jpeg")
        assert data["vendor"] == "PETRO-CANADA"
    finally:
        ocr._image_to_text = old_fn


def test_extract_pst_sanity_over_total():
    text = "Store\nTotal $77.17\nGST $3.67\nPST $147.00"
    from app import ocr
    old_fn = ocr._image_to_text
    try:
        ocr._image_to_text = lambda b, m: text
        data = extract_receipt_data(b"fake", "image/jpeg")
        assert data["amount"] == 77.17
        assert data["tax_pst"] is None
        assert data["tax_gst"] == 3.67
    finally:
        ocr._image_to_text = old_fn


def test_extract_bc_ferries_balance():
    """BC Ferries: vendor recognized; avoid using address numbers or prepaid card balance as expense total."""
    text = """bes ene Bay
atte orri
ite 506 - 1321 Blanshard Street
PURCHASE 2026/02/19
Total .45
Balance:$98.1
19 Feb 2026 17:59:59"""
    from app import ocr
    old_fn = ocr._image_to_text
    try:
        ocr._image_to_text = lambda b, m: text
        data = extract_receipt_data(b"fake", "image/jpeg")
        assert data["vendor"] == "BC Ferries"
        assert data["date"] is not None and str(data["date"])[:10] == "2026-02-19"
        assert data["amount"] is None
    finally:
        ocr._image_to_text = old_fn


def test_extract_petro_canada_full():
    """Petro-Canada receipt: date 2026-61-23 -> 2026-01-23, GST INCLUDED, PST reg # rejected."""
    text = """tage Po- CANADA
> HWY 4 WEST
GST #- 8863696026
PST 4: 14792877
2026-61-23 16:67:41
Fuel sales $ 77.17
GST INCLUDED $3.67
TOTAL $77.17"""
    from app import ocr
    old_fn = ocr._image_to_text
    try:
        ocr._image_to_text = lambda b, m: text
        data = extract_receipt_data(b"fake", "image/jpeg")
        assert data["vendor"] == "PETRO-CANADA"
        assert data["date"] is not None and str(data["date"])[:10] == "2026-01-23"
        assert data["amount"] == 77.17
        assert data["tax_gst"] == 3.67
        assert data["tax_pst"] is None
    finally:
        ocr._image_to_text = old_fn


def test_extract_bc_ferries_langdale():
    """BC Ferries Langdale/Horseshoe Bay: vendor BC Ferries, Total Prepaid 20.00."""
    text = """Langdale
Horseshoe Bay
vite 566 L321] Blanshard Street
Victoria er Canada VBW OR7
RECEIPT - PLEASE RETAIN
PURCHASE 2026/01/01
1 Reservation fee 20.00
Total Prepaid 20.00
Total Changes > 0.00
01 Jan 2026 08:27:49"""
    from app import ocr
    old_fn = ocr._image_to_text
    try:
        ocr._image_to_text = lambda b, m: text
        data = extract_receipt_data(b"fake", "image/jpeg")
        assert data["vendor"] == "BC Ferries"
        assert data["date"] is not None and str(data["date"])[:10] == "2026-01-01"
        assert data["amount"] == 20.0
    finally:
        ocr._image_to_text = old_fn


def test_heic_decode_when_available():
    """If HAS_HEIF and a HEIC file exists in test_receipts, decode returns non-empty or no exception."""
    import pytest
    from pathlib import Path
    heic_dir = Path(__file__).resolve().parent.parent.parent / "test_receipts"
    heic_paths = list(heic_dir.glob("*.heic")) + list(heic_dir.glob("*.HEIC"))
    if not heic_paths or not HAS_HEIF:
        pytest.skip("No HEIC file in test_receipts or pillow-heif/libheif not available")
    path = heic_paths[0]
    content = path.read_bytes()
    text = _image_to_text(content, "image/heic")
    # Should not crash; may return empty if tesseract fails on content, but decode should work
    assert isinstance(text, str)


def test_heic_magic_bytes_detection():
    """_is_heic_bytes detects HEIC by ftyp box and brand."""
    assert _is_heic_bytes(b"\x00\x00\x00\x20ftypheic\x00\x00\x00\x00") is True
    assert _is_heic_bytes(b"\x00\x00\x00\x20ftypmif1\x00\x00\x00\x00") is True
    assert _is_heic_bytes(b"xxxxftypheic") is True
    assert _is_heic_bytes(b"\x00\x00\x00\x0cftypiso5") is False
    assert _is_heic_bytes(b"too short") is False
    assert _is_heic_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF") is False


def test_crop_receipt_to_rect_no_crash():
    """_crop_receipt_to_rect accepts a PIL Image and returns None or a PIL Image."""
    from PIL import Image
    img = Image.new("RGB", (100, 100), color=(240, 240, 240))
    result = _crop_receipt_to_rect(img)
    if HAS_RECEIPT_CROP:
        assert result is None or isinstance(result, Image.Image)
    else:
        assert result is None


def test_receipt_expected_vs_saved_ocr():
    """When test_receipts/ocr/<stem>.txt exists and expected.json has expectations, parser output must match."""
    import json
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent.parent
    expected_path = repo_root / "test_receipts" / "expected.json"
    ocr_dir = repo_root / "test_receipts" / "ocr"
    if not expected_path.exists() or not ocr_dir.exists():
        import pytest
        pytest.skip("test_receipts/expected.json or test_receipts/ocr/ not present")

    with open(expected_path) as f:
        expected = json.load(f)

    from app import ocr
    old_fn = ocr._image_to_text

    failures = []
    for filename, exp in expected.items():
        if filename.startswith("_") or exp is None:
            continue
        stem = Path(filename).stem
        txt_path = ocr_dir / f"{stem}.txt"
        if not txt_path.is_file():
            continue
        text = txt_path.read_text(encoding="utf-8")
        try:
            ocr._image_to_text = lambda b, m, t=text: t
            data = extract_receipt_data(b"fake", "image/jpeg")
        finally:
            ocr._image_to_text = old_fn

        got_date = data["date"].isoformat()[:10] if data.get("date") else None
        if exp.get("vendor") is not None and data.get("vendor") != exp["vendor"]:
            failures.append(f"{filename}: vendor got {data.get('vendor')} expected {exp['vendor']}")
        if exp.get("date") is not None and got_date != exp["date"]:
            failures.append(f"{filename}: date got {got_date} expected {exp['date']}")
        if exp.get("amount") is not None and data.get("amount") != exp["amount"]:
            failures.append(f"{filename}: amount got {data.get('amount')} expected {exp['amount']}")
        for key in ("tax_gst", "tax_pst", "amount_subtotal"):
            if exp.get(key) is not None and data.get(key) != exp.get(key):
                failures.append(f"{filename}: {key} got {data.get(key)} expected {exp.get(key)}")

    if failures:
        raise AssertionError("Expected vs saved OCR mismatches:\n" + "\n".join(failures))
