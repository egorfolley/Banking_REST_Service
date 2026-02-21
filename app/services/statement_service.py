from datetime import datetime, time

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.enums import TransactionType
from app.models.transaction import Transaction


def build_statement(db: Session, account_id: str, start_date, end_date):
    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.max)

    last_before = db.scalar(
        select(Transaction)
        .where(Transaction.account_id == account_id, Transaction.created_at < start_dt)
        .order_by(desc(Transaction.created_at))
    )
    opening_balance_cents = last_before.balance_after_cents if last_before else 0

    transactions = db.scalars(
        select(Transaction)
        .where(
            Transaction.account_id == account_id,
            Transaction.created_at >= start_dt,
            Transaction.created_at <= end_dt,
        )
        .order_by(Transaction.created_at)
    ).all()

    closing_balance_cents = opening_balance_cents
    if transactions:
        closing_balance_cents = transactions[-1].balance_after_cents

    deposit_types = {TransactionType.deposit, TransactionType.transfer_in}
    withdrawal_types = {TransactionType.withdrawal, TransactionType.transfer_out, TransactionType.fee}

    total_deposits_cents = sum(
        t.amount_cents for t in transactions if t.transaction_type in deposit_types
    )
    total_withdrawals_cents = sum(
        t.amount_cents for t in transactions if t.transaction_type in withdrawal_types
    )

    return {
        "opening_balance_cents": opening_balance_cents,
        "closing_balance_cents": closing_balance_cents,
        "total_deposits_cents": total_deposits_cents,
        "total_withdrawals_cents": total_withdrawals_cents,
        "transaction_count": len(transactions),
        "transactions": transactions,
    }
