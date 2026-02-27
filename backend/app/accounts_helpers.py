from typing import Set

from sqlalchemy.orm import Session

from app.models import Account, AccountAccess, User


def get_allowed_account_ids(db: Session, user_id: int) -> Set[int]:
    """Account IDs the user owns or has been granted access to."""
    owned = db.query(Account.id).filter(Account.owner_user_id == user_id).all()
    shared = db.query(AccountAccess.account_id).filter(AccountAccess.user_id == user_id).all()
    return {r[0] for r in owned} | {r[0] for r in shared}


def user_can_access_account(db: Session, user_id: int, account_id: int) -> bool:
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return False
    if account.owner_user_id == user_id:
        return True
    return db.query(AccountAccess).filter(
        AccountAccess.user_id == user_id,
        AccountAccess.account_id == account_id,
    ).first() is not None


def user_owns_account(db: Session, user_id: int, account_id: int) -> bool:
    account = db.query(Account).filter(Account.id == account_id).first()
    return account is not None and account.owner_user_id == user_id
