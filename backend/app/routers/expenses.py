from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.accounts_helpers import user_can_access_account
from app.db import get_db
from app.models import Account, Expense, Receipt
from app.receipt_storage import receipt_stored_path
from app.routers.auth import get_current_user
from app.schemas import ExpenseCreate, ExpenseResponse, ExpenseUpdate, ReceiptResponse, ExtractResponse
from app.models import User

router = APIRouter(prefix="/expenses", tags=["expenses"])

ALLOWED_MIME = {"image/jpeg", "image/png", "image/gif", "image/webp", "application/pdf"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post("/extract", response_model=ExtractResponse)
async def extract_receipt(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    from app.ocr import extract_receipt_data
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_MIME:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type not allowed")
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 20MB)")
    data = extract_receipt_data(content, content_type)
    return ExtractResponse(**data)


@router.post("/from-receipt", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense_from_receipt(
    file: UploadFile = File(...),
    account_id: int = Form(...),
    category: Optional[str] = Form(None),
    vendor: Optional[str] = Form(None),
    date: Optional[str] = Form(None),
    amount: Optional[float] = Form(None),
    amount_subtotal: Optional[float] = Form(None),
    tax_gst: Optional[float] = Form(None),
    tax_pst: Optional[float] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.accounts_helpers import get_allowed_account_ids
    from app.ocr import extract_receipt_data
    if not user_can_access_account(db, current_user.id, account_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_MIME:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type not allowed")
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 20MB)")
    data = extract_receipt_data(content, content_type)
    from datetime import datetime as dt
    def _opt(s):
        return (s or "").strip() or None
    def _opt_float(v):
        if v is None: return None
        try: return float(v)
        except (TypeError, ValueError): return None
    vendor_val = _opt(vendor)
    date_val = _opt(date)
    amount_val = _opt_float(amount) if amount is not None else data["amount"]
    amount_subtotal_val = _opt_float(amount_subtotal) if amount_subtotal is not None else data["amount_subtotal"]
    tax_gst_val = _opt_float(tax_gst) if tax_gst is not None else data["tax_gst"]
    tax_pst_val = _opt_float(tax_pst) if tax_pst is not None else data["tax_pst"]
    expense_date = dt.utcnow()
    if date_val:
        try:
            expense_date = dt.fromisoformat(date_val.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass
    elif data["date"]:
        expense_date = data["date"]
    expense = Expense(
        account_id=account_id,
        amount=float(amount_val or 0.0),
        amount_subtotal=amount_subtotal_val,
        tax_gst=tax_gst_val,
        tax_pst=tax_pst_val,
        currency="CAD",
        date=expense_date,
        vendor=(vendor_val or data["vendor"] or "Unknown").strip() or "Unknown",
        category=category or data.get("category"),
        notes=None,
        created_by_user_id=current_user.id,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    existing_count = 0
    full_path, stored_relative = receipt_stored_path(expense, account, existing_count, file.filename or "file")
    full_path.write_bytes(content)
    receipt = Receipt(
        expense_id=expense.id,
        original_filename=file.filename or "file",
        stored_path=stored_relative,
        mime_type=content_type,
    )
    db.add(receipt)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("", response_model=List[ExpenseResponse])
def list_expenses(
    account_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.accounts_helpers import get_allowed_account_ids
    allowed = get_allowed_account_ids(db, current_user.id)
    if not allowed:
        return []
    q = db.query(Expense).filter(Expense.account_id.in_(allowed))
    if account_id is not None:
        if account_id not in allowed:
            return []
        q = q.filter(Expense.account_id == account_id)
    q = q.order_by(Expense.date.desc(), Expense.id.desc())
    return q.all()


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    data: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user_can_access_account(db, current_user.id, data.account_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    account = db.query(Account).filter(Account.id == data.account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    expense = Expense(
        account_id=data.account_id,
        amount=data.amount,
        amount_subtotal=data.amount_subtotal,
        tax_gst=data.tax_gst,
        tax_pst=data.tax_pst,
        currency=data.currency or "CAD",
        date=data.date,
        vendor=data.vendor,
        category=data.category,
        notes=data.notes,
        created_by_user_id=current_user.id,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.accounts_helpers import get_allowed_account_ids
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    allowed = get_allowed_account_ids(db, current_user.id)
    if expense.account_id not in allowed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return expense


@router.patch("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.accounts_helpers import get_allowed_account_ids
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    allowed = get_allowed_account_ids(db, current_user.id)
    if expense.account_id not in allowed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    if data.amount is not None:
        expense.amount = data.amount
    if data.amount_subtotal is not None:
        expense.amount_subtotal = data.amount_subtotal
    if data.tax_gst is not None:
        expense.tax_gst = data.tax_gst
    if data.tax_pst is not None:
        expense.tax_pst = data.tax_pst
    if data.date is not None:
        expense.date = data.date
    if data.vendor is not None:
        expense.vendor = data.vendor
    if data.category is not None:
        expense.category = data.category
    if data.notes is not None:
        expense.notes = data.notes
    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.accounts_helpers import get_allowed_account_ids
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    allowed = get_allowed_account_ids(db, current_user.id)
    if expense.account_id not in allowed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    db.delete(expense)
    db.commit()
    return None


@router.get("/{expense_id}/receipts", response_model=List[ReceiptResponse])
def list_receipts(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.accounts_helpers import get_allowed_account_ids
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    allowed = get_allowed_account_ids(db, current_user.id)
    if expense.account_id not in allowed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    receipts = db.query(Receipt).filter(Receipt.expense_id == expense_id).order_by(Receipt.created_at).all()
    return receipts


@router.post("/{expense_id}/receipts", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED)
async def upload_receipt(
    expense_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.accounts_helpers import get_allowed_account_ids
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    allowed = get_allowed_account_ids(db, current_user.id)
    if expense.account_id not in allowed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    account = db.query(Account).filter(Account.id == expense.account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_MIME)}",
        )
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 20MB)")
    existing_count = db.query(Receipt).filter(Receipt.expense_id == expense_id).count()
    full_path, stored_relative = receipt_stored_path(expense, account, existing_count, file.filename or "file")
    full_path.write_bytes(content)
    receipt = Receipt(
        expense_id=expense_id,
        original_filename=file.filename or "file",
        stored_path=stored_relative,
        mime_type=content_type,
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt
