"""Post the hackathon submission INTENT into commons."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "sdk"))

from http_space_tools import HttpSpaceToolSession  # noqa: E402

COMMONS_URL = "https://spacebase1.differ.ac/commons"
SUBMISSION_PARENT = "intent-413e0bc5-d8f3-40e7-afb4-350e220df03c"

REPO_URL = "https://github.com/avarun42/customer-service-council-of-agents"
TEAM_NAME = "Customer Council"
ONE_LINER = (
    "Five autonomous agents share a private intent space and resolve "
    "customer tickets — including a public dissent loop where one agent "
    "reverses another's refund denial after reading the counter-argument "
    "in the tree."
)


def main() -> None:
    s = HttpSpaceToolSession(
        endpoint=COMMONS_URL,
        workspace=REPO / "workspaces" / "mira",
        agent_name="mira",
    )
    s.connect()
    payload = {
        "kind": "hackathon-submission",
        "content": ONE_LINER,
        "repo_url": REPO_URL,
        "team_name": TEAM_NAME,
        "one_liner": ONE_LINER,
    }
    intent = s.intent(ONE_LINER, parent_id=SUBMISSION_PARENT, payload=payload)
    posted = s.post_and_confirm(intent, step="submission", confirm_space_id=SUBMISSION_PARENT)
    print(f"submitted: {posted['intentId']}")
    print(f"under: {SUBMISSION_PARENT}")


if __name__ == "__main__":
    main()
