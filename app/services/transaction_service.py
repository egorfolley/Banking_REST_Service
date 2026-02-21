from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.enums import AccountStatus, TransactionStatus, TransactionType
from app.models.transaction import Transaction


def _round_amount(value: float) -> float:
    return round(value, 2)


def _ensure_active(account: Account) -> None:
    if account.status in {AccountStatus.frozen, AccountStatus.closed}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is not active",
        )


def apply_deposit(
    db: Session,
    account: Account,
    amount: float,
    description: str | None = None,
    transaction_type: TransactionType = TransactionType.deposit,
    reference_id: str | None = None,
) -> Transaction:
    _ensure_active(account)
    new_balance = _round_amount(account.balance + amount)
    account.balance = new_balance
    tx = Transaction(
        account_id=account.id,
        transaction_type=transaction_type,
        amount=_round_amount(amount),
        balance_after=new_balance,
        description=description,
        reference_id=reference_id,
        status=TransactionStatus.posted,
    )
    db.add(tx)
    return tx


def apply_withdrawal(
    db: Session,
    account: Account,
    amount: float,
    description: str | None = None,
    transaction_type: TransactionType = TransactionType.withdrawal,
    reference_id: str | None = None,
) -> Transaction:
    _ensure_active(account)
    if account.balance < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds",
        )
    new_balance = _round_amount(account.balance - amount)
    account.balance = new_balance
    tx = Transaction(
        account_id=account.id,
        transaction_type=transaction_type,
        amount=_round_amount(amount),
        balance_after=new_balance,
        description=description,
        reference_id=reference_id,
        status=TransactionStatus.posted,
    )
    db.add(tx)
    return tx
