from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.account_holder import AccountHolder
from app.models.user import User
from app.schemas.account_holder import (
    AccountHolderCreate,
    AccountHolderResponse,
    AccountHolderUpdate,
)
from app.services.audit_service import log_action

router = APIRouter()


@router.post("/", response_model=AccountHolderResponse, status_code=status.HTTP_201_CREATED)
def create_account_holder(
    payload: AccountHolderCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.scalar(select(AccountHolder).where(AccountHolder.user_id == current_user.id))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account holder profile already exists",
        )

    holder = AccountHolder(user_id=current_user.id, **payload.model_dump())
    db.add(holder)
    db.commit()
    db.refresh(holder)

    log_action(
        db,
        user_id=current_user.id,
        action="create_account_holder",
        resource_type="account_holder",
        resource_id=holder.id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()

    return holder


@router.get("/me", response_model=AccountHolderResponse)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    holder = db.scalar(select(AccountHolder).where(AccountHolder.user_id == current_user.id))
    if not holder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account holder profile not found",
        )
    return holder


@router.put("/me", response_model=AccountHolderResponse)
def update_me(
    payload: AccountHolderUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    holder = db.scalar(select(AccountHolder).where(AccountHolder.user_id == current_user.id))
    if not holder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account holder profile not found",
        )

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(holder, field, value)

    log_action(
        db,
        user_id=current_user.id,
        action="update_account_holder",
        resource_type="account_holder",
        resource_id=holder.id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(holder)

    return holder
