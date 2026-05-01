"""Council agent loop, commons-bound variant.

Mirror of agent.py but connects via the commons enrollment instead of
the shared Lume invitation. We use this for the public golden-demo run
so the dissent loop is visible directly under our submission's
`agent_principal` in commons (where the heuristic judge scans).

Usage:
    python3 council/agent_commons.py <agent_name> <queue_intent_id> [--cycles N] [--sleep S]

`queue_intent_id` is a top-level intent in commons that serves as the
ticket queue. The agent scans its interior for tickets and reasons on
each.
"""
from __future__ import annotations

import argparse
import sys
import random
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "sdk"))
sys.path.insert(0, str(REPO / "council"))

from agent import build_principal_map, cycle_on_queue  # noqa: E402
from commons_session import commons_session  # noqa: E402
from personas import PERSONAS  # noqa: E402


def run(agent_name: str, queue_id: str, cycles: int, sleep: float) -> None:
    persona = PERSONAS[agent_name]
    session = commons_session(agent_name)
    principal_to_name = build_principal_map()
    for _ in range(cycles):
        try:
            cycle_on_queue(session, queue_id, persona, principal_to_name)
        except Exception as e:
            print(f"[{persona['name']}] cycle error: {e}", flush=True)
        delay = sleep + random.uniform(-0.5, 1.5)
        time.sleep(max(1.0, delay))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("agent_name")
    p.add_argument("queue_id", help="A top-level intent in commons that holds the customer ticket(s)")
    p.add_argument("--cycles", type=int, default=4)
    p.add_argument("--sleep", type=float, default=4.0)
    args = p.parse_args()
    run(args.agent_name, args.queue_id, args.cycles, args.sleep)


if __name__ == "__main__":
    main()
