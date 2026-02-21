from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import TransactionStatus, TransactionType


class DepositRequest(BaseModel):
    amount_cents: int = Field(gt=0)
    description: str | None = None


class WithdrawRequest(BaseModel):
    amount_cents: int = Field(gt=0)
    description: str | None = None


class TransactionResponse(BaseModel):
    id: str
    account_id: str
    transaction_type: TransactionType
    amount_cents: int
    balance_after_cents: int
    description: str | None
    reference_id: str | None
    status: TransactionStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    page: int
    page_size: int
    total: int
