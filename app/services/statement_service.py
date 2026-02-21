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
    opening_balance = last_before.balance_after if last_before else 0.0

    transactions = db.scalars(
        select(Transaction)
        .where(
            Transaction.account_id == account_id,
            Transaction.created_at >= start_dt,
            Transaction.created_at <= end_dt,
        )
        .order_by(Transaction.created_at)
    ).all()

    closing_balance = opening_balance
    if transactions:
        closing_balance = transactions[-1].balance_after

    deposit_types = {TransactionType.deposit, TransactionType.transfer_in}
    withdrawal_types = {TransactionType.withdrawal, TransactionType.transfer_out, TransactionType.fee}

    total_deposits = sum(t.amount for t in transactions if t.transaction_type in deposit_types)
    total_withdrawals = sum(t.amount for t in transactions if t.transaction_type in withdrawal_types)

    return {
        "opening_balance": round(opening_balance, 2),
        "closing_balance": round(closing_balance, 2),
        "total_deposits": round(total_deposits, 2),
        "total_withdrawals": round(total_withdrawals, 2),
        "transaction_count": len(transactions),
        "transactions": transactions,
    }
