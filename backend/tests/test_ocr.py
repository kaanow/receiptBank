from app.ocr import extract_receipt_data


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
