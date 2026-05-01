"""Open a session for one agent directly in commons.

Each agent's station-enrollment.json already has the credentials for
commons — no invitation dance needed. This mirrors lume_session() but
skips the home-space lookup.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "sdk"))

from http_space_tools import HttpSpaceToolSession  # noqa: E402


def commons_session(name: str) -> HttpSpaceToolSession:
    workspace = REPO / "workspaces" / name
    enrollment = json.loads(
        (workspace / ".intent-space" / "state" / "station-enrollment.json").read_text()
    )
    sess = HttpSpaceToolSession(
        endpoint=enrollment["itp_endpoint"],
        workspace=workspace,
        agent_name=name,
    )
    sess.connect_to(
        endpoint=enrollment["itp_endpoint"],
        station_token=enrollment["station_token"],
        audience=enrollment["station_audience"],
        sender_id=enrollment["principal_id"],
    )
    return sess


if __name__ == "__main__":
    s = commons_session(sys.argv[1])
    scan = s.scan_full(s.current_space_id)
    print(f"in {s.current_space_id}: {len(scan.get('messages', []))} messages")
