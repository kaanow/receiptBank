import csv
import io
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from zipfile import ZipFile, ZIP_DEFLATED

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.accounts_helpers import get_allowed_account_ids
from app.config import settings
from app.db import get_db
from app.models import Account, Expense, Receipt
from app.routers.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/reports", tags=["reports"])


def _expenses_for_report(
    db: Session,
    user_id: int,
    from_date: date,
    to_date: date,
    account_id: Optional[int] = None,
    account_type: Optional[str] = None,
) -> List[Expense]:
    allowed = get_allowed_account_ids(db, user_id)
    if not allowed:
        return []
    from_dt = datetime.combine(from_date, datetime.min.time())
    to_dt = datetime.combine(to_date, datetime.max.time())
    q = (
        db.query(Expense)
        .join(Account, Expense.account_id == Account.id)
        .filter(Expense.account_id.in_(allowed))
        .filter(Expense.date >= from_dt, Expense.date <= to_dt)
    )
    if account_id is not None:
        if account_id not in allowed:
            return []
        q = q.filter(Expense.account_id == account_id)
    if account_type is not None:
        q = q.filter(Account.type == account_type)
    return q.order_by(Expense.date, Expense.id).all()


def _receipt_full_path(stored_relative: str) -> Path:
    return Path(settings.file_storage_path) / stored_relative


@router.get("/tax")
def report_tax(
    from_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    to_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    account_id: Optional[int] = Query(None),
    include_receipts: bool = Query(False),
    taxes_separate: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rental income tax report: expenses grouped by category. Optional receipt ZIP and tax columns."""
    expenses = _expenses_for_report(db, current_user.id, from_date, to_date, account_id=account_id, account_type="rental")
    if taxes_separate:
        by_cat: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"amount": 0, "tax_gst": 0, "tax_pst": 0, "amount_subtotal": 0, "count": 0})
        for e in expenses:
            key = e.category or "Uncategorized"
            by_cat[key]["amount"] += float(e.amount)
            by_cat[key]["tax_gst"] += float(e.tax_gst or 0)
            by_cat[key]["tax_pst"] += float(e.tax_pst or 0)
            by_cat[key]["amount_subtotal"] += float(e.amount_subtotal or e.amount)
            by_cat[key]["count"] += 1
        summary = [{"category": k, **v} for k, v in sorted(by_cat.items())]
    else:
        by_cat = defaultdict(lambda: {"amount": 0, "count": 0})
        for e in expenses:
            key = e.category or "Uncategorized"
            by_cat[key]["amount"] += float(e.amount)
            by_cat[key]["count"] += 1
        summary = [{"category": k, **v} for k, v in sorted(by_cat.items())]
    result = {"from": from_date.isoformat(), "to": to_date.isoformat(), "by_category": summary}
    if include_receipts:
        buf = io.BytesIO()
        with ZipFile(buf, "w", ZIP_DEFLATED) as zf:
            for e in expenses:
                for r in e.receipts:
                    full = _receipt_full_path(r.stored_path)
                    if full.exists():
                        zf.write(full, r.stored_path)
        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=receipts.zip"},
        )
    result["expenses"] = [
        {"id": e.id, "date": e.date.isoformat() if hasattr(e.date, "isoformat") else str(e.date), "vendor": e.vendor, "amount": float(e.amount), "category": e.category}
        for e in expenses
    ]
    return result


@router.get("/monthly")
def report_monthly(
    from_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    to_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    account_id: Optional[int] = Query(None),
    include_receipts: bool = Query(False),
    taxes_separate: bool = Query(False),
    format: str = Query("json", pattern="^(json|csv)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Monthly expense report: list expenses. Optional receipt ZIP, tax columns, CSV export."""
    expenses = _expenses_for_report(db, current_user.id, from_date, to_date, account_id=account_id)
    rows = []
    for e in expenses:
        row = {
            "id": e.id,
            "date": e.date.isoformat() if hasattr(e.date, "isoformat") else str(e.date),
            "vendor": e.vendor,
            "amount": float(e.amount),
            "category": e.category,
            "account_id": e.account_id,
        }
        if taxes_separate:
            row["amount_subtotal"] = float(e.amount_subtotal or e.amount)
            row["tax_gst"] = float(e.tax_gst or 0)
            row["tax_pst"] = float(e.tax_pst or 0)
        rows.append(row)
    if include_receipts:
        buf = io.BytesIO()
        with ZipFile(buf, "w", ZIP_DEFLATED) as zf:
            for e in expenses:
                for r in e.receipts:
                    full = _receipt_full_path(r.stored_path)
                    if full.exists():
                        zf.write(full, r.stored_path)
        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=monthly-receipts.zip"},
        )
    if format == "csv":
        out = io.StringIO()
        if not rows:
            writer = csv.writer(out)
            writer.writerow(["date", "vendor", "amount", "category"] + (["subtotal", "gst", "pst"] if taxes_separate else []))
        else:
            keys = list(rows[0].keys())
            writer = csv.DictWriter(out, fieldnames=keys, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        return StreamingResponse(
            iter([out.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=monthly-expenses.csv"},
        )
    return {"from": from_date.isoformat(), "to": to_date.isoformat(), "expenses": rows}

