from uuid import uuid4

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AccountStatus, AccountType
from app.models.mixins import TimestampMixin


class Account(TimestampMixin, Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    holder_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("account_holders.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    account_number: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    account_type: Mapped[AccountType] = mapped_column(Enum(AccountType), nullable=False)
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus),
        default=AccountStatus.active,
        nullable=False,
    )
    balance_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    holder = relationship("AccountHolder", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")
    cards = relationship("Card", back_populates="account")
