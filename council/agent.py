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
from personas import PERSONAS  # noqa: E402

COMMONS_URL = "https://spacebase1.differ.ac/commons"


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


def cycle(session: HttpSpaceToolSession, parent_id: str, persona: dict, principal_to_name: dict[str, str]) -> bool:
    """Run one observe-decide-post cycle. Returns True if something was posted."""
    full = session.scan_full(parent_id)
    messages = full.get("messages", [])
    tree = render_tree(messages, session.agent_id, principal_to_name)

    sender_ids_in_tree = {m.get("senderId") for m in messages}
    you_already_acted = session.agent_id in sender_ids_in_tree

    other_intents = [m for m in messages if m.get("type") == "INTENT" and m.get("senderId") != session.agent_id]
    if not other_intents and persona.get("role") != "customer":
        # Nothing to react to yet, and we're not the seeder.
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
        f"VISIBLE PARENT INTENT (this is the customer ticket — its space id is `{parent_id}`):\n"
        f"{tree}\n\n"
        f"YOUR PRINCIPAL: {session.agent_id}\n"
        f"YOU HAVE ALREADY POSTED IN THIS SPACE: {you_already_acted}\n\n"
        f"GUIDELINES:\n{persona['guidelines']}\n\n"
        "Decide: do you want to post a new child intent under this customer ticket, or skip this cycle?\n"
        "Only post if there is something genuinely new to add. If you've already said your piece and nothing new "
        "has happened since, skip. Avoid repeating yourself.\n\n"
        f"{rules}"
    )

    print(f"[{persona['name']}] thinking ({len(messages)} messages visible)…", flush=True)
    raw = llm_call(prompt, model=persona.get("model", "sonnet"), system=system, timeout=120)
    decision = parse_decision(raw)
    action = decision.get("action", "skip")
    print(f"[{persona['name']}] decision: {action} — {decision.get('kind') or decision.get('reasoning', '')[:80]}", flush=True)

    if action != "post":
        return False

    content = decision.get("content")
    if not content:
        return False
    target = decision.get("parent_intent_id") or parent_id
    payload = {"content": content, "kind": decision.get("kind", persona.get("default_kind", "reply")), "agent": persona["name"]}
    msg = session.intent(content, parent_id=target, payload=payload)
    session.post(msg, step=f"{persona['name']}.post")
    print(f"[{persona['name']}] posted {short_id(msg['intentId'])} under {short_id(target)}", flush=True)
    return True


def build_principal_map() -> dict[str, str]:
    """Read each workspace's enrollment file to build principal_id -> friendly name."""
    mapping: dict[str, str] = {}
    ws_dir = REPO / "workspaces"
    if not ws_dir.exists():
        return mapping
    for d in ws_dir.iterdir():
        if not d.is_dir():
            continue
        enrollment = d / ".intent-space" / "state" / "station-enrollment.json"
        if enrollment.exists():
            try:
                data = json.loads(enrollment.read_text())
                pid = data.get("principal_id")
                if pid:
                    mapping[pid] = d.name
            except Exception:
                pass
    return mapping


def run_agent(agent_name: str, parent_id: str, cycles: int, sleep: float) -> None:
    persona = PERSONAS[agent_name]
    session = HttpSpaceToolSession(
        endpoint=COMMONS_URL,
        workspace=REPO / "workspaces" / agent_name,
        agent_name=agent_name,
    )
    session.connect()
    principal_to_name = build_principal_map()
    for i in range(cycles):
        try:
            posted = cycle(session, parent_id, persona, principal_to_name)
        except Exception as e:
            print(f"[{persona['name']}] cycle error: {e}", flush=True)
            posted = False
        # Jitter so concurrent agents don't lock-step
        delay = sleep + random.uniform(-0.5, 1.5)
        time.sleep(max(1.0, delay))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("agent_name")
    p.add_argument("parent_id")
    p.add_argument("--cycles", type=int, default=4)
    p.add_argument("--sleep", type=float, default=4.0)
    args = p.parse_args()
    run_agent(args.agent_name, args.parent_id, args.cycles, args.sleep)


if __name__ == "__main__":
    main()
