import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Card, User
from app.schemas.cards import CardCreate, CardOut, IssuedCardOut
from app.schemas.errors import error_responses
from app.services import cards as card_service
from app.services.card_numbers import format_expiry
from app.services.ownership import get_owned_account, get_owned_card

router = APIRouter(tags=["cards"])


@router.post(
    "/accounts/{account_id}/cards",
    status_code=201,
    response_model=IssuedCardOut,
    responses=error_responses(401, 404, 409, 422),
)
def issue_card(
    account_id: uuid.UUID,
    req: CardCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IssuedCardOut:
    account = get_owned_account(db, user, account_id, for_update=True)
    card, pan, cvv = card_service.issue_card(db, account, req.daily_limit)
    db.commit()
    return IssuedCardOut(
        id=card.id,
        account_id=card.account_id,
        pan=pan,
        cvv=cvv,
        expiry=format_expiry(card.expiry_date),
        status=card.status,
        daily_limit=card.daily_limit,
    )


@router.get(
    "/accounts/{account_id}/cards",
    response_model=list[CardOut],
    responses=error_responses(401, 404, 422),
)
def list_cards(
    account_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[CardOut]:
    account = get_owned_account(db, user, account_id)
    query = select(Card).where(Card.account_id == account.id).order_by(Card.created_at)
    return [card_service.card_out(c) for c in db.scalars(query)]


@router.get("/cards/{card_id}", response_model=CardOut, responses=error_responses(401, 404, 422))
def get_card(
    card_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> CardOut:
    return card_service.card_out(get_owned_card(db, user, card_id))


@router.post(
    "/cards/{card_id}/block", response_model=CardOut, responses=error_responses(401, 404, 409, 422)
)
def block_card(
    card_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> CardOut:
    card = get_owned_card(db, user, card_id, for_update=True)
    card_service.block_by_client(card)
    db.commit()
    return card_service.card_out(card)
