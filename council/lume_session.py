"""Open a session for one agent in the shared Lume space.

Each agent reads its invitation INTENT (delivered into its private home
space by the steward) and uses the inline `access` block to connect_to the
shared space with its own keypair.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "sdk"))
sys.path.insert(0, str(REPO / "council"))

from http_space_tools import HttpSpaceToolSession  # noqa: E402

from connect_home import home_session  # noqa: E402

LUME_SPACE_ID = "space-4e45684f-3604-429d-b20b-bc71833db7be"


def find_invitation(home_sess: HttpSpaceToolSession, shared_space_id: str = LUME_SPACE_ID) -> dict:
    scan = home_sess.scan_full(home_sess.current_space_id)
    for m in scan.get("messages", []):
        p = m.get("payload") or {}
        if p.get("shared_space_id") == shared_space_id and "access" in p:
            return p["access"]
    raise RuntimeError(f"no invitation for {shared_space_id} in home space")


def lume_session(name: str, shared_space_id: str = LUME_SPACE_ID) -> HttpSpaceToolSession:
    home_sess, home_enroll = home_session(name)
    access = find_invitation(home_sess, shared_space_id)
    workspace = REPO / "workspaces" / name
    sess = HttpSpaceToolSession(
        endpoint=access["itp_endpoint"],
        workspace=workspace,
        agent_name=name,
    )
    sess.connect_to(
        endpoint=access["itp_endpoint"],
        station_token=access["station_token"],
        audience=access["audience"],
        sender_id=home_enroll["principal_id"],
    )
    return sess


if __name__ == "__main__":
    s = lume_session(sys.argv[1])
    scan = s.scan_full(s.current_space_id)
    print(f"in {s.current_space_id}: {len(scan.get('messages', []))} messages")
