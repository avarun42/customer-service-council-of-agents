"""Pretty-print the current state of the shared Lume space.

Useful for inspecting the demo from the CLI when the observatory isn't
handy.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "sdk"))
sys.path.insert(0, str(REPO / "council"))

from lume_session import LUME_SPACE_ID, lume_session  # noqa: E402


def main() -> None:
    s = lume_session("mira")
    queue = s.scan_full(LUME_SPACE_ID)
    tickets = [m for m in queue.get("messages", []) if m.get("type") == "INTENT" and (m.get("payload") or {}).get("kind") == "customer-complaint"]
    print(f"shared Lume space: {LUME_SPACE_ID}")
    print(f"top-level intents: {len(queue.get('messages', []))}")
    print(f"customer tickets: {len(tickets)}")
    for t in tickets:
        tid = t["intentId"]
        interior = s.scan_full(tid)
        replies = interior.get("messages", [])
        print(f"\nticket {tid}: {len(replies)} replies")
        for m in replies:
            kind = (m.get("payload") or {}).get("kind", "?")
            sender = m.get("senderId", "?")[-12:]
            content = ((m.get("payload") or {}).get("content") or "")[:120]
            print(f"  [{kind:25}] by {sender}: {content}")


if __name__ == "__main__":
    main()
