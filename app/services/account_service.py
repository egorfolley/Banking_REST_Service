from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.account_holder import AccountHolder
from app.models.enums import TransactionType
from app.services.transaction_service import apply_deposit
from app.utils.account_number import generate_account_number


def _unique_account_number(db: Session) -> str:
    for _ in range(10):
        candidate = generate_account_number()
        exists = db.scalar(select(Account).where(Account.account_number == candidate))
        if not exists:
            return candidate
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not generate account number",
    )


def create_account(
    db: Session,
    holder: AccountHolder,
    account_type,
    currency: str,
    initial_deposit: float | None,
) -> Account:
    account_number = _unique_account_number(db)
    account = Account(
        holder_id=holder.id,
        account_number=account_number,
        account_type=account_type,
        currency=currency,
        balance=0.0,
    )
    db.add(account)
    db.flush()

    if initial_deposit and initial_deposit > 0:
        apply_deposit(
            db,
            account,
            amount=initial_deposit,
            description="Initial deposit",
            transaction_type=TransactionType.deposit,
        )

    return account
