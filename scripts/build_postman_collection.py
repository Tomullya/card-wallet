#!/usr/bin/env python3
"""Build postman/card-wallet.postman_collection.json (Postman Collection v2.1).

Kept as code so the collection is reviewable in git; run after changing it:
    python3 scripts/build_postman_collection.py
"""

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "postman" / "card-wallet.postman_collection.json"
JSON_HEADER = {"key": "Content-Type", "value": "application/json"}


def test(*lines):
    return {"listen": "test", "script": {"type": "text/javascript", "exec": list(lines)}}


def pre(*lines):
    return {"listen": "prerequest", "script": {"type": "text/javascript", "exec": list(lines)}}


def status(code):
    return f"pm.test('status {code}', () => pm.response.to.have.status({code}));"


def req(name, method, path, body=None, events=(), headers=(), noauth=False, description=None):
    request = {"method": method, "url": "{{baseUrl}}/api/v1" + path, "header": list(headers)}
    if body is not None:
        request["header"].append(JSON_HEADER)
        request["body"] = {
            "mode": "raw",
            "raw": json.dumps(body, indent=2, ensure_ascii=False),
            "options": {"raw": {"language": "json"}},
        }
    if noauth:
        request["auth"] = {"type": "noauth"}
    if description:
        request["description"] = description
    return {"name": name, "request": request, "event": list(events)}


def folder(name, *items):
    return {"name": name, "item": list(items)}


def payment(name, amount, merchant, category, cvv="{{card_cvv}}", key="{{$guid}}", events=()):
    body = {
        "card_id": "{{card_id}}",
        "cvv": cvv,
        "amount": amount,
        "merchant_name": merchant,
        "merchant_category": category,
    }
    return req(name, "POST", "/payments", body, events,
               headers=[{"key": "Idempotency-Key", "value": key}])


