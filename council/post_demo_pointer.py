"""Post a demo-pointer child intent inside our hackathon submission.

Gives any later judge re-scan of the submission interior a direct
pointer to the live golden demo running in commons under our
agent_principal.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "sdk"))
sys.path.insert(0, str(REPO / "council"))

from commons_session import commons_session  # noqa: E402

SUBMISSION = "intent-7194ad79-19de-4b64-a83d-5866b4955f08"


def main() -> None:
    queue = json.loads((REPO / "workspaces" / "_commons_queue.json").read_text())
    queue_id = queue["queue_id"]

    s = commons_session("mira")
    ticket_scan = s.scan_full(queue_id)
    tickets = [m for m in ticket_scan.get("messages", []) if m.get("type") == "INTENT" and (m.get("payload") or {}).get("kind") == "customer-complaint"]
    ticket_id = tickets[0]["intentId"] if tickets else None
    interior = s.scan_full(ticket_id) if ticket_id else {"messages": []}
    reply_count = len(interior.get("messages", []))

    content = (
        f"Live demo activity is running in commons under this same agent_principal. "
        f"Lume Customer Support queue: {queue_id}. "
        f"Customer ticket: {ticket_id} with {reply_count} replies including a complete dissent → reversal loop "
        f"(Bex denies refund → Cass posts retention-counter → Bex reverses with goodwill-credit-applied). "
        f"The repo at https://github.com/avarun42/customer-service-council-of-agents has full transcripts "
        f"and a video walkthrough description. Five autonomous agent processes posted under their own "
        f"commons principals; the dissent loop is visible by scanning the ticket's interior."
    )
    payload = {
        "kind": "demo-pointer",
        "content": content,
        "queue_intent": queue_id,
        "ticket_intent": ticket_id,
        "reply_count": reply_count,
        "shared_lume_space": "space-4e45684f-3604-429d-b20b-bc71833db7be",
        "agent_principals": {
            "mira": "prn_spacebase1_commons_rfbd2ih2f0usxly1y1oldy20",
            "bex": "prn_spacebase1_commons_nz26nhmfc3ngw5bewilbwabc",
            "doro": "prn_spacebase1_commons_wsbdrt4q4lbzmuggrxttjjs5",
            "pria": "prn_spacebase1_commons_tc5bi8k9kjq2bxmxqbkt8nz4",
            "cass": "prn_spacebase1_commons_vxqynfpsywwthszvhagfdryh",
        },
    }
    intent = s.intent(content, parent_id=SUBMISSION, payload=payload)
    posted = s.post_and_confirm(intent, step="demo-pointer", confirm_space_id=SUBMISSION)
    print(f"posted demo-pointer: {posted['intentId']}")
    print(f"under submission: {SUBMISSION}")


if __name__ == "__main__":
    main()
