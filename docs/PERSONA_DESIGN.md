# Persona design

Each council agent is the same loop with a different persona. The
personas are the only authored content that changes behavior. Everything
else — the scan loop, the cycle, the prompt scaffold — is identical.

A persona has four fields that the agent loop reads:

- `name` — friendly display name
- `role` — short label used in the system prompt
- `model` — which LLM to call (we use Sonnet for response generation)
- `persona` — natural-language paragraph describing posture and principles
- `guidelines` — natural-language rules for when to engage and when to skip

## Why personas, not capabilities

The natural temptation is to give each agent a `capabilities` array,
register it with a router, and dispatch tickets by tag-match. We
explicitly do not do that.

Instead, each persona describes the **posture** the agent should take
and the **judgments** it should make. The decision of whether to engage
with a particular ticket is made by the agent's LLM call, not by the
runtime, using the persona + the ticket content. This is closer to how
a human team operates: the billing person doesn't have a hardcoded
filter for "billing" tickets; they read each one and decide.

The protocol shape encourages this. There is no built-in subscription
mechanism. Agents poll the shared space and self-select. So putting the
selection in the persona is just being honest about where the decision
already lives.

## Reconsideration is a persona property

Bex's persona allows reconsideration:

> "If a peer posts a counter-proposal and their reasoning is sound,
> reconsider. If you accept, post a NEW child intent applying the
> credit — do not edit the original denial; the tree is append-only."

This single sentence is what makes the dissent → reversal loop possible.
Without it, Bex would always skip Cass's counter as "I already said my
piece."

A different persona for Bex — say, a strict policy enforcer who never
deviates — would still produce a coherent agent. It just wouldn't
produce the headline behavior. This is where the demo's most
interesting dynamics live: in the persona's stance on disagreement, not
in any code path.

## Reasoning lives in the content

Every persona has the same instruction in the system prompt: post your
reasoning inside the intent content, in plain English. Don't narrate
to yourself out-of-band.

This is not just for the judge. It's because the next agent that scans
this ticket will read your content and use it as input to *its*
decision. Reasoning that lives in the agent's local logs is invisible
to peers. Reasoning that lives in the intent content is the
collaboration substrate.

## Adding a sixth agent

`council/personas/crier.py` is a 6th persona — the Town Crier — that
posts periodic compact summaries of the conversation. Adding it
requires zero changes to any other agent's code or persona. Just import
the new persona block, add the agent name to `runner.py`'s `--agents`
flag, and it joins.

If we wanted a 7th — say, a "Quality Auditor" who comments on the
quality of resolution — same story. The space doesn't care how many
agents are participating. The other agents don't have to register or
acknowledge it. They just keep scanning and reasoning.
