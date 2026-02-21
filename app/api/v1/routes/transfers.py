from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_account_for_user, get_current_user, get_db
from app.models.account import Account
from app.models.transfer import Transfer
from app.models.user import User
from app.schemas.transfer import TransferCreate, TransferResponse
from app.services.audit_service import log_action
from app.services.transfer_service import create_transfer

router = APIRouter()


@router.post("/", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
def transfer_funds(
    payload: TransferCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.scalar(select(Transfer).where(Transfer.idempotency_key == payload.idempotency_key))
    if existing:
        get_account_for_user(existing.from_account_id, current_user, db)
        return existing

    from_account = get_account_for_user(payload.from_account_id, current_user, db)
    to_account = db.scalar(select(Account).where(Account.id == payload.to_account_id))
    if not to_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destination account not found",
        )
    transfer = create_transfer(
        db,
        from_account,
        to_account,
        idempotency_key=payload.idempotency_key,
        amount_cents=payload.amount_cents,
        description=payload.description,
    )

    log_action(
        db,
        user_id=current_user.id,
        action="transfer",
        resource_type="transfer",
        resource_id=transfer.id,
        details=f"from={from_account.id} to={to_account.id}",
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(transfer)
    return transfer
