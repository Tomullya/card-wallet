# BR-AUTH — Registration, login and access

## BR-AUTH-01 Registration

A new client can register with email, name and password.

Acceptance criteria:
- Email must have a valid format and is stored in lower case.
- Email must be unique. A duplicate email returns `409 EMAIL_ALREADY_REGISTERED`.
- Name: 1–100 characters, not only spaces.
- Password: at least 8 characters, contains at least one letter and one digit.
- Invalid input returns `422 VALIDATION_ERROR`.
- Successful registration returns `201` with client id, email, name and registration date.
- The response never contains the password or its hash.

## BR-AUTH-02 Login

A registered client can log in with email and password and receives an access token.

Acceptance criteria:
- Correct credentials return `200` with a JWT access token valid for 60 minutes.
- Wrong email **or** wrong password returns `401 INVALID_CREDENTIALS` with the same
  message in both cases (the API must not reveal whether the email exists).
- Email is matched case-insensitively.

## BR-AUTH-03 Protected endpoints

All endpoints except registration, login and health check require a valid token.

Acceptance criteria:
- Missing, malformed, expired or tampered token returns `401 UNAUTHORIZED`.
- The token is sent in the header `Authorization: Bearer <token>`.

## BR-AUTH-04 Current client

A logged-in client can get their own profile.

Acceptance criteria:
- `GET /api/v1/me` returns id, email, name and registration date of the token owner.

## BR-AUTH-05 Password storage

Acceptance criteria:
- Passwords are stored only as a salted hash (bcrypt).
- Passwords never appear in API responses or logs.
