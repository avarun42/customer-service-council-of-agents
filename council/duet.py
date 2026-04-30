"""Duet warmup: two agents alternating song lines under one parent intent.

This validates the scaffolding before we build the real council.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "sdk"))

from http_space_tools import HttpSpaceToolSession  # noqa: E402

COMMONS_URL = "https://spacebase1.differ.ac/commons"


def session_for(agent_name: str) -> HttpSpaceToolSession:
    s = HttpSpaceToolSession(
        endpoint=COMMONS_URL,
        workspace=REPO / "workspaces" / agent_name,
        agent_name=agent_name,
    )
    s.connect()
    return s


def main() -> None:
    a = session_for("duet1")
    b = session_for("duet2")

    parent = a.post_and_confirm(
        a.intent("Duet warmup: alternating lines about intent space.", parent_id=a.current_space_id),
        step="duet.parent",
    )
    space = parent["intentId"]
    print("parent intent:", space)

    lines = [
        ("duet1", "Verses bloom where attention rests,"),
        ("duet2", "Spaces nest and intents converge,"),
        ("duet1", "Promises echo without command,"),
        ("duet2", "And work emerges from open hands."),
    ]
    for who, text in lines:
        sess = a if who == "duet1" else b
        sess.post(sess.intent(text, parent_id=space), step=f"duet.line.{who}")
        time.sleep(0.5)

    final = a.scan_full(space)
    print(f"\n=== {len(final.get('messages', []))} messages under {space} ===")
    for m in final.get("messages", []):
        if m.get("type") == "INTENT":
            print(f"  [{m.get('senderId', '')[-12:]}] {m.get('payload', {}).get('content')}")


if __name__ == "__main__":
    main()
