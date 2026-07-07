"""Small helpers for HTMX response headers (toasts via HX-Trigger)."""

from __future__ import annotations

import json


def toast_header(message: str, kind: str = "success") -> dict[str, str]:
    return {"HX-Trigger": json.dumps({"show-toast": {"message": message, "kind": kind}})}
