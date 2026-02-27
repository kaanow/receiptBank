from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    accounts_owned: Mapped[list["Account"]] = relationship("Account", back_populates="owner", foreign_keys="Account.owner_user_id")
    account_access: Mapped[list["AccountAccess"]] = relationship("AccountAccess", back_populates="user", foreign_keys="AccountAccess.user_id")
    expenses_created: Mapped[list["Expense"]] = relationship("Expense", back_populates="created_by_user", foreign_keys="Expense.created_by_user_id")


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    friendly_name: Mapped[str] = mapped_column(String(128), nullable=False)  # short name for filenames
    type: Mapped[str] = mapped_column(String(32), nullable=False)  # rental, employment, personal
    metadata_: Mapped[Optional[str]] = mapped_column("metadata", Text, nullable=True)  # e.g. property address
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    owner: Mapped["User"] = relationship("User", back_populates="accounts_owned", foreign_keys=[owner_user_id])
    access_grants: Mapped[list["AccountAccess"]] = relationship("AccountAccess", back_populates="account", cascade="all, delete-orphan")
    expenses: Mapped[list["Expense"]] = relationship("Expense", back_populates="account", cascade="all, delete-orphan")


class AccountAccess(Base):
    __tablename__ = "account_access"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True)
    granted_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="account_access", foreign_keys=[user_id])
    account: Mapped["Account"] = relationship("Account", back_populates="access_grants")
    granted_by: Mapped["User"] = relationship("User", foreign_keys=[granted_by_user_id])


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)  # total CAD
    amount_subtotal: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    tax_gst: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    tax_pst: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CAD")
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    vendor: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)  # BC rental category when account type is rental
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    account: Mapped["Account"] = relationship("Account", back_populates="expenses")
    created_by_user: Mapped[Optional["User"]] = relationship("User", back_populates="expenses_created", foreign_keys=[created_by_user_id])
    receipts: Mapped[list["Receipt"]] = relationship("Receipt", back_populates="expense", cascade="all, delete-orphan")


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    expense: Mapped["Expense"] = relationship("Expense", back_populates="receipts")
