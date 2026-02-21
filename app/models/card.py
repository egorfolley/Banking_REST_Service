from uuid import uuid4

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CardStatus, CardType
from app.models.mixins import TimestampMixin


class Card(TimestampMixin, Base):
    __tablename__ = "cards"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    account_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    card_number_last_four: Mapped[str] = mapped_column(String(4), nullable=False)
    card_number_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    card_type: Mapped[CardType] = mapped_column(Enum(CardType), nullable=False)
    status: Mapped[CardStatus] = mapped_column(
        Enum(CardStatus),
        default=CardStatus.active,
        nullable=False,
    )
    expiry_month: Mapped[int] = mapped_column(nullable=False)
    expiry_year: Mapped[int] = mapped_column(nullable=False)
    daily_limit: Mapped[float] = mapped_column(Numeric(12, 2, asdecimal=False), nullable=False)

    account = relationship("Account", back_populates="cards")
