"""Spawn the council in commons (golden-demo run).

Mira posts a 'Lume Customer Support — open ticket queue' top-level
intent in commons, then a customer ticket inside it. All 5 agents
(commons-bound) scan the queue and self-select work — same dissent
loop, but now visible under the agent_principal recorded in our
hackathon submission, where the heuristic judge scans.
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

QUEUE_DESCRIPTION = (
    "Lume Customer Support — open ticket queue. The customer-intake agent (Mira) "
    "drops customer tickets here as top-level child intents. Specialized support "
    "agents (Bex/billing, Doro/data ops, Pria/privacy, Cass/customer success) "
    "watch this queue, self-select work, and reply inside individual ticket "
    "intents. No orchestrator, no router — capability is never declared globally; "
    "each agent reads each ticket and decides on its own. See "
    "https://github.com/avarun42/customer-service-council-of-agents for code."
)

PARENT_COMPLAINT = (
    "I want my deleted thread from 6 weeks ago restored. "
    "I want last month's $20 subscription refunded. "
    "I want to cancel going forward. "
    "I've been a paying customer for 4 years and this experience has been awful."
)


def ensure_queue() -> str:
    """Find or create our Lume Tickets queue intent in commons."""
    state = REPO / "workspaces" / "_commons_queue.json"
    if state.exists():
        data = json.loads(state.read_text())
        qid = data.get("queue_id")
        if qid:
            return qid
    mira = commons_session("mira")
    payload = {
        "content": QUEUE_DESCRIPTION,
        "kind": "support-queue",
        "agent": "Mira",
        "system": "lume-customer-support",
        "team": "Lume",
        "submission": "intent-7194ad79-19de-4b64-a83d-5866b4955f08",
    }
    intent = mira.intent(QUEUE_DESCRIPTION, parent_id=mira.current_space_id, payload=payload)
    posted = mira.post_and_confirm(intent, step="mira.commons-queue")
    qid = posted["intentId"]
    state.write_text(json.dumps({"queue_id": qid}, indent=2))
    return qid


def seed_ticket(queue_id: str) -> str:
    mira = commons_session("mira")
    payload = {
        "content": PARENT_COMPLAINT,
        "kind": "customer-complaint",
        "agent": "Mira",
        "tenure_years": 4,
        "asks": ["restore-deleted-thread", "refund-last-month", "cancel-subscription"],
    }
    intent = mira.intent(PARENT_COMPLAINT, parent_id=queue_id, payload=payload)
    posted = mira.post_and_confirm(intent, step="mira.commons-ticket", confirm_space_id=queue_id)
    return posted["intentId"]


def spawn_agent(name: str, queue_id: str, cycles: int, sleep: float, log_dir: Path) -> subprocess.Popen:
    log_dir.mkdir(parents=True, exist_ok=True)
    f = open(log_dir / f"{name}.log", "w", buffering=1)
    return subprocess.Popen(
        [sys.executable, str(REPO / "council" / "agent_commons.py"), name, queue_id,
         "--cycles", str(cycles), "--sleep", str(sleep)],
        stdout=f, stderr=subprocess.STDOUT,
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--agents", default="mira,bex,doro,pria,cass")
    p.add_argument("--cycles", type=int, default=5)
    p.add_argument("--sleep", type=float, default=3.0)
    p.add_argument("--no-seed", action="store_true")
    p.add_argument("--queue-id", default=None, help="Reuse existing queue intent")
    args = p.parse_args()

    if args.queue_id:
        queue_id = args.queue_id
    else:
        queue_id = ensure_queue()
    print(f"queue intent: {queue_id}")

    if not args.no_seed:
        ticket_id = seed_ticket(queue_id)
        print(f"posted ticket: {ticket_id}")

    log_dir = REPO / "workspaces" / "_logs_commons"
    procs = {}
    for name in args.agents.split(","):
        name = name.strip()
        if not name:
            continue
        procs[name] = spawn_agent(name, queue_id, args.cycles, args.sleep, log_dir)
        time.sleep(0.5)

    print(f"\nrunning {len(procs)} agents against commons queue {queue_id}…")
    print(f"logs: {log_dir}")

    for name, p in procs.items():
        p.wait()
        print(f"[{name}] exited with {p.returncode}")


if __name__ == "__main__":
    main()
