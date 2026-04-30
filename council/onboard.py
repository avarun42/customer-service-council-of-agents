"""Sign up an agent to spacebase1 commons.

Each agent has its own workspace dir with its own RSA keypair, station token,
and principal id. This is the per-agent key requirement of the spec.

Usage: python3 council/onboard.py <agent_name>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "sdk"))

from http_space_tools import HttpSpaceToolSession  # noqa: E402

COMMONS_URL = "https://spacebase1.differ.ac/commons"


def onboard(agent_name: str) -> dict:
    workspace = REPO / "workspaces" / agent_name
    workspace.mkdir(parents=True, exist_ok=True)
    session = HttpSpaceToolSession(
        endpoint=COMMONS_URL,
        workspace=workspace,
        agent_name=agent_name,
    )
    enrollment = session.local_state.load_enrollment()
    if not enrollment:
        print(f"[{agent_name}] signing up to {COMMONS_URL}…")
        enrollment = session.signup(COMMONS_URL, handle=agent_name)
    else:
        print(f"[{agent_name}] already enrolled")
    session.connect()
    print(json.dumps({
        "agent": agent_name,
        "principal": session.agent_id,
        "endpoint": session.endpoint,
        "current_space": session.current_space_id,
        "declared_default": session.declared_default_space_id,
    }, indent=2))
    return enrollment


if __name__ == "__main__":
    onboard(sys.argv[1])
