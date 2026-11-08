from datetime import UTC, datetime
from typing import Annotated

from pydantic import PlainSerializer


def _iso_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


# Timestamps are always returned in UTC with a "Z" suffix (NFR-02).
UtcDatetime = Annotated[datetime, PlainSerializer(_iso_utc, return_type=str)]
