from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_account_for_user, get_current_user, get_db
from app.models.user import User
from app.schemas.statement import StatementResponse
from app.services.audit_service import log_action
from app.services.statement_service import build_statement

router = APIRouter()


@router.get("/{account_id}", response_model=StatementResponse)
def get_statement(
    account_id: str,
    request: Request,
    start: date = Query(...),
    end: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start must be before end",
        )

    account = get_account_for_user(account_id, current_user, db)
    result = build_statement(db, account.id, start, end)

    log_action(
        db,
        user_id=current_user.id,
        action="statement",
        resource_type="account",
        resource_id=account.id,
        details=f"start={start} end={end}",
        ip_address=request.client.host if request.client else None,
    )
    db.commit()

    return result
