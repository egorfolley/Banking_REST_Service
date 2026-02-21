from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_account_for_user, get_current_user, get_db
from app.models.account import Account
from app.models.enums import TransactionType
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import (
    DepositRequest,
    TransactionListResponse,
    TransactionResponse,
    WithdrawRequest,
)
from app.services.audit_service import log_action
from app.services.transaction_service import apply_deposit, apply_withdrawal

router = APIRouter()


@router.post("/{account_id}/deposit", response_model=TransactionResponse)
def deposit(
    account_id: str,
    payload: DepositRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = get_account_for_user(account_id, current_user, db)
    tx = apply_deposit(db, account, payload.amount_cents, payload.description)
    db.flush()
    log_action(
        db,
        user_id=current_user.id,
        action="deposit",
        resource_type="transaction",
        resource_id=tx.id,
        details=f"account_id={account.id}",
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(tx)
    return tx


@router.post("/{account_id}/withdraw", response_model=TransactionResponse)
def withdraw(
    account_id: str,
    payload: WithdrawRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = get_account_for_user(account_id, current_user, db)
    tx = apply_withdrawal(db, account, payload.amount_cents, payload.description)
    db.flush()
    log_action(
        db,
        user_id=current_user.id,
        action="withdraw",
        resource_type="transaction",
        resource_id=tx.id,
        details=f"account_id={account.id}",
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(tx)
    return tx


@router.get("/{account_id}", response_model=TransactionListResponse)
def list_transactions(
    account_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    transaction_type: TransactionType | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = get_account_for_user(account_id, current_user, db)
    stmt = select(Transaction).where(Transaction.account_id == account.id)
    if transaction_type:
        stmt = stmt.where(Transaction.transaction_type == transaction_type)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = (
        db.scalars(
            stmt.order_by(Transaction.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .all()
    )
    return TransactionListResponse(items=items, page=page, page_size=page_size, total=total)
