"""Council agent: scans a space, decides via LLM whether to post, posts reasoning into the tree.

Run one process per agent with its own workspace dir / per-agent keys.

Usage:
    python3 council/agent.py <agent_name> <parent_intent_id> [--cycles N] [--sleep S]

The agent only watches the *interior* of <parent_intent_id> — that is
spacebase1's "every intent is itself a space" model. Top-level discovery
of the parent ticket happens in the runner script.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "sdk"))
sys.path.insert(0, str(REPO / "council"))

from http_space_tools import HttpSpaceToolSession  # noqa: E402

from llm import call as llm_call  # noqa: E402
from lume_session import lume_session  # noqa: E402
from personas import PERSONAS  # noqa: E402


def short_id(s: str | None) -> str:
    if not s:
        return "?"
    return s.split("-")[-1][:8] if "-" in s else s[-12:]


def render_tree(messages: list[dict], my_principal: str, principal_to_name: dict[str, str]) -> str:
    """Render the visible tree as a compact textual log for the LLM."""
    lines = []
    for m in messages:
        kind = m.get("type", "?")
        sender = m.get("senderId", "?")
        who = principal_to_name.get(sender, short_id(sender))
        if sender == my_principal:
            who += " (you)"
        payload = m.get("payload") or {}
        content = payload.get("content") or payload.get("summary") or payload.get("reason") or json.dumps(payload, ensure_ascii=False)
        if len(content) > 600:
            content = content[:600] + "…"
        marker = ""
        if m.get("intentId"):
            marker = f" [{short_id(m['intentId'])}]"
        elif m.get("promiseId"):
            marker = f" [promise {short_id(m['promiseId'])}]"
        lines.append(f"- {kind} by {who}{marker}: {content}")
    return "\n".join(lines) if lines else "(empty)"


def parse_decision(text: str) -> dict:
    """Extract a JSON action from the LLM response."""
    # Try fenced JSON first
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except Exception:
            pass
    # Try last balanced brace block
    start = text.rfind("{")
    if start >= 0:
        candidate = text[start:]
        try:
            return json.loads(candidate)
        except Exception:
            pass
    return {"action": "skip", "reasoning": "could not parse LLM output"}


def find_seed_intent(session: HttpSpaceToolSession, intent_id: str, search_space: str) -> dict | None:
    """The seed intent that created `intent_id` as a space lives in its containing space."""
    try:
        scan = session.scan_full(search_space)
    except Exception:
        return None
    for m in scan.get("messages", []):
        if m.get("type") == "INTENT" and m.get("intentId") == intent_id:
            return m
    return None


def cycle_on_ticket(session: HttpSpaceToolSession, ticket_id: str, queue_id: str, persona: dict, principal_to_name: dict[str, str]) -> bool:
    """Consider one ticket: scan its interior, decide, post a reply if engaged."""
    seed = find_seed_intent(session, ticket_id, queue_id)
    full = session.scan_full(ticket_id)
    messages = full.get("messages", [])
    tree = render_tree(messages, session.agent_id, principal_to_name)
    seed_block = ""
    if seed:
        seed_who = principal_to_name.get(seed.get("senderId", ""), short_id(seed.get("senderId")))
        seed_content = (seed.get("payload") or {}).get("content") or ""
        seed_block = f"TICKET (parent intent, posted by {seed_who}):\n  {seed_content}\n\n"

    sender_ids_in_tree = {m.get("senderId") for m in messages}
    you_already_acted = session.agent_id in sender_ids_in_tree

    # Skip only if you've already posted here AND nothing has happened since.
    # We can't cheaply detect "since" — instead let the LLM decide. The
    # cycle limit caps any waste from over-engagement.
    if not seed:
        # Without a seed we have no idea what this ticket is about.
        return False
    seed_payload = (seed.get("payload") or {})
    seed_kind = seed_payload.get("kind", "")
    if persona.get("role") != "customer" and seed_kind not in ("customer-complaint", "support-ticket", ""):
        # Skip steward presence intents and other non-ticket nodes.
        return False

    system = (
        f"You are {persona['name']}, a {persona['role']} on a customer support team for an AI app called Lume.\n"
        f"PERSONA: {persona['persona']}\n\n"
        "You operate inside an intent-space: every intent is also a space, and every reply is itself a child intent.\n"
        "You are NOT an orchestrator. You decide for yourself whether to engage. You are free to skip.\n"
        "Reasoning you post is read by both teammates and a fictional customer — write naturally.\n"
        "Always post your reasoning IN the intent content; never narrate to yourself out-of-band."
    )

    rules = (
        "You will respond with EXACTLY one JSON object and nothing else. Schema:\n"
        '{\n'
        '  "action": "post" | "skip",\n'
        '  "parent_intent_id": "<the intent-id under which to post; usually the visible parent>",\n'
        '  "content": "<the natural language body of your child intent — include your reasoning in plain English>",\n'
        '  "kind": "<short tag, e.g. cancellation, refund-denial, escalation, counter-proposal, approval, thank-you>"\n'
        '}\n'
        "If you skip, omit content/kind/parent_intent_id and include a one-line 'reasoning' field saying why."
    )

    prompt = (
        f"{seed_block}"
        f"REPLIES SO FAR INSIDE THIS TICKET'S SPACE (`{ticket_id}`):\n"
        f"{tree}\n\n"
        f"YOUR PRINCIPAL: {session.agent_id}\n"
        f"YOU HAVE ALREADY POSTED IN THIS TICKET: {you_already_acted}\n\n"
        f"GUIDELINES:\n{persona['guidelines']}\n\n"
        f"The ticket id you should usually post under is: {ticket_id}\n"
        "Decide: do you want to post a new child intent under this ticket, or skip this cycle?\n"
        "Only post if there is something genuinely new to add. If you've already said your piece and nothing new "
        "has happened since, skip. Avoid repeating yourself.\n\n"
        f"{rules}"
    )

    print(f"[{persona['name']}] thinking on {short_id(ticket_id)} ({len(messages)} replies visible)…", flush=True)
    raw = llm_call(prompt, model=persona.get("model", "sonnet"), system=system, timeout=120)
    decision = parse_decision(raw)
    action = decision.get("action", "skip")
    print(f"[{persona['name']}] decision: {action} — {decision.get('kind') or decision.get('reasoning', '')[:80]}", flush=True)

    if action != "post":
        return False

    content = decision.get("content")
    if not content:
        return False
    target = decision.get("parent_intent_id") or ticket_id
    payload = {"content": content, "kind": decision.get("kind", persona.get("default_kind", "reply")), "agent": persona["name"]}
    msg = session.intent(content, parent_id=target, payload=payload)
    session.post(msg, step=f"{persona['name']}.post")
    print(f"[{persona['name']}] posted {short_id(msg['intentId'])} under {short_id(target)}", flush=True)
    return True


def cycle_on_queue(session: HttpSpaceToolSession, queue_id: str, persona: dict, principal_to_name: dict[str, str]) -> int:
    """Scan the queue for tickets and consider engaging with each one. Returns count posted."""
    queue_scan = session.scan_full(queue_id)
    tickets = [m for m in queue_scan.get("messages", []) if m.get("type") == "INTENT"]
    posted = 0
    for ticket in tickets:
        ticket_id = ticket.get("intentId")
        if not ticket_id:
            continue
        try:
            if cycle_on_ticket(session, ticket_id, queue_id, persona, principal_to_name):
                posted += 1
        except Exception as e:
            print(f"[{persona['name']}] error on {short_id(ticket_id)}: {e}", flush=True)
    return posted


def build_principal_map() -> dict[str, str]:
    """Read each workspace's enrollment files to build principal_id -> friendly name.

    We map BOTH the commons principal and the home-space principal so the LLM
    sees friendly names for any sender id that appears in scans, regardless of
    which audience the agent is currently bound to.
    """
    mapping: dict[str, str] = {}
    ws_dir = REPO / "workspaces"
    if not ws_dir.exists():
        return mapping
    for d in ws_dir.iterdir():
        if not d.is_dir():
            continue
        for fname in ("station-enrollment.json", "home-enrollment.json"):
            enrollment = d / ".intent-space" / "state" / fname
            if enrollment.exists():
                try:
                    data = json.loads(enrollment.read_text())
                    pid = data.get("principal_id")
                    if pid:
                        mapping[pid] = d.name
                except Exception:
                    pass
    return mapping


def run_agent(agent_name: str, queue_id: str, cycles: int, sleep: float) -> None:
    persona = PERSONAS[agent_name]
    session = lume_session(agent_name)
    principal_to_name = build_principal_map()
    for i in range(cycles):
        try:
            cycle_on_queue(session, queue_id, persona, principal_to_name)
        except Exception as e:
            print(f"[{persona['name']}] cycle error: {e}", flush=True)
        # Jitter so concurrent agents don't lock-step
        delay = sleep + random.uniform(-0.5, 1.5)
        time.sleep(max(1.0, delay))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("agent_name")
    p.add_argument("queue_id", help="The Lume Tickets queue space (a top-level intent in commons)")
    p.add_argument("--cycles", type=int, default=4)
    p.add_argument("--sleep", type=float, default=4.0)
    args = p.parse_args()
    run_agent(args.agent_name, args.queue_id, args.cycles, args.sleep)


if __name__ == "__main__":
    main()
