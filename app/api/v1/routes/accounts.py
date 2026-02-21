from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_account_for_user, get_current_holder, get_current_user, get_db
from app.models.account import Account
from app.models.enums import AccountStatus
from app.models.user import User
from app.schemas.account import AccountCreate, AccountResponse, AccountStatusUpdate
from app.services.account_service import create_account
from app.services.audit_service import log_action

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
        initial_deposit=payload.initial_deposit,
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
    if payload.status == AccountStatus.closed and account.balance != 0:
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
