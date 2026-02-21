from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.enums import AccountStatus, TransactionStatus, TransactionType
from app.models.transaction import Transaction


def _ensure_active(account: Account) -> None:
    if account.status in {AccountStatus.frozen, AccountStatus.closed}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is not active",
        )


def apply_deposit(
    db: Session,
    account: Account,
    amount_cents: int,
    description: str | None = None,
    transaction_type: TransactionType = TransactionType.deposit,
    reference_id: str | None = None,
) -> Transaction:
    _ensure_active(account)
    if amount_cents <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than zero",
        )
    new_balance = account.balance_cents + amount_cents
    account.balance_cents = new_balance
    tx = Transaction(
        account_id=account.id,
        transaction_type=transaction_type,
        amount_cents=amount_cents,
        balance_after_cents=new_balance,
        description=description,
        reference_id=reference_id,
        status=TransactionStatus.posted,
    )
    db.add(tx)
    return tx


def apply_withdrawal(
    db: Session,
    account: Account,
    amount_cents: int,
    description: str | None = None,
    transaction_type: TransactionType = TransactionType.withdrawal,
    reference_id: str | None = None,
) -> Transaction:
    _ensure_active(account)
    if amount_cents <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than zero",
        )
    if account.balance_cents < amount_cents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds",
        )
    new_balance = account.balance_cents - amount_cents
    account.balance_cents = new_balance
    tx = Transaction(
        account_id=account.id,
        transaction_type=transaction_type,
        amount_cents=amount_cents,
        balance_after_cents=new_balance,
        description=description,
        reference_id=reference_id,
        status=TransactionStatus.posted,
    )
    db.add(tx)
    return tx
