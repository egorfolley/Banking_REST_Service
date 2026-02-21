from datetime import date, datetime

from pydantic import BaseModel, field_validator

from app.utils.validators import validate_ssn_last_four


class AccountHolderBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    phone: str
    address: str
    ssn_last_four: str

    @field_validator("ssn_last_four")
    @classmethod
    def _ssn_last_four(cls, value: str) -> str:
        return validate_ssn_last_four(value)


class AccountHolderCreate(AccountHolderBase):
    pass


class AccountHolderUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    phone: str | None = None
    address: str | None = None
    ssn_last_four: str | None = None

    @field_validator("ssn_last_four")
    @classmethod
    def _ssn_last_four(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_ssn_last_four(value)


class AccountHolderResponse(AccountHolderBase):
    id: str
    user_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
