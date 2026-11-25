"""Shared document formatting helpers for MongoDB repositories."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def iso_or_raw(value: Any) -> Any:
    """Return an ISO 8601 string for datetimes, otherwise the raw value.

    PyMongo hands back naive datetimes that are actually UTC; tag them so
    browsers do not read them as local time.
    """
    if isinstance(value, datetime):
        return (value.replace(tzinfo=UTC) if value.tzinfo is None else value).isoformat()
    return value
