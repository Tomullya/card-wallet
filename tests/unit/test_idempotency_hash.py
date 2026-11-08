import uuid

import pytest
from app.schemas.payments import PaymentRequest
from app.services.idempotency import request_hash


def payment(cvv: str) -> PaymentRequest:
    return PaymentRequest(
        card_id=uuid.UUID(int=1),
        cvv=cvv,
        amount="10.00",
        merchant_name="Shop",
        merchant_category="GROCERIES",
    )


@pytest.mark.req("NFR-04", "BR-PAY-07")
def test_request_hash_does_not_depend_on_cvv():
    """Found in final review: the stored hash included the CVV, so the CVV could be
    recovered with 1000 guesses. The CVV must not influence the stored hash."""
    assert request_hash(payment("123")) == request_hash(payment("456"))


@pytest.mark.req("BR-PAY-07")
def test_request_hash_depends_on_amount():
    other = payment("123").model_copy(update={"merchant_name": "Other"})
    assert request_hash(payment("123")) != request_hash(other)
