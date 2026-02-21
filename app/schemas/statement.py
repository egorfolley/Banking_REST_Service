from pydantic import BaseModel

from app.schemas.transaction import TransactionResponse


class StatementResponse(BaseModel):
    opening_balance_cents: int
    closing_balance_cents: int
    total_deposits_cents: int
    total_withdrawals_cents: int
    transaction_count: int
    transactions: list[TransactionResponse]
