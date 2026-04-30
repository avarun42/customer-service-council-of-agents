"""Claim a private home space for one agent via the commons steward.

Posts the standard request shape into commons, waits for PROMISE,
posts ACCEPT, waits for COMPLETE, and persists the resulting credentials.

Usage: python3 council/claim_home.py <agent_name>
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "sdk"))

from http_space_tools import HttpSpaceToolSession  # noqa: E402

COMMONS_URL = "https://spacebase1.differ.ac/commons"


def claim(name: str, timeout: float = 90.0) -> dict:
    homefile = REPO / "workspaces" / name / ".intent-space" / "state" / "home-space.json"
    if homefile.exists():
        existing = json.loads(homefile.read_text())
        print(f"[{name}] already has home space: {existing.get('spaceId') or existing.get('space_id')}")
        return existing

    session = HttpSpaceToolSession(
        endpoint=COMMONS_URL,
        workspace=REPO / "workspaces" / name,
        agent_name=name,
    )
    session.connect()
    request_payload = {
        "content": f"Please provision one private home space for {name}.",
        "requestedSpace": {"kind": "home"},
        "spacePolicy": {"visibility": "private"},
    }
    request = session.intent(
        request_payload["content"],
        parent_id=session.current_space_id,
        payload=request_payload,
    )
    posted = session.post_and_confirm(request, step=f"{name}.home-request")
    request_id = posted["intentId"]
    print(f"[{name}] posted home-space request {request_id}")

    deadline = time.time() + timeout
    promise = None
    while time.time() < deadline and not promise:
        try:
            scan = session.scan_full(request_id)
            for m in scan.get("messages", []):
                if m.get("type") == "PROMISE":
                    promise = m
                    break
        except Exception as e:
            print(f"[{name}] scan err: {e}")
        if not promise:
            time.sleep(2)
    if not promise:
        raise RuntimeError(f"[{name}] no PROMISE in {timeout}s")
    print(f"[{name}] got PROMISE {promise.get('promiseId')}")

    accept = session.accept(promise_id=promise["promiseId"], parent_id=request_id)
    session.post(accept, step=f"{name}.accept")
    print(f"[{name}] sent ACCEPT")

    complete = None
    deadline = time.time() + timeout
    while time.time() < deadline and not complete:
        scan = session.scan_full(request_id)
        for m in scan.get("messages", []):
            if m.get("type") == "COMPLETE":
                complete = m
                break
        if not complete:
            time.sleep(2)
    if not complete:
        raise RuntimeError(f"[{name}] no COMPLETE in {timeout}s")

    payload = complete.get("payload", {}) or {}
    print(f"[{name}] got COMPLETE — payload keys: {list(payload.keys())}")
    homefile.parent.mkdir(parents=True, exist_ok=True)
    homefile.write_text(json.dumps(payload, indent=2))
    return payload


if __name__ == "__main__":
    out = claim(sys.argv[1])
    print(json.dumps(out, indent=2))
