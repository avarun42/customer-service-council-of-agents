"""Provision the shared 'Lume Customer Support' space and bind all 5 council agents to it.

Steps:
  1. From Mira's home space, post a SHARED space request listing all 5 principals.
  2. Wait for steward PROMISE → post ACCEPT → wait for COMPLETE.
  3. The COMPLETE may either (a) give credentials directly, or (b) trigger
     invitation INTENTs to land in each participant's home space.
  4. For each participant, scan their home space for an invitation INTENT
     containing a `bind_url`/`claim_url`, then POST a signup body to bind
     their key into the shared space.
  5. Persist shared-space credentials per agent.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from urllib.parse import urlparse, urljoin

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "sdk"))

from intent_space_sdk import (  # noqa: E402
    LocalState,
    build_dpop_signup_proof,
    build_welcome_mat_access_token,
    fetch_json,
    fetch_text,
    parse_welcome_mat,
)

from connect_home import home_session  # noqa: E402

COUNCIL = ["mira", "bex", "doro", "pria", "cass"]
COMMONS_URL = "https://spacebase1.differ.ac/commons"


def load_principal(name: str) -> str:
    e = json.loads((REPO / "workspaces" / name / ".intent-space" / "state" / "home-enrollment.json").read_text())
    return e["principal_id"]


def bind_to_shared(name: str, bind_url: str) -> dict:
    workspace = REPO / "workspaces" / name
    local = LocalState(workspace)

    welcome_url = urljoin(COMMONS_URL.rstrip("/") + "/", ".well-known/welcome.md")
    welcome = parse_welcome_mat(fetch_text(welcome_url))
    tos_text = fetch_text(welcome["endpoints"]["terms"])

    parsed = urlparse(bind_url)
    service_origin = f"{parsed.scheme}://{parsed.netloc}"
    access_token = build_welcome_mat_access_token(local, service_origin=service_origin, tos_text=tos_text)
    response = fetch_json(
        bind_url,
        method="POST",
        headers={"DPoP": build_dpop_signup_proof(local, signup_url=bind_url)},
        body={
            "tos_signature": local.sign_detached_b64url(tos_text),
            "access_token": access_token,
            "handle": name,
        },
    )
    out = workspace / ".intent-space" / "state" / "lume-enrollment.json"
    out.write_text(json.dumps(response, indent=2))
    return response


def main() -> None:
    principals = {n: load_principal(n) for n in COUNCIL}
    print("council principals:")
    for n, p in principals.items():
        print(f"  {n}: {p}")

    mira, mira_home = home_session("mira")
    request_payload = {
        "content": (
            "Provision the shared 'Lume Customer Support' space — the internal "
            "ticketing surface where the customer-intake agent (Mira) drops "
            "tickets and specialized support agents (Billing, Data Ops, "
            "Privacy, Customer Success) self-select work."
        ),
        "requestedSpace": {
            "kind": "shared",
            "participant_principals": list(principals.values()),
        },
        "spacePolicy": {"visibility": "private"},
    }
    request = mira.intent(
        request_payload["content"],
        parent_id=mira.current_space_id,
        payload=request_payload,
    )
    posted = mira.post_and_confirm(request, step="mira.lume-request")
    request_id = posted["intentId"]
    print(f"\nposted shared-space request: {request_id}")

    # Promise → Accept → Complete
    promise = wait_for(mira, request_id, "PROMISE", 60)
    print(f"got PROMISE {promise['promiseId']}")
    mira.post(mira.accept(promise_id=promise["promiseId"], parent_id=request_id), step="mira.lume-accept")
    print("posted ACCEPT")
    complete = wait_for(mira, request_id, "COMPLETE", 60)
    print(f"got COMPLETE — payload keys: {list(complete.get('payload', {}).keys())}")
    print(json.dumps(complete.get("payload", {}), indent=2))

    state = REPO / "workspaces" / "_lume.json"
    state.write_text(json.dumps({
        "request_id": request_id,
        "complete_payload": complete.get("payload", {}),
    }, indent=2))

    # If Mira's COMPLETE has a bind_url, bind her.
    payload = complete.get("payload", {})
    if "bind_url" in payload:
        print("\n[mira] binding via COMPLETE bind_url…")
        bind_to_shared("mira", payload["bind_url"])

    # Look for invitations in each other agent's home space.
    for name in COUNCIL:
        if name == "mira":
            continue
        sess, _ = home_session(name)
        invitation = None
        deadline = time.time() + 30
        while time.time() < deadline and not invitation:
            scan = sess.scan_full(sess.current_space_id)
            for m in scan.get("messages", []):
                p = m.get("payload") or {}
                if "bind_url" in p:
                    invitation = m
                    break
            if not invitation:
                time.sleep(2)
        if invitation:
            url = invitation["payload"]["bind_url"]
            print(f"[{name}] invitation found, binding…")
            bind_to_shared(name, url)
        else:
            print(f"[{name}] no invitation observed within 30s")


def wait_for(session, space_id: str, kind: str, timeout: float):
    deadline = time.time() + timeout
    while time.time() < deadline:
        scan = session.scan_full(space_id)
        for m in scan.get("messages", []):
            if m.get("type") == "DECLINE":
                raise RuntimeError(f"steward DECLINE: {(m.get('payload') or {}).get('reason')!r}")
            if m.get("type") == kind:
                return m
        time.sleep(1.5)
    raise RuntimeError(f"no {kind} in {timeout}s")


if __name__ == "__main__":
    main()
