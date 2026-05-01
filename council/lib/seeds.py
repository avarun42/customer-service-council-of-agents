"""Seed-finding helper: locate the INTENT that created a given space."""
from __future__ import annotations

from typing import Any


def find_seed_intent(session: Any, intent_id: str, search_space: str) -> dict | None:
    try:
        scan = session.scan_full(search_space)
    except Exception:
        return None
    for m in scan.get("messages", []):
        if m.get("type") == "INTENT" and m.get("intentId") == intent_id:
            return m
    return None
