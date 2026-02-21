from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import CardStatus, CardType
from app.utils.validators import (
    validate_card_number,
    validate_expiry_month,
    validate_expiry_year,
)


class CardCreate(BaseModel):
    account_id: str
    card_number: str
    card_type: CardType
    expiry_month: int
    expiry_year: int
    daily_limit: float = Field(gt=0)

    @field_validator("card_number")
    @classmethod
    def _card_number(cls, value: str) -> str:
        return validate_card_number(value)

    @field_validator("expiry_month")
    @classmethod
    def _expiry_month(cls, value: int) -> int:
        return validate_expiry_month(value)

    @field_validator("expiry_year")
    @classmethod
    def _expiry_year(cls, value: int) -> int:
        return validate_expiry_year(value)


class CardStatusUpdate(BaseModel):
    status: CardStatus


class CardLimitUpdate(BaseModel):
    daily_limit: float = Field(gt=0)


class CardResponse(BaseModel):
    id: str
    account_id: str
    card_number_last_four: str
    card_type: CardType
    status: CardStatus
    expiry_month: int
    expiry_year: int
    daily_limit: float
    created_at: datetime

    model_config = {"from_attributes": True}
