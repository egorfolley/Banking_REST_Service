from pydantic import BaseModel

from app.schemas.transaction import TransactionResponse


class StatementResponse(BaseModel):
    opening_balance: float
    closing_balance: float
    total_deposits: float
    total_withdrawals: float
    transaction_count: int
    transactions: list[TransactionResponse]
