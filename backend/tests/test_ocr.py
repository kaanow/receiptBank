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
