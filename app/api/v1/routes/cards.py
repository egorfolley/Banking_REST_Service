from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_account_for_user, get_current_holder, get_current_user, get_db
from app.models.account import Account
from app.models.card import Card
from app.models.enums import CardStatus
from app.models.user import User
from app.schemas.card import CardCreate, CardLimitUpdate, CardResponse, CardStatusUpdate
from app.services.audit_service import log_action
from app.utils.card_utils import hash_card_number, last_four

router = APIRouter()


def _get_card_for_holder(card_id: str, holder_id: str, db: Session) -> Card:
    stmt = (
        select(Card)
        .join(Account, Card.account_id == Account.id)
        .where(Card.id == card_id, Account.holder_id == holder_id)
    )
    card = db.scalar(stmt)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found",
        )
    return card


@router.post("/", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
def create_card(
    payload: CardCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = get_account_for_user(payload.account_id, current_user, db)
    active_count = db.scalar(
        select(func.count()).select_from(Card).where(
            Card.account_id == account.id,
            Card.status == CardStatus.active,
        )
    ) or 0
    if active_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum of 3 active cards allowed",
        )

    card = Card(
        account_id=account.id,
        card_number_last_four=last_four(payload.card_number),
        card_number_hash=hash_card_number(payload.card_number),
        card_type=payload.card_type,
        status=CardStatus.active,
        expiry_month=payload.expiry_month,
        expiry_year=payload.expiry_year,
        daily_limit=round(payload.daily_limit, 2),
    )
    db.add(card)
    db.flush()

    log_action(
        db,
        user_id=current_user.id,
        action="create_card",
        resource_type="card",
        resource_id=card.id,
        details=f"account_id={account.id}",
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(card)
    return card


@router.get("/", response_model=list[CardResponse])
def list_cards(
    holder=Depends(get_current_holder),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Card)
        .join(Account, Card.account_id == Account.id)
        .where(Account.holder_id == holder.id)
    )
    return db.scalars(stmt).all()


@router.get("/{card_id}", response_model=CardResponse)
def get_card(
    card_id: str,
    holder=Depends(get_current_holder),
    db: Session = Depends(get_db),
):
    return _get_card_for_holder(card_id, holder.id, db)


@router.patch("/{card_id}/status", response_model=CardResponse)
def update_card_status(
    card_id: str,
    payload: CardStatusUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    holder=Depends(get_current_holder),
    db: Session = Depends(get_db),
):
    card = _get_card_for_holder(card_id, holder.id, db)
    if payload.status == CardStatus.active and card.status != CardStatus.active:
        active_count = db.scalar(
            select(func.count()).select_from(Card).where(
                Card.account_id == card.account_id,
                Card.status == CardStatus.active,
            )
        ) or 0
        if active_count >= 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum of 3 active cards allowed",
            )

    card.status = payload.status
    log_action(
        db,
        user_id=current_user.id,
        action="update_card_status",
        resource_type="card",
        resource_id=card.id,
        details=f"status={payload.status}",
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(card)
    return card


@router.patch("/{card_id}/limit", response_model=CardResponse)
def update_card_limit(
    card_id: str,
    payload: CardLimitUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    holder=Depends(get_current_holder),
    db: Session = Depends(get_db),
):
    card = _get_card_for_holder(card_id, holder.id, db)
    card.daily_limit = round(payload.daily_limit, 2)

    log_action(
        db,
        user_id=current_user.id,
        action="update_card_limit",
        resource_type="card",
        resource_id=card.id,
        details=f"limit={card.daily_limit}",
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(card)
    return card
