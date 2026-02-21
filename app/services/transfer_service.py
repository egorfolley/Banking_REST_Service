from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.enums import AccountStatus, TransactionType, TransferStatus
from app.models.transfer import Transfer
from app.services.transaction_service import apply_deposit, apply_withdrawal


def create_transfer(
    db: Session,
    from_account: Account,
    to_account: Account,
    idempotency_key: str,
    amount: float,
    description: str | None,
) -> Transfer:
    amount = round(amount, 2)
    if from_account.status != AccountStatus.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source account is not active",
        )
    if to_account.status != AccountStatus.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Destination account is not active",
        )

    existing = db.scalar(select(Transfer).where(Transfer.idempotency_key == idempotency_key))
    if existing:
        return existing

    transfer = Transfer(
        idempotency_key=idempotency_key,
        from_account_id=from_account.id,
        to_account_id=to_account.id,
        amount=amount,
        description=description,
        status=TransferStatus.pending,
    )
    db.add(transfer)
    db.flush()

    apply_withdrawal(
        db,
        from_account,
        amount=amount,
        description=description or "Transfer out",
        transaction_type=TransactionType.transfer_out,
        reference_id=transfer.id,
    )
    apply_deposit(
        db,
        to_account,
        amount=amount,
        description=description or "Transfer in",
        transaction_type=TransactionType.transfer_in,
        reference_id=transfer.id,
    )

    transfer.status = TransferStatus.completed
    transfer.completed_at = datetime.now(timezone.utc)
    return transfer
