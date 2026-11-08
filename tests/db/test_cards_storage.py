import pytest

from tests.helpers import create_account, issue_card, register_and_login


@pytest.mark.req("BR-CARD-02", "NFR-04")
def test_full_pan_and_cvv_not_stored(api, db):
    client = register_and_login(api)
    card = issue_card(api, client, create_account(api, client)["id"])
    row = db.execute(
        "select pan_last4, pan_hash, cvv_hash, row_to_json(cards)::text from cards where id = %s",
        (card["id"],),
    ).fetchone()
    pan_last4, pan_hash, cvv_hash, whole_row = row
    assert pan_last4 == card["pan"][-4:]
    assert card["pan"] not in whole_row
    assert cvv_hash.startswith("$2")
    assert f'"{card["cvv"]}"' not in whole_row


@pytest.mark.req("BR-CARD-02", "NFR-04")
def test_pan_hash_is_keyed_not_plain_sha256(api, db):
    """Found in final review: plain SHA-256 of a PAN with known prefix and last 4 digits
    can be brute-forced in under a second (only 10^6 candidates)."""
    import hashlib

    client = register_and_login(api)
    card = issue_card(api, client, create_account(api, client)["id"])
    stored = db.execute("select pan_hash from cards where id = %s", (card["id"],)).fetchone()[0]
    assert stored != hashlib.sha256(card["pan"].encode()).hexdigest()
