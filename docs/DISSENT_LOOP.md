# The dissent loop

This is the headline emergent behavior of the council and the part most
worth understanding.

## What happens, in plain English

A customer files a ticket with three asks: restore a deleted thread,
refund last month, cancel going forward. Bex (billing) reads the ticket
and applies policy: she cancels the subscription effective end-of-period
(reply #2), and separately denies the refund per ToS (reply #4).

Cass (customer success) reads the same tree. She doesn't have authority
over Bex. She doesn't talk to Bex through any side channel. She just
reads the visible state and decides Bex's denial creates retention risk
that outweighs the policy upside. So she posts a sibling reply (#7) —
`retention-counter` — explicitly disagreeing with Bex by name and
proposing a $10 goodwill credit instead.

Bex's loop scans the ticket again on its next cycle. The new state now
contains Cass's counter-argument. Bex's persona allows reconsideration
when a peer's reasoning is sound. The LLM call evaluates Cass's argument
against Bex's own prior reasoning. The result: Bex posts reply #11 —
`goodwill-credit-applied` — reversing her earlier denial and naming the
intent that changed her mind.

That sequence — disagree publicly, then reach consensus by one party
moving — happens with no orchestrator. The whole loop is mediated by
the tree.

## What makes it actually work

Three things have to be true simultaneously:

1. **Both agents read the same shared state.** They both poll the same
   shared Lume space; they both call `scan_full(ticket_id)`; they both
   see the entire conversation each cycle, including each other's posts.
2. **Reasoning is in the content.** Cass's `retention-counter` doesn't
   just say "I disagree." It includes her actual argument:
   tenure, churn risk, comparative cost. Bex's LLM has something to
   evaluate, not just a flag.
3. **Personas allow reconsideration.** Bex isn't dogmatic. Her persona
   block in `council/personas.py` says: *"If a peer posts a
   counter-proposal and their reasoning is sound, reconsider. If you
   accept, post a NEW child intent applying the credit — do not edit
   the original denial; the tree is append-only."* This sentence is
   what makes the reversal possible. Without it, Bex would skip Cass's
   counter on every subsequent cycle.

## What this would look like in a non-intent-space system

In a triage-then-dispatch system:

- A router decides Bex owns the refund decision. The customer's ticket
  is split into sub-tickets. Bex's sub-ticket is closed once she denies.
  Cass never sees Bex's reasoning unless someone explicitly fans it out
  to her.
- If Cass *does* want to dispute, she has to call a separate "escalate"
  workflow. That workflow probably reopens Bex's sub-ticket via an
  approval request. Bex sees an approval-request notification, not the
  reasoning behind it.
- The reversal, if it happens, is a state machine transition on the
  sub-ticket. The audit trail is "approval received" and "decision
  changed" — not Bex's reasoning, Cass's reasoning, and Bex's revised
  reasoning, all readable side-by-side.

In intent space, it's just intents. The reversal is itself an intent
with stated reasoning. The whole disagreement is a tree, not a state
diagram.

## Verifiable in the live demo

Open the Lume space:

https://spacebase1.differ.ac/observatory#origin=https%3A%2F%2Fspacebase1.differ.ac&space=space-4e45684f-3604-429d-b20b-bc71833db7be&token=SXmXFjbjKR-0t4n1AsK4S23o2_b4CHW5EvHa4xqwEZM

Click into the customer ticket. Read the 11 child intents in order.
Reply #4 is the denial. Reply #7 is Cass's counter. Reply #11 is Bex's
reversal. The reasoning in each is verbatim what the agent's LLM
produced — no edits, no post-processing.
