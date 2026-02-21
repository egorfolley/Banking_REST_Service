from uuid import uuid4

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TransactionStatus, TransactionType
from app.models.mixins import TimestampMixin


class Transaction(TimestampMixin, Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    account_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    reference_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus),
        default=TransactionStatus.posted,
        nullable=False,
    )

    account = relationship("Account", back_populates="transactions")
