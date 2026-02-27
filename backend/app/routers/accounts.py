from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.accounts_helpers import (
    get_allowed_account_ids,
    user_can_access_account,
    user_owns_account,
)
from app.db import get_db
from app.models import Account, AccountAccess, User
from app.routers.auth import get_current_user
from app.schemas import AccountCreate, AccountResponse, AccountUpdate, ShareRequest

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=List[AccountResponse])
def list_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed = get_allowed_account_ids(db, current_user.id)
    if not allowed:
        return []
    accounts = db.query(Account).filter(Account.id.in_(allowed)).order_by(Account.name).all()
    return accounts


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    data: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = Account(
        owner_user_id=current_user.id,
        name=data.name,
        friendly_name=data.friendly_name,
        type=data.type,
        metadata_=data.metadata,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user_can_access_account(db, current_user.id, account_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


@router.patch("/{account_id}", response_model=AccountResponse)
def update_account(
  account_id: int,
  data: AccountUpdate,
  current_user: User = Depends(get_current_user),
  db: Session = Depends(get_db),
):
    if not user_owns_account(db, current_user.id, account_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    if data.name is not None:
        account.name = data.name
    if data.friendly_name is not None:
        account.friendly_name = data.friendly_name
    if data.type is not None:
        account.type = data.type
    if data.metadata is not None:
        account.metadata_ = data.metadata
    db.commit()
    db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
  account_id: int,
  current_user: User = Depends(get_current_user),
  db: Session = Depends(get_db),
):
    if not user_owns_account(db, current_user.id, account_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    db.delete(account)
    db.commit()
    return None


@router.post("/{account_id}/share", status_code=status.HTTP_204_NO_CONTENT)
def share_account(
  account_id: int,
  data: ShareRequest,
  current_user: User = Depends(get_current_user),
  db: Session = Depends(get_db),
):
    if not user_owns_account(db, current_user.id, account_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    other = db.query(User).filter(User.email == data.email).first()
    if not other:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if other.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot share with yourself")
    existing = db.query(AccountAccess).filter(
        AccountAccess.user_id == other.id,
        AccountAccess.account_id == account_id,
    ).first()
    if existing:
        return None
    grant = AccountAccess(
        user_id=other.id,
        account_id=account_id,
        granted_by_user_id=current_user.id,
    )
    db.add(grant)
    db.commit()
    return None


@router.delete("/{account_id}/share/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_access(
  account_id: int,
  user_id: int,
  current_user: User = Depends(get_current_user),
  db: Session = Depends(get_db),
):
    if not user_owns_account(db, current_user.id, account_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    grant = db.query(AccountAccess).filter(
        AccountAccess.account_id == account_id,
        AccountAccess.user_id == user_id,
    ).first()
    if grant:
        db.delete(grant)
        db.commit()
    return None
