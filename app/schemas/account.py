from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import AccountStatus, AccountType


class AccountCreate(BaseModel):
    account_type: AccountType
    currency: str = "USD"
    initial_deposit: float | None = Field(default=None, ge=0)


class AccountStatusUpdate(BaseModel):
    status: AccountStatus


class AccountResponse(BaseModel):
    id: str
    holder_id: str
    account_number: str
    account_type: AccountType
    status: AccountStatus
    balance: float
    currency: str
    created_at: datetime

    model_config = {"from_attributes": True}
