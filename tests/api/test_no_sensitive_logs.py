"""Full PAN, CVV and passwords must never appear in service logs (NFR-04)."""

import shutil
import subprocess

import pytest

from tests.helpers import PASSWORD, funded_card, pay, register_and_login, wrong_cvv


def compose_logs() -> str:
    result = subprocess.run(
        ["docker", "compose", "logs", "--no-color", "wallet", "fraud"],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    return result.stdout + result.stderr


@pytest.mark.req("NFR-04")
@pytest.mark.skipif(shutil.which("docker") is None, reason="needs docker to read service logs")
def test_logs_do_not_contain_pan_cvv_or_password(api):
    client = register_and_login(api)
    card = funded_card(api, client)
    pay(api, client, card, "10.00")
    pay(api, client, card, "10.00", cvv=wrong_cvv(card["cvv"]))
    pay(api, client, card, "10.00", merchant="TEST_ERROR")
    logs = compose_logs()
    assert card["pan"] not in logs
    assert f"cvv={card['cvv']}" not in logs and f'"cvv": "{card["cvv"]}"' not in logs
    assert PASSWORD not in logs
