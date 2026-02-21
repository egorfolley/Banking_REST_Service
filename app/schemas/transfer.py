from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.enums import TransferStatus


class TransferCreate(BaseModel):
    from_account_id: str
    to_account_id: str
    amount_cents: int = Field(gt=0)
    description: str | None = None
    idempotency_key: Optional[str] = None

    @field_validator("to_account_id")
    @classmethod
    def _no_self_transfer(cls, value: str, info) -> str:
        from_account_id = info.data.get("from_account_id")
        if from_account_id and value == from_account_id:
            raise ValueError("from_account_id must differ from to_account_id")
        return value


class TransferResponse(BaseModel):
    id: str
    idempotency_key: str
    from_account_id: str
    to_account_id: str
    amount_cents: int
    description: str | None
    status: TransferStatus
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
