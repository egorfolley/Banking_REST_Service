from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_account_for_user, get_current_holder, get_current_user, get_db
from app.models.account import Account
from app.models.enums import AccountStatus, TransactionType
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.account import AccountCreate, AccountResponse, AccountStatusUpdate
from app.schemas.transaction import (
    DepositRequest,
    TransactionListResponse,
    TransactionResponse,
)
from app.services.account_service import create_account
from app.services.audit_service import log_action
from app.services.transaction_service import apply_deposit

router = APIRouter()


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account_endpoint(
    payload: AccountCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    holder=Depends(get_current_holder),
    db: Session = Depends(get_db),
):
    account = create_account(
        db,
        holder,
        account_type=payload.account_type,
        currency=payload.currency,
        initial_deposit_cents=payload.initial_deposit_cents,
    )
    log_action(
        db,
        user_id=current_user.id,
        action="create_account",
        resource_type="account",
        resource_id=account.id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(account)
    return account


@router.get("/", response_model=list[AccountResponse])
def list_accounts(
    holder=Depends(get_current_holder),
    db: Session = Depends(get_db),
):
    return db.scalars(select(Account).where(Account.holder_id == holder.id)).all()


@router.get("/all", response_model=list[AccountResponse])
def list_all_accounts(
    db: Session = Depends(get_db),
):
    """List all active accounts in the system (for transfer destinations)."""
    return db.scalars(select(Account).where(Account.status == AccountStatus.active)).all()


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_account_for_user(account_id, current_user, db)


@router.patch("/{account_id}/status", response_model=AccountResponse)
def update_account_status(
    account_id: str,
    payload: AccountStatusUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = get_account_for_user(account_id, current_user, db)
    if payload.status == AccountStatus.closed and account.balance_cents != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot close account with non-zero balance",
        )

    account.status = payload.status
    log_action(
        db,
        user_id=current_user.id,
        action="update_account_status",
        resource_type="account",
        resource_id=account.id,
        details=f"status={payload.status}",
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(account)
    return account


@router.post("/{account_id}/deposit", response_model=TransactionResponse)
def deposit_to_account(
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


@router.get("/{account_id}/transactions", response_model=TransactionListResponse)
def list_account_transactions(
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
