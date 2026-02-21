from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models.account import Account
from app.models.account_holder import AccountHolder
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    user = db.scalar(select(User).where(User.id == user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
        )
    return user


def get_current_holder(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountHolder:
    holder = db.scalar(select(AccountHolder).where(AccountHolder.user_id == current_user.id))
    if not holder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account holder profile not found",
        )
    return holder


def get_account_for_user(
    account_id: str,
    current_user: User,
    db: Session,
) -> Account:
    stmt = (
        select(Account)
        .join(AccountHolder, Account.holder_id == AccountHolder.id)
        .where(Account.id == account_id, AccountHolder.user_id == current_user.id)
    )
    account = db.scalar(stmt)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return account
