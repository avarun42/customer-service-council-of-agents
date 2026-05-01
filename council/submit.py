"""Post the hackathon submission INTENT into commons.

Per hack.memetic.software submission spec, payload requires:
  kind, event, repo_url, team_name, agent_principal, one_liner.

content must be: "Submission: <team name> — <one-line description>".
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "sdk"))

from http_space_tools import HttpSpaceToolSession  # noqa: E402

COMMONS_URL = "https://spacebase1.differ.ac/commons"
SUBMISSION_PARENT = "intent-413e0bc5-d8f3-40e7-afb4-350e220df03c"
EVENT = "spacebase1-hackathon-2026"

REPO_URL = "https://github.com/avarun42/customer-service-council-of-agents"
TEAM_NAME = "Lume"
ONE_LINER = (
    "A multi-agent customer support coordinator where specialized agents "
    "(billing, data ops, privacy, retention) share an intent-space "
    "ticket queue: each agent self-selects work on incoming tickets, "
    "escalations and handoffs happen through nested intents, and "
    "disagreements between agents (e.g. policy vs. retention) get "
    "resolved by public counter-proposals that peers re-evaluate against "
    "— no central router, no fixed assignments."
)
SHORT_PUNCH = (
    "five autonomous agents resolve customer tickets through public "
    "dissent and consensus."
)


def main() -> None:
    s = HttpSpaceToolSession(
        endpoint=COMMONS_URL,
        workspace=REPO / "workspaces" / "mira",
        agent_name="mira",
    )
    s.connect()
    enrollment = json.loads((REPO / "workspaces" / "mira" / ".intent-space" / "state" / "station-enrollment.json").read_text())
    agent_principal = enrollment["principal_id"]

    content = f"Submission: {TEAM_NAME} — {SHORT_PUNCH}"
    payload = {
        "kind": "hackathon-submission",
        "event": EVENT,
        "repo_url": REPO_URL,
        "team_name": TEAM_NAME,
        "agent_principal": agent_principal,
        "one_liner": ONE_LINER,
        "content": content,
    }
    intent = s.intent(content, parent_id=SUBMISSION_PARENT, payload=payload)
    posted = s.post_and_confirm(intent, step="submission", confirm_space_id=SUBMISSION_PARENT)
    print(f"submitted: {posted['intentId']}")
    print(f"under: {SUBMISSION_PARENT}")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
