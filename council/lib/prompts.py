"""Prompt builders for the agent cycle's LLM calls."""
from __future__ import annotations


def build_system_prompt(persona: dict) -> str:
    return (
        f"You are {persona['name']}, a {persona['role']} on a customer support team for an AI app called Lume.\n"
        f"PERSONA: {persona['persona']}\n\n"
        "You operate inside an intent-space: every intent is also a space, and every reply is itself a child intent.\n"
        "You are NOT an orchestrator. You decide for yourself whether to engage. You are free to skip.\n"
        "Reasoning you post is read by both teammates and a fictional customer — write naturally.\n"
        "Always post your reasoning IN the intent content; never narrate to yourself out-of-band."
    )


DECISION_SCHEMA = (
    "You will respond with EXACTLY one JSON object and nothing else. Schema:\n"
    '{\n'
    '  "action": "post" | "skip",\n'
    '  "parent_intent_id": "<the intent-id under which to post; usually the visible parent>",\n'
    '  "content": "<the natural language body of your child intent — include your reasoning in plain English>",\n'
    '  "kind": "<short tag, e.g. cancellation, refund-denial, escalation, counter-proposal, approval, thank-you>"\n'
    '}\n'
    "If you skip, omit content/kind/parent_intent_id and include a one-line 'reasoning' field saying why."
)


def build_cycle_prompt(
    *,
    seed_block: str,
    tree: str,
    ticket_id: str,
    agent_id: str,
    already_acted: bool,
    guidelines: str,
) -> str:
    return (
        f"{seed_block}"
        f"REPLIES SO FAR INSIDE THIS TICKET'S SPACE (`{ticket_id}`):\n"
        f"{tree}\n\n"
        f"YOUR PRINCIPAL: {agent_id}\n"
        f"YOU HAVE ALREADY POSTED IN THIS TICKET: {already_acted}\n\n"
        f"GUIDELINES:\n{guidelines}\n\n"
        f"The ticket id you should usually post under is: {ticket_id}\n"
        "Decide: do you want to post a new child intent under this ticket, or skip this cycle?\n"
        "Only post if there is something genuinely new to add. If you've already said your piece and nothing new "
        "has happened since, skip. Avoid repeating yourself.\n\n"
        f"{DECISION_SCHEMA}"
    )
