from fastapi import APIRouter

from app.api.v1.routes import (
    account_holders,
    accounts,
    auth,
    cards,
    statements,
    transactions,
    transfers,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(account_holders.router, prefix="/account-holders", tags=["account-holders"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(transfers.router, prefix="/transfers", tags=["transfers"])
api_router.include_router(cards.router, prefix="/cards", tags=["cards"])
api_router.include_router(statements.router, prefix="/statements", tags=["statements"])
