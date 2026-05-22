from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_KEYS = {"core_docs", "components"}


def validate_source(payload: dict[str, Any]) -> None:
    """Strict schema checks for generator input payload."""
    missing = REQUIRED_KEYS - payload.keys()
    if missing:
        raise ValueError(f"Missing required sections: {', '.join(sorted(missing))}")

    # Source schema is object maps keyed by slug.
    if not isinstance(payload["core_docs"], dict):
        raise ValueError("'core_docs' must be an object map")
    if not isinstance(payload["components"], dict):
        raise ValueError("'components' must be an object map")


def load_framework7_source(path: Path) -> dict[str, Any]:
    """
    Load and validate the Framework7 documentation source.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Source documentation file not found: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in source file: {path}") from exc

    if not isinstance(payload, dict):
        raise ValueError("Invalid source payload: expected root object")

    validate_source(payload)
    return payload
