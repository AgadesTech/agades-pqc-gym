from __future__ import annotations

from typing import Any

from pydantic import ValidationError


def stable_validation_error_messages(exc: ValidationError) -> list[str]:
    errors = _validation_error_details(exc)
    messages: list[str] = []
    for error in errors:
        if not isinstance(error, dict):
            continue
        location = _location_label(error.get("loc"))
        message = str(error.get("msg") or "validation error")
        error_type = str(error.get("type") or "validation_error")
        messages.append(f"{location}: {message} [{error_type}]")
    return messages or [exc.__class__.__name__]


def _validation_error_details(exc: ValidationError) -> list[Any]:
    try:
        return exc.errors(include_url=False, include_input=False)
    except TypeError:
        return exc.errors()


def _location_label(location: Any) -> str:
    if not isinstance(location, tuple) or not location:
        return "AttackPlan"
    return ".".join(str(part) for part in location)
