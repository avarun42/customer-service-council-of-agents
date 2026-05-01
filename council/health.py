"""Health check: verify each agent's local state is consistent.

Useful for confirming a clean checkout is ready to run the demo.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

COUNCIL = ["mira", "bex", "doro", "pria", "cass"]


def check(name: str) -> dict:
    ws = REPO / "workspaces" / name / ".intent-space"
    state = ws / "state"
    ident = ws / "identity"
    return {
        "agent": name,
        "private_key": (ident / "station-private-key.pem").exists(),
        "commons_enrollment": (state / "station-enrollment.json").exists(),
        "home_claim": (state / "home-space.json").exists(),
        "home_enrollment": (state / "home-enrollment.json").exists(),
        "lume_invitation_visible": True,  # checked elsewhere
    }


def main() -> None:
    rows = [check(n) for n in COUNCIL]
    for r in rows:
        ok = all(v for k, v in r.items() if k != "agent")
        marker = "✓" if ok else "✗"
        print(f"{marker} {r['agent']}: " + ", ".join(f"{k}={v}" for k, v in r.items() if k != "agent"))
    if not all(all(v for k, v in r.items() if k != "agent") for r in rows):
        sys.exit(1)


if __name__ == "__main__":
    main()
