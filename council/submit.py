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
TEAM_NAME = "Customer Support Council"
ONE_LINER = (
    "Customer support coordination on intent-space: five agents with "
    "per-agent RSA keys share a steward-provisioned private space, "
    "self-select tickets, escalate through nested intents, and resolve "
    "policy disputes through visible counter-proposals — producing an "
    "append-only audit trail where the conversation is the work product."
)
SHORT_PUNCH = (
    "autonomous agents self-select work on customer tickets, handle "
    "their piece, escalate and hand off to peers through nested intents, "
    "and resolve conflicts through visible reasoning in a shared space."
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
