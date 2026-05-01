"""Spawn the council directly inside commons.

Mira posts the customer ticket as a top-level INTENT (parent_id = "commons"),
then all 5 agents run against commons as their queue. The dissent loop is
visible under our submission's agent_principal, which is what the heuristic
judge scans.
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
sys.path.insert(0, str(REPO / "council"))

from commons_session import commons_session  # noqa: E402

PARENT_COMPLAINT = (
    "I want my deleted thread from 6 weeks ago restored. "
    "I want last month's $20 subscription refunded. "
    "I want to cancel going forward. "
    "I've been a paying customer for 4 years and this experience has been awful."
)


def seed_complaint() -> str:
    """Mira posts a ticket as a top-level INTENT inside commons."""
    mira = commons_session("mira")
    payload = {
        "content": PARENT_COMPLAINT,
        "kind": "customer-complaint",
        "agent": "Mira",
        "tenure_years": 4,
        "asks": ["restore-deleted-thread", "refund-last-month", "cancel-subscription"],
    }
    intent = mira.intent(PARENT_COMPLAINT, parent_id="commons", payload=payload)
    posted = mira.post_and_confirm(intent, step="mira.ticket", confirm_space_id="commons")
    return posted["intentId"]


def spawn_agent(name: str, parent_id: str, cycles: int, sleep: float, log_dir: Path) -> subprocess.Popen:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{name}.commons.log"
    f = open(log_file, "w", buffering=1)
    return subprocess.Popen(
        [sys.executable, str(REPO / "council" / "agent.py"), name, parent_id,
         "--cycles", str(cycles), "--sleep", str(sleep), "--commons"],
        stdout=f, stderr=subprocess.STDOUT,
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--agents", default="mira,bex,doro,pria,cass")
    p.add_argument("--cycles", type=int, default=5)
    p.add_argument("--sleep", type=float, default=4.0)
    p.add_argument("--no-seed", action="store_true", help="Don't post a new ticket — agents scan existing commons")
    args = p.parse_args()

    if not args.no_seed:
        ticket_id = seed_complaint()
        print(f"posted ticket into commons: {ticket_id}")

    log_dir = REPO / "workspaces" / "_logs"
    procs = {}
    for name in args.agents.split(","):
        name = name.strip()
        if not name:
            continue
        procs[name] = spawn_agent(name, "commons", args.cycles, args.sleep, log_dir)
        time.sleep(0.5)

    print(f"\nrunning {len(procs)} agents against commons…")
    print(f"logs: {log_dir}")

    for name, proc in procs.items():
        proc.wait()
        print(f"[{name}] exited with {proc.returncode}")


if __name__ == "__main__":
    main()
