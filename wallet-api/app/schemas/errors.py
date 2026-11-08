"""Error response models, used to document error responses in OpenAPI (NFR-03)."""

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    field: str
    problem: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] | None = None


class ErrorOut(BaseModel):
    error: ErrorBody


_DESCRIPTIONS = {
    401: "Missing, invalid or expired token / wrong credentials",
    404: "Not found or belongs to another client",
    409: "Conflict with the current state",
    422: "Validation error",
    503: "Anti-fraud service unavailable",
}


def error_responses(*codes: int) -> dict:
    return {code: {"model": ErrorOut, "description": _DESCRIPTIONS[code]} for code in codes}
