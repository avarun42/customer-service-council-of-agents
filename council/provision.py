"""Provision a shared home space for the council via the commons steward.

Flow (per STEWARDS.md):
  1. Mira posts INTENT into commons describing the requested space (kind: shared, with all 5 council principals).
  2. Steward observes and posts PROMISE inside the request's subspace.
  3. Mira posts ACCEPT inside the request's subspace.
  4. Steward posts COMPLETE with credentials and any per-participant invitations.
  5. We harvest credentials for every council agent and persist them.
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
COUNCIL = ["mira", "bex", "doro", "pria", "cass"]


def session_for(name: str) -> HttpSpaceToolSession:
    s = HttpSpaceToolSession(
        endpoint=COMMONS_URL,
        workspace=REPO / "workspaces" / name,
        agent_name=name,
    )
    s.connect()
    return s


def load_principal(name: str) -> str:
    e = json.loads((REPO / "workspaces" / name / ".intent-space" / "state" / "station-enrollment.json").read_text())
    return e["principal_id"]


def find_steward_id(session: HttpSpaceToolSession) -> str | None:
    """Find a steward presence intent in commons. Returns its senderId."""
    scan = session.scan_full(session.current_space_id)
    for m in scan.get("messages", []):
        if m.get("type") != "INTENT":
            continue
        payload = m.get("payload") or {}
        if "offeredSpaces" in payload or "howToRequest" in payload:
            return m.get("senderId")
    return None


def main() -> None:
    mira = session_for("mira")
    principals = {name: load_principal(name) for name in COUNCIL}
    print("council principals:")
    for name, pid in principals.items():
        print(f"  {name}: {pid}")

    steward_id = find_steward_id(mira)
    print(f"\nsteward in commons: {steward_id}")

    request_payload = {
        "content": "Customer Council requests a shared home space for our hackathon demo.",
        "requestedSpace": {"kind": "shared"},
        "spacePolicy": {
            "visibility": "private",
            "participants": list(principals.values()),
        },
        "kind": "space-request",
    }
    request = mira.intent(
        request_payload["content"],
        parent_id=mira.current_space_id,
        payload=request_payload,
    )
    posted = mira.post_and_confirm(request, step="mira.space-request")
    request_id = posted["intentId"]
    print(f"\nposted space request: {request_id}")

    # Wait for PROMISE inside the request's subspace
    print("waiting for PROMISE…")
    promise = None
    deadline = time.time() + 30
    while time.time() < deadline:
        scan = mira.scan_full(request_id)
        for m in scan.get("messages", []):
            if m.get("type") == "PROMISE":
                promise = m
                break
        if promise:
            break
        time.sleep(1.5)

    if not promise:
        print("ERROR: no PROMISE received within timeout")
        sys.exit(1)
    print(f"got PROMISE: {promise.get('promiseId')} from {promise.get('senderId')}")

    # ACCEPT
    accept = mira.accept(promise_id=promise["promiseId"], parent_id=request_id)
    mira.post(accept, step="mira.accept")
    print("posted ACCEPT")

    # Wait for COMPLETE
    print("waiting for COMPLETE…")
    complete = None
    deadline = time.time() + 60
    while time.time() < deadline:
        scan = mira.scan_full(request_id)
        for m in scan.get("messages", []):
            if m.get("type") == "COMPLETE":
                complete = m
                break
        if complete:
            break
        time.sleep(1.5)

    if not complete:
        print("ERROR: no COMPLETE received within timeout")
        sys.exit(1)

    print("got COMPLETE")
    print(json.dumps(complete.get("payload", {}), indent=2))

    # Persist for the runner to pick up
    out = REPO / "workspaces" / "_provisioned.json"
    out.write_text(json.dumps({
        "request_id": request_id,
        "promise_id": promise["promiseId"],
        "complete_payload": complete.get("payload", {}),
    }, indent=2))
    print(f"\nsaved → {out}")


if __name__ == "__main__":
    main()
