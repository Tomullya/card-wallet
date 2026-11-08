# Test cases — Registration and login (BR-AUTH)

Base URL `http://localhost:8000/api/v1`. "Automated by" names the pytest test; run it with
`.venv/bin/pytest "<node id>"`.

### TC-AUTH-001 Register with valid data

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-AUTH-01, BR-AUTH-05 | High | Positive | `tests/api/test_auth.py::test_register_success_returns_201_without_password` |

**Preconditions:** e-mail not registered.
**Steps:** 1. `POST /auth/register` with `{"email": "User.X@Example.COM", "name": "Anna", "password": "Passw0rd1"}`.
**Expected result:** 201; body has exactly `id`, `email`, `name`, `created_at`; e-mail is lower case; no password field; `created_at` ends with `Z`.

### TC-AUTH-002 Duplicate e-mail in different case

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-AUTH-01 | High | Negative | `tests/api/test_auth.py::test_register_duplicate_email_409` |

**Steps:** 1. Register `user@example.com`. 2. Register `USER@EXAMPLE.COM`.
**Expected result:** step 2 → 409 `EMAIL_ALREADY_REGISTERED`.

### TC-AUTH-003 Password and name boundaries

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-AUTH-01 | Medium | Boundary | `tests/api/test_auth.py::test_register_validation`, `tests/api/test_auth.py::test_register_boundaries_ok` |

**Steps:** register with each value.
**Expected result:** password `abcdefg1` (8) and name of 100 characters → 201. Password `short12` (7 characters), `onlyletters`, `12345678`; name empty, spaces only, 101 characters; invalid e-mail → 422 `VALIDATION_ERROR`.

### TC-AUTH-004 Password longer than 72 bytes

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-AUTH-01, BR-AUTH-02 | Medium | Negative | `tests/api/test_auth.py::test_register_password_over_72_bytes_422_not_500`, `tests/api/test_auth.py::test_login_with_very_long_password_401_not_500` |

**Steps:** 1. Register with a 72-character Cyrillic password (144 bytes). 2. Log in to an existing account with a 100-character password.
**Expected result:** step 1 → 422; step 2 → 401. Never 500 (regression of BUG-06).

### TC-AUTH-005 Login does not reveal registered e-mails

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-AUTH-02 | High | Security | `tests/api/test_auth.py::test_login_wrong_password_and_unknown_email_same_401` |

**Steps:** 1. Log in with a registered e-mail and a wrong password. 2. Log in with an unknown e-mail.
**Expected result:** both 401 `INVALID_CREDENTIALS` with identical bodies.

### TC-AUTH-006 Login ignores e-mail case and spaces

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-AUTH-02 | Medium | Positive | `tests/api/test_auth.py::test_login_email_case_and_spaces_ignored` |

**Steps:** log in with `"  USER@EXAMPLE.COM "`.
**Expected result:** 200 with a token; `expires_in` = 3600.

### TC-AUTH-007 Invalid tokens are rejected

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-AUTH-03 | High | Security | `tests/api/test_auth.py::test_protected_endpoint_rejects_bad_tokens` |

**Steps:** call `GET /me` with: no header; `Bearer garbage`; `Token <valid>`; a token signed with another secret; an expired token; a token for an unknown user.
**Expected result:** every case → 401 `UNAUTHORIZED`.
