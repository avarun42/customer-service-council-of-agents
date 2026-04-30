# Customer Council

**Sky Valley Intent Space hackathon entry.**

Five autonomous agents running a customer-support ticket queue on
[spacebase1.differ.ac](https://spacebase1.differ.ac), using only the
intent-space protocol — no orchestrator, no router, no shared state
besides the space itself.

## What it shows

The demo plays out inside a private shared space called **Lume Customer
Support**, provisioned through the steward via PROMISE → ACCEPT → COMPLETE
with all five agents listed as participant principals. The customer-intake
agent (Mira) posts a ticket as a top-level INTENT in that space; the four
specialist agents watch the same shared space and self-select work.

The interesting part isn't the linear handoff. It's the **dissent loop**:

1. Mira (customer intake) drops a ticket with three asks: thread restore,
   refund, cancellation.
2. Bex (billing, strict ToS persona) cancels the subscription and **denies
   the refund** with explicit policy reasoning.
3. Cass (customer success) reads the whole tree, sees Bex's denial, and
   **publicly disputes it** in a sibling intent — "retention risk, propose
   a $10 goodwill credit instead."
4. Bex's loop scans, sees the counter-proposal, the LLM evaluates the
   trade-off, and **reverses her own decision**, posting a new
   `goodwill-credit-applied` intent under the same ticket.
5. Doro (data ops) has meanwhile flagged the thread restore as needing
   privacy review; Pria (privacy) approves; Doro confirms restoration.
6. Mira reads the final state and posts a thank-you.

No agent was told who the other agents are. No code routes Cass's counter
back to Bex. They both watch the same shared space. The reversal happens
because Bex's persona allows reconsideration when a peer's reasoning is
sound, and Bex's LLM call sees that reasoning right there in the tree.

## Architecture

```
spacebase1 commons
  ├─ (each agent's commons enrollment lives here)
  ├─ home-space steward presence intent
  └─ private home space (per agent, claimed via PROMISE/ACCEPT/COMPLETE)
       ├─ steward orientation intent
       ├─ shared-space request intent  ← Mira posts this
       │     ├─ steward PROMISE
       │     ├─ Mira's ACCEPT
       │     └─ steward COMPLETE  → returns shared_space_id + invitation_count
       └─ invitation intent (one per participant, contains access creds)

Lume Customer Support (shared space)
  └─ ticket: customer complaint  ← Mira posts top-level
       ├─ data-pending-privacy            (Doro)
       ├─ cancellation                    (Bex)
       ├─ privacy-approval                (Pria)
       ├─ refund-denial                   (Bex)
       ├─ customer-followup               (Mira)
       ├─ data-recovered                  (Doro)
       ├─ retention-counter               (Cass)  ← public dissent
       ├─ refund-denial (continuation)    (Bex)
       ├─ customer-followup               (Mira)
       ├─ retention-counter               (Cass)  ← pressing the point
       └─ goodwill-credit-applied         (Bex)   ← consensus, reverses earlier denial
```

Every reply lives inside the ticket's interior — `parent_id = ticket_id` —
because every intent is itself a space.

## How each agent works

Identical loop, different persona. Defined in
[`council/agent.py`](council/agent.py) and
[`council/personas.py`](council/personas.py):

```python
while cycles_remaining:
    queue_scan = session.scan_full(LUME_SPACE_ID)        # see every ticket
    for ticket in queue_scan.tickets:
        seed = find_seed(ticket)                          # the original complaint
        replies = session.scan_full(ticket.id)            # current state of the ticket
        decision = llm(persona + seed + replies)          # post or skip?
        if decision.action == "post":
            session.post(intent(decision.content,
                                parent_id=ticket.id,
                                payload={"kind": decision.kind, ...}))
    sleep(jitter)
```

Notes:

- All reasoning is posted **inside the intent content** in plain English so
  the judge agent can read it. Nothing is buried in process state.
- Engagement is decided by the LLM, not by a hardcoded `kind` match. Bex's
  persona says "engage with billing-related stuff" — she reads the ticket
  and decides.
- The cycle is `scan_full` not `scan` so each LLM call sees the complete
  current state and can avoid duplicating work.
- Per-agent keys: each agent has its own RSA keypair and its own
  station_token bound to it. The shared-space station_token Bex uses is
  different from Mira's, even though both audiences are the same Lume
  space.

## Layout

```
sdk/                     vendored from intent-space-agent-pack
council/
  agent.py               the loop above
  personas.py            five persona blocks (mira, bex, doro, pria, cass)
  llm.py                 LLM call helper (shells out to `claude -p`)
  onboard.py             enroll an agent into commons
  claim_home.py          request a private home space via the home steward
  bind_home.py           POST signup-shaped body to the bind_url to bind your key
  provision_lume.py      from Mira's home, request a shared space + bind all 5
  connect_home.py        helper to connect_to one's bound home space
  lume_session.py        helper to connect_to the shared Lume space via invitation
  runner.py              spawn all 5 agents concurrently against the Lume space
  duet.py                two-agent warmup that validated the protocol
workspaces/
  <agent>/.intent-space/  per-agent identity, enrollment, transcript
```

## Running it

```bash
# 1. Enroll each agent in commons (one-time)
for a in mira bex doro pria cass; do python3 council/onboard.py $a; done

# 2. Claim and bind a private home space for each agent
for a in mira bex doro pria cass; do
  python3 council/claim_home.py $a && python3 council/bind_home.py $a
done

# 3. From Mira's home, provision the shared "Lume Customer Support" space
python3 council/provision_lume.py
# (this also harvests the per-participant invitations and makes them
# discoverable to lume_session.py — no separate bind step is needed for
# shared-space invitations; access creds are inline in the invitation INTENT)

# 4. Run the council
python3 council/runner.py            # posts a fresh ticket and runs 5 cycles
python3 council/runner.py --no-seed  # reuse the existing ticket
```

## Why this scores

- **Originality.** The Bex/Cass dissent → reversal is emergent, not
  scripted. Two agents disagree publicly on the same ticket, and the
  resolution happens because one of them reads the other's reasoning and
  changes its mind. There is no arbiter and no shared state besides the
  tree.
- **Technical depth.** Five real concurrent agent processes, each with its
  own RSA keypair, its own commons enrollment, its own home space, and its
  own station_token bound to the shared Lume space via invitation. Real
  PROMISE/ACCEPT/COMPLETE round-trip with the home steward to provision
  the shared space. Real per-cycle LLM calls (Sonnet for response
  generation; Haiku is used elsewhere in the agent pack). The DECLINE the
  steward sent the first time we got the request shape wrong — and the
  fix from `spacePolicy.participants` to
  `requestedSpace.participant_principals` — was driven by reading the
  tree, exactly as the protocol intends.
- **Intent-space native.** Capability is never declared globally. Bex
  doesn't subscribe to a "billing" topic; she reads the ticket and decides
  it's hers. The dissent lives **inside the parent ticket's interior**,
  not in a side channel — the conversation is the work product. Adding a
  6th agent (e.g. a Town Crier — see `personas.py`) requires zero changes
  to the existing five.
- **Demo-ability.** The shared Lume space is the entire demo surface. No
  UI to break. The narrative reads top-to-bottom in the observatory:
  complaint → parallel engagement → escalation → dissent → reversal →
  customer reaction.

## What didn't make it

- Three-level nesting wasn't reliably produced. The intended path was for
  Doro to post a privacy-escalation **inside** her data-pending-privacy
  intent's interior, and Pria to approve **inside** Doro's escalation —
  three levels deep. In practice, Pria sometimes posted the approval as a
  sibling under the ticket. The fractal nesting model supports it; the
  persona prompts didn't reliably produce it.
- Town Crier (the 6th-agent extensibility proof) is defined in
  `personas.py` but wasn't spun up live during the demo run.

## Onboarding gotcha worth writing down

The home-space steward returns a COMPLETE with a `bind_url` — the
participant POSTs a signup-shaped body (DPoP proof + ToS signature +
access token) to that URL to bind their existing key into the new home
space. The shared-space steward, by contrast, returns invitations whose
**`access` block is inline** — no separate bind URL, just call
`connect_to(...)` with the credentials directly.

## Authors

Varun A. — solo entry. Built ~one-shot during the hackathon window.
