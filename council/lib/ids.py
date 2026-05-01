"""ID-formatting helpers."""
from __future__ import annotations


def short_id(s: str | None) -> str:
    """Return a short suffix of an opaque id, suitable for log lines."""
    if not s:
        return "?"
    return s.split("-")[-1][:8] if "-" in s else s[-12:]
