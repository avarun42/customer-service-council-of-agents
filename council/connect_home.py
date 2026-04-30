"""Connect to an agent's already-bound home space and return the session.

Reuse this from other modules so we don't need to re-bind.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "sdk"))

from http_space_tools import HttpSpaceToolSession  # noqa: E402

COMMONS_URL = "https://spacebase1.differ.ac/commons"


def home_session(name: str) -> tuple[HttpSpaceToolSession, dict]:
    workspace = REPO / "workspaces" / name
    home = json.loads((workspace / ".intent-space" / "state" / "home-enrollment.json").read_text())
    session = HttpSpaceToolSession(
        endpoint=home["itp_endpoint"],
        workspace=workspace,
        agent_name=name,
    )
    session.connect_to(
        endpoint=home["itp_endpoint"],
        station_token=home["station_token"],
        audience=home["station_audience"],
        sender_id=home["principal_id"],
    )
    return session, home


if __name__ == "__main__":
    s, h = home_session(sys.argv[1])
    scan = s.scan_full(s.current_space_id)
    print(f"home: {s.current_space_id}, messages: {len(scan.get('messages', []))}")
