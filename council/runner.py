"""Spawn the council: post the parent complaint, then run all agents concurrently.

This is intentionally NOT an orchestrator — it just kicks off independent
agent processes that share visibility through the commons. Each agent
decides on its own whether to engage.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "sdk"))

from http_space_tools import HttpSpaceToolSession  # noqa: E402

COMMONS_URL = "https://spacebase1.differ.ac/commons"

PARENT_COMPLAINT = (
    "I want my deleted thread from 6 weeks ago restored. "
    "I want last month's $20 subscription refunded. "
    "I want to cancel going forward. "
    "I've been a paying customer for 4 years and this experience has been awful."
)


def seed_complaint() -> str:
    session = HttpSpaceToolSession(
        endpoint=COMMONS_URL,
        workspace=REPO / "workspaces" / "mira",
        agent_name="mira",
    )
    session.connect()
    payload = {
        "content": PARENT_COMPLAINT,
        "kind": "customer-complaint",
        "agent": "Mira",
        "tenure_years": 4,
        "asks": ["restore-deleted-thread", "refund-last-month", "cancel-subscription"],
    }
    intent = session.intent(PARENT_COMPLAINT, parent_id=session.current_space_id, payload=payload)
    posted = session.post_and_confirm(intent, step="mira.parent-complaint")
    return posted["intentId"]


def spawn_agent(name: str, parent_id: str, cycles: int, sleep: float, log_dir: Path) -> subprocess.Popen:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{name}.log"
    f = open(log_file, "w", buffering=1)
    return subprocess.Popen(
        [sys.executable, str(REPO / "council" / "agent.py"), name, parent_id,
         "--cycles", str(cycles), "--sleep", str(sleep)],
        stdout=f, stderr=subprocess.STDOUT,
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--agents", default="mira,bex,doro,pria,cass")
    p.add_argument("--cycles", type=int, default=5)
    p.add_argument("--sleep", type=float, default=4.0)
    p.add_argument("--parent-id", default=None, help="Reuse an existing parent intent")
    args = p.parse_args()

    if args.parent_id:
        parent_id = args.parent_id
        print(f"reusing existing parent: {parent_id}")
    else:
        parent_id = seed_complaint()
        print(f"posted parent complaint: {parent_id}")

    log_dir = REPO / "workspaces" / "_logs"
    procs = {}
    for name in args.agents.split(","):
        name = name.strip()
        if not name:
            continue
        procs[name] = spawn_agent(name, parent_id, args.cycles, args.sleep, log_dir)
        time.sleep(0.5)  # mild stagger so they don't all hit the API at once

    print(f"\nrunning {len(procs)} agents against {parent_id}…")
    print(f"watch live: https://spacebase1.differ.ac/?space={parent_id}")
    print(f"logs: {log_dir}")

    for name, p in procs.items():
        p.wait()
        print(f"[{name}] exited with {p.returncode}")

    state = {"parent_id": parent_id}
    (REPO / "workspaces" / "_state.json").write_text(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
