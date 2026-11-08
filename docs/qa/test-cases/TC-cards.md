# Test cases — Cards (BR-CARD)

### TC-CARD-001 Issue a card: full PAN and CVV shown once

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-CARD-02, BR-CARD-03 | High | Positive | `tests/api/test_cards.py::test_issue_card_returns_full_pan_and_cvv_once` |

**Steps:** 1. `POST /accounts/{id}/cards` with `{}`. 2. `GET /cards/{card_id}`.
**Expected result:** step 1 → 201, `pan` = 16 digits starting `400000`, Luhn-valid; `cvv` = 3 digits; `status` ACTIVE; `daily_limit` `"1000.00"`; `expiry` = end of month in 3 years. Step 2 → `masked_pan` = `**** **** **** <last 4>`, no `pan`, no `cvv`.

### TC-CARD-002 Daily limit boundaries

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-CARD-02 | Medium | Boundary | `tests/api/test_cards.py::test_daily_limit_boundaries_accepted`, `tests/api/test_cards.py::test_daily_limit_invalid_422` |

**Expected result:** `1.00` and `10000.00` → 201; `0.99`, `10000.01`, `0`, `-5`, `abc` → 422.

### TC-CARD-003 At most 3 active cards per account

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-CARD-01 | High | Boundary | `tests/api/test_cards.py::test_fourth_active_card_409`, `tests/api/test_cards.py::test_blocked_card_frees_slot`, `tests/api/test_cards.py::test_expired_card_frees_slot_and_shows_expired` |

**Steps:** 1. Issue 3 cards, then a 4th. 2. Block one card, issue again. 3. Expire one card (DB), issue again.
**Expected result:** 4th → 409 `CARD_LIMIT_REACHED`; after blocking or expiry a new card can be issued.

### TC-CARD-004 Block a card

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-CARD-04 | High | State transition | `tests/api/test_cards.py::test_block_card` |

**Steps:** block an ACTIVE card twice.
**Expected result:** first → 200 `BLOCKED` / `BLOCKED_BY_CLIENT`; second → 409 `CARD_ALREADY_BLOCKED`.

### TC-CARD-005 Expiry date boundary

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-CARD-05 | Medium | Boundary | `tests/api/test_cards.py::test_card_valid_on_expiry_day`, `tests/unit/test_card_numbers.py::test_is_expired` |

**Steps:** set `expiry_date` to today (UTC), view the card; set it to yesterday, view again.
**Expected result:** today → ACTIVE; yesterday → EXPIRED.

### TC-CARD-006 Three wrong CVV block the card

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-CARD-06 | High | State transition | `tests/api/test_cvv_attempts.py::test_three_wrong_cvv_blocks_card`, `tests/api/test_cvv_attempts.py::test_two_wrong_cvv_keep_card_active` |

**Steps:** pay with a wrong CVV 3 times, then with the correct CVV.
**Expected result:** attempts 1–3 → DECLINED `INVALID_CVV`; after 2 attempts the card is still ACTIVE; after 3 it is BLOCKED / `TOO_MANY_FAILED_ATTEMPTS`; the 4th payment → `CARD_BLOCKED`.

### TC-CARD-007 CVV counter resets only on approval

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-CARD-06 | High | State transition | `tests/api/test_cvv_attempts.py::test_success_resets_counter`, `tests/api/test_cvv_attempts.py::test_other_declines_do_not_count`, `tests/api/test_cvv_attempts.py::test_attempts_on_blocked_card_do_not_count` |

**Steps:** wrong, wrong, approved, wrong, wrong → check status. Separately: wrong, wrong, insufficient funds, wrong.
**Expected result:** first sequence → ACTIVE. Second sequence → BLOCKED only after the 3rd wrong CVV. Attempts on a blocked card do not change the counter. (Planted defect BUG-03 breaks the first sequence.)

### TC-CARD-008 Another client's cards are invisible

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-CARD-03, BR-CARD-04 | High | Security | `tests/api/test_cards.py::test_other_users_card_and_account_404` |

**Steps:** client B: view A's card, block it, list A's account cards, issue a card on A's account.
**Expected result:** each → 404; A's card stays ACTIVE. (Planted defect BUG-04 breaks this.)
