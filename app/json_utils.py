"""JSON serialization for embedding data in templates (Decimal -> float)."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any


def _default(value: Any) -> float:
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"Object of type {type(value)} is not JSON serializable")


def dumps(data: Any) -> str:
    return json.dumps(data, default=_default)