collection = {
    "info": {
        "name": "Card Wallet API",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        "description": (
            "Mini Card Wallet — demo fintech API (local). Run top to bottom: every request "
            "saves what the next one needs (token, account, card, CVV). All data is fictional."
        ),
    },
    "auth": {"type": "bearer", "bearer": [{"key": "token", "value": "{{token}}", "type": "string"}]},
    "variable": [
        {"key": "baseUrl", "value": "http://localhost:8000"},
        {"key": "token", "value": ""},
        {"key": "email", "value": ""},
        {"key": "password", "value": "Passw0rd1"},
        {"key": "account_id", "value": ""},
        {"key": "card_id", "value": ""},
        {"key": "card_cvv", "value": ""},
        {"key": "wrong_cvv", "value": ""},
        {"key": "idem_key", "value": ""},
        {"key": "first_tx", "value": ""},
    ],
    "item": [
        req("Health", "GET", "/health", noauth=True, events=[test(
            status(200),
            "pm.test('all services ok', () => pm.expect(pm.response.json().status).to.eql('ok'));",
        )]),
        folder("1. Auth",
            req("Register", "POST", "/auth/register",
                {"email": "{{email}}", "name": "Anna Tester", "password": "{{password}}"},
                noauth=True, events=[
                    pre("pm.collectionVariables.set('email', `user-${Date.now()}@example.com`);"),
                    test(status(201),
                         "pm.test('password not returned', () => pm.expect(pm.response.json()).to.not.have.property('password'));"),
                ]),
            req("Login", "POST", "/auth/login", {"email": "{{email}}", "password": "{{password}}"},
                noauth=True, events=[test(
                    status(200),
                    "const token = pm.response.json().access_token;",
                    "pm.collectionVariables.set('token', token);",
                    "if (pm.environment.name) { pm.environment.set('token', token); }",
                )]),
            req("Login — wrong password", "POST", "/auth/login",
                {"email": "{{email}}", "password": "Wrong1234"}, noauth=True, events=[test(
                    status(401),
                    "pm.test('same error for unknown e-mail and wrong password', () => pm.expect(pm.response.json().error.code).to.eql('INVALID_CREDENTIALS'));",
                )]),
            req("Me", "GET", "/me", events=[test(status(200))]),
        ),
        folder("2. Accounts",
            req("Open EUR account", "POST", "/accounts", {"currency": "EUR"}, events=[test(
                status(201),
                "pm.test('new account has zero balance', () => pm.expect(pm.response.json().balance).to.eql('0.00'));",
                "pm.collectionVariables.set('account_id', pm.response.json().id);",
            )]),
            req("Open second EUR account → 409", "POST", "/accounts", {"currency": "EUR"}, events=[test(
                status(409),
                "pm.test('ACCOUNT_ALREADY_EXISTS', () => pm.expect(pm.response.json().error.code).to.eql('ACCOUNT_ALREADY_EXISTS'));",
            )]),
            req("List accounts", "GET", "/accounts", events=[test(
                status(200),
                "pm.test('one account', () => pm.expect(pm.response.json()).to.have.lengthOf(1));",
            )]),
            req("Top up 100.00", "POST", "/accounts/{{account_id}}/top-up", {"amount": "100.00"}, events=[test(
                status(201),
                "pm.test('balance 100.00', () => pm.expect(pm.response.json().balance).to.eql('100.00'));",
            )]),
            req("Top up 10000.01 → 422", "POST", "/accounts/{{account_id}}/top-up", {"amount": "10000.01"},
                events=[test(status(422))]),
        ),
        folder("3. Cards",
            req("Issue card", "POST", "/accounts/{{account_id}}/cards", {"daily_limit": "500.00"}, events=[test(
                status(201),
                "const card = pm.response.json();",
                "pm.test('PAN uses the fake 400000 prefix', () => pm.expect(card.pan).to.match(/^400000\\d{10}$/));",
                "pm.collectionVariables.set('card_id', card.id);",
                "pm.collectionVariables.set('card_cvv', card.cvv);",
                "pm.collectionVariables.set('wrong_cvv', String((parseInt(card.cvv, 10) + 1) % 1000).padStart(3, '0'));",
            )]),
            req("Get card (masked)", "GET", "/cards/{{card_id}}", events=[test(
                status(200),
                "pm.test('PAN masked, no CVV', () => {",
                "  const c = pm.response.json();",
                "  pm.expect(c.masked_pan).to.match(/^\\*{4} \\*{4} \\*{4} \\d{4}$/);",
                "  pm.expect(c).to.not.have.property('cvv');",
                "});",
            )]),
            req("List cards", "GET", "/accounts/{{account_id}}/cards", events=[test(status(200))]),
        ),
        folder("4. Payments",
            payment("Pay 10.00 (approved, min commission)", "10.00", "Coffee Shop", "RESTAURANTS", events=[test(
                status(201),
                "pm.test('approved with commission 0.50', () => {",
                "  const p = pm.response.json();",
                "  pm.expect(p.status).to.eql('APPROVED');",
                "  pm.expect(p.commission).to.eql('0.50');",
                "});",
            )]),
            payment("Gambling merchant → fraud decline", "10.00", "Lucky Casino", "GAMBLING", events=[test(
                status(201),
                "pm.test('FRAUD_BLOCKED_CATEGORY', () => pm.expect(pm.response.json().decline_reason).to.eql('FRAUD_BLOCKED_CATEGORY'));",
            )]),
            payment("Fraud service timeout → 503", "10.00", "TEST_TIMEOUT", "OTHER", events=[test(
                status(503),
                "pm.test('FRAUD_SERVICE_UNAVAILABLE', () => pm.expect(pm.response.json().error.code).to.eql('FRAUD_SERVICE_UNAVAILABLE'));",
            )]),
            payment("Idempotency — first request", "5.00", "Book Store", "OTHER", key="{{idem_key}}", events=[
                pre("pm.collectionVariables.set('idem_key', pm.variables.replaceIn('{{$guid}}'));"),
                test(status(201), "pm.collectionVariables.set('first_tx', pm.response.json().transaction_id);"),
            ]),
            payment("Idempotency — same key again (no double charge)", "5.00", "Book Store", "OTHER",
                    key="{{idem_key}}", events=[test(
                status(201),
                "pm.test('same transaction returned', () => pm.expect(pm.response.json().transaction_id).to.eql(pm.collectionVariables.get('first_tx')));",
            )]),
            payment("Idempotency — same key, other amount → 409", "6.00", "Book Store", "OTHER",
                    key="{{idem_key}}", events=[test(
                status(409),
                "pm.test('IDEMPOTENCY_KEY_REUSED', () => pm.expect(pm.response.json().error.code).to.eql('IDEMPOTENCY_KEY_REUSED'));",
            )]),
            req("Balance after payments", "GET", "/accounts/{{account_id}}", events=[test(
                status(200),
                "pm.test('100 - 10.50 - 5.50 = 84.00', () => pm.expect(pm.response.json().balance).to.eql('84.00'));",
            )]),
            *[payment(f"Wrong CVV attempt {n}", "1.00", "Shop", "GROCERIES", cvv="{{wrong_cvv}}", events=[test(
                status(201),
                "pm.test('INVALID_CVV', () => pm.expect(pm.response.json().decline_reason).to.eql('INVALID_CVV'));",
            )]) for n in (1, 2, 3)],
            req("Card is blocked after 3 wrong CVV", "GET", "/cards/{{card_id}}", events=[test(
                status(200),
                "pm.test('BLOCKED / TOO_MANY_FAILED_ATTEMPTS', () => {",
                "  const c = pm.response.json();",
                "  pm.expect(c.status).to.eql('BLOCKED');",
                "  pm.expect(c.block_reason).to.eql('TOO_MANY_FAILED_ATTEMPTS');",
                "});",
            )]),
        ),
        folder("5. Statement",
            req("Statement — all", "GET", "/accounts/{{account_id}}/transactions?limit=20&offset=0", events=[test(
                status(200),
                "pm.test('newest first', () => {",
                "  const items = pm.response.json().items;",
                "  pm.expect(items[items.length - 1].type).to.eql('TOP_UP');",
                "});",
            )]),
            req("Statement — declined only", "GET", "/accounts/{{account_id}}/transactions?status=DECLINED", events=[test(
                status(200),
                "pm.test('only declined', () => pm.response.json().items.forEach(i => pm.expect(i.status).to.eql('DECLINED')));",
            )]),
        ),
        folder("6. Cleanup",
            req("Block card → already blocked (409)", "POST", "/cards/{{card_id}}/block", events=[test(
                status(409),
                "pm.test('CARD_ALREADY_BLOCKED', () => pm.expect(pm.response.json().error.code).to.eql('CARD_ALREADY_BLOCKED'));",
            )]),
        ),
    ],
}

OUT.write_text(json.dumps(collection, indent=2, ensure_ascii=False) + "\n")
print(f"Wrote {OUT}")
