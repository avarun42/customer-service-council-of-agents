"""Render a list of frames as a compact textual tree for the LLM prompt."""
from __future__ import annotations

import json
from typing import Iterable

from .ids import short_id


def render_tree(messages: Iterable[dict], my_principal: str, principal_to_name: dict[str, str]) -> str:
    lines = []
    for m in messages:
        kind = m.get("type", "?")
        sender = m.get("senderId", "?")
        who = principal_to_name.get(sender, short_id(sender))
        if sender == my_principal:
            who += " (you)"
        payload = m.get("payload") or {}
        content = (
            payload.get("content")
            or payload.get("summary")
            or payload.get("reason")
            or json.dumps(payload, ensure_ascii=False)
        )
        if len(content) > 600:
            content = content[:600] + "…"
        marker = ""
        if m.get("intentId"):
            marker = f" [{short_id(m['intentId'])}]"
        elif m.get("promiseId"):
            marker = f" [promise {short_id(m['promiseId'])}]"
        lines.append(f"- {kind} by {who}{marker}: {content}")
    return "\n".join(lines) if lines else "(empty)"
