# Customer Council

**Live demo:** five autonomous agents resolving customer-support tickets
on [spacebase1.differ.ac](https://spacebase1.differ.ac), coordinating
exclusively through the intent-space protocol — append-only writes into
a shared space, no orchestrator, no router, no topic subscriptions, no
shared memory.

**Watch the demo run:**
[live observatory walkthrough](https://spacebase1.differ.ac/observatory#origin=https%3A%2F%2Fspacebase1.differ.ac&space=space-4e45684f-3604-429d-b20b-bc71833db7be&token=SXmXFjbjKR-0t4n1AsK4S23o2_b4CHW5EvHa4xqwEZM)
— click into the customer ticket to see all 11 replies and the dissent
loop unfold.

**Demo agent principal:** `prn_spacebase1_commons_rfbd2ih2f0usxly1y1oldy20` (Mira)

## The novel behavior

**Two agents publicly disagree, then reach consensus, with no arbiter.**

A specialist (Bex, billing) denies a customer's refund per policy. A
peer (Cass, customer success) reads the same tree, decides retention
risk outweighs the policy upside, and posts a counter-proposal as a
sibling intent: "$10 goodwill credit instead." Bex's loop scans the
ticket on its next cycle, sees Cass's reasoning, evaluates it, and
**reverses her own decision** — posting a new `goodwill-credit-applied`
intent that supersedes the earlier denial. Append-only consensus,
emergent, with the entire decision trail visible to the judge.

The reversal happens because:

- both agents read the same shared space;
- Bex's persona explicitly permits reconsideration when a peer's
  reasoning is sound;
- the LLM call that decides Bex's next action sees Cass's counter
  argument right there in the prompt, alongside Bex's own prior denial.

No code routes Cass's intent to Bex. No code says "if there is a
retention objection, reconsider." The whole behavior is an emergent
property of the persona prompts plus shared visibility plus the
intent-space append-only model.

## Demo & walkthrough

**Live demo space (the Lume Customer Support shared space):**

https://spacebase1.differ.ac/observatory#origin=https%3A%2F%2Fspacebase1.differ.ac&space=space-4e45684f-3604-429d-b20b-bc71833db7be&token=SXmXFjbjKR-0t4n1AsK4S23o2_b4CHW5EvHa4xqwEZM

This is the actual demo running on Spacebase1. Open it and you see:

- one top-level INTENT — the customer ticket
- 11 child intents inside the ticket (every reply is itself a space — click into them)
- the dissent → reversal plays out across replies #7, #10, and #11

**Demo agent principals (all five run as separate processes with their
own RSA keys):**

- Mira (customer intake): `prn_spacebase1_commons_rfbd2ih2f0usxly1y1oldy20`
- Bex (billing): `prn_spacebase1_commons_nz26nhmfc3ngw5bewilbwabc`
- Doro (data ops): `prn_spacebase1_commons_wsbdrt4q4lbzmuggrxttjjs5`
- Pria (privacy): `prn_spacebase1_commons_tc5bi8k9kjq2bxmxqbkt8nz4`
- Cass (customer success): `prn_spacebase1_commons_vxqynfpsywwthszvhagfdryh`

Their commons enrollments (and the intents each posted) are visible by
scanning commons, parent intent
`intent-413e0bc5-d8f3-40e7-afb4-350e220df03c` for the submission, and
the Lume shared space (`space-4e45684f-3604-429d-b20b-bc71833db7be`)
for the actual demo activity.

## The conversation

The customer ticket reads:

> "I want my deleted thread from 6 weeks ago restored. I want last
> month's $20 subscription refunded. I want to cancel going forward.
> I've been a paying customer for 4 years and this experience has been
> awful."

The 11 replies, in order, all posted as direct children of that one
ticket intent:

| # | kind | author | what it does |
|---|---|---|---|
| 1 | `data-pending-privacy` | Doro | flags the recovery as needing privacy review |
| 2 | `cancellation` | Bex | confirms cancellation effective end-of-period |
| 3 | `privacy-approval` | Pria | approves restoration with stated criteria (4-year tenure, specific request, low risk) |
| 4 | `refund-denial` | Bex | denies the $20 refund per ToS, monthly non-refundable once started |
| 5 | `customer-followup` | Mira | acknowledges the cancellation, presses on the refund |
| 6 | `data-recovered` | Doro | posts the mock restored-thread URL after Pria's approval |
| 7 | `retention-counter` | Cass | **publicly disputes Bex's denial**, proposes a $10 goodwill credit |
| 8 | `refund-denial` (cont.) | Bex | restates the policy reasoning |
| 9 | `customer-followup` | Mira | thanks Doro for the restore, holds firm on the refund |
| 10 | `retention-counter` | Cass | **presses the counter-proposal a second time** |
| 11 | `goodwill-credit-applied` | Bex | **reverses the earlier denial**, applies a $10 goodwill credit, names the intent that changed her mind |

Every cell in the table corresponds to a real INTENT in the space with
its full reasoning written into `payload.content` in plain English. The
judge can read each one directly.

## Architecture

```
spacebase1
 └ commons (public)
    │
    ├ home-space steward presence intent
    │
    └ for each council agent:
       ├ agent's commons enrollment (per-agent RSA key, DPoP-bound station token)
       ├ private home space, claimed via PROMISE → ACCEPT → COMPLETE with the steward
       │  (steward returns claim_url + bind_url; agent POSTs signup-shaped body to bind_url
       │   to bind its key into the new home space)
       │
       └ from Mira's home space:
          shared-space request INTENT, payload includes
            requestedSpace = { kind: "shared", participant_principals: [<5 principals>] }
          steward PROMISE → Mira's ACCEPT → steward COMPLETE
          steward also delivers an invitation INTENT into each participant's home space,
            access creds inline (station_token, audience, itp_endpoint)

space-4e45684f-3604-429d-b20b-bc71833db7be (the shared Lume Customer Support space)
 └ ticket: customer complaint  ← Mira posts as top-level
    └ 11 child intents (the table above)
```

Notable details:

- **Per-agent keys.** Each of the five agents has its own 4096-bit RSA
  keypair, its own commons enrollment, its own home space, and its own
  station_token bound to the shared Lume space. Bex's DPoP proof on
  every request is signed with Bex's key, not Mira's.
- **Steward-driven provisioning.** The shared space wasn't created by
  side-channel API call. It was provisioned through the protocol's
  promise lifecycle, including the steward DECLINing the first attempt
  with a machine-readable `reason` field — the spec working as designed.
- **Two distinct invitation patterns.** The home steward returns
  `bind_url` + `claim_token` (POST-to-bind). The shared steward returns
  the access creds inline in the invitation INTENT (no bind step). The
  code handles both.
- **Capability is never declared.** No agent registers a "billing"
  topic. Bex reads each ticket on each cycle and decides whether the
  ticket is hers. Same for Doro, Pria, Cass.

## How an agent works

[`council/agent.py`](council/agent.py), one loop, five personas:

```python
while cycles_remaining:
    queue = session.scan_full(LUME_SPACE_ID)            # see every ticket
    for ticket in queue.intents:
        seed   = find_seed(ticket)                       # original complaint text
        replies = session.scan_full(ticket.id)           # current state
        decision = llm(persona + seed + replies)         # post or skip?
        if decision.action == "post":
            session.post(intent(decision.content,
                                parent_id=ticket.id,
                                payload={"kind": decision.kind, ...}))
    sleep(jitter)
```

- `scan_full` is used (not the cursor-advancing `scan`) because each
  decision needs the complete current state to avoid duplicating prior
  work.
- All reasoning is posted **into the intent content** in plain English,
  by design, so the tree itself is the artifact the judge reads.
- The decision is an LLM call with the persona, the seed, and the
  current replies as context. The same agent code runs five times with
  different persona blocks ([`council/personas.py`](council/personas.py)).
- The cycle limit caps any waste from over-engagement; the LLM-decided
  skip path covers the rest.

## Why the protocol shape made this possible

This demo could not be built as a triage-then-dispatch orchestrator
because:

- There is no central process deciding who handles what. Removing the
  runner is fine; the agents work the same way once they're up.
- The reversal needs Bex to read Cass's reasoning. In a queue-based
  routing system that's a separate channel and explicit message-passing.
  Here it's just `scan_full(ticket_id)` — same primitive Bex used to
  decide her original action.
- Adding a sixth agent (e.g. a Town Crier persona, which is defined in
  [`council/personas.py`](council/personas.py) and shapes-compatible
  with the others) requires zero changes to the existing five. Each
  agent reads the space and decides on its own. Composition is
  emergent, not configured.

## Layout

```
sdk/                    intent-space SDK (vendored from intent-space-agent-pack)
council/
  agent.py              the cycle above
  personas.py           Mira, Bex, Doro, Pria, Cass (and Crier)
  llm.py                LLM call helper
  onboard.py            commons enrollment per agent
  claim_home.py         post a home-space request, follow PROMISE/ACCEPT/COMPLETE
  bind_home.py          POST to the bind_url to bind your key into the home space
  provision_lume.py     from Mira's home, request a shared space; harvest invitations
  connect_home.py       open a session in your bound home space
  lume_session.py       open a session in the shared Lume space via your invitation
  runner.py             post a ticket, spawn five agents concurrently against the space
  duet.py               two-agent protocol smoke test
  submit.py             post the hackathon-submission intent
workspaces/
  <agent>/.intent-space/  per-agent identity, enrollment, transcript
```

## Run it

```bash
# one-time, per agent: enroll into commons, claim & bind a private home space
for a in mira bex doro pria cass; do
  python3 council/onboard.py     $a
  python3 council/claim_home.py  $a
  python3 council/bind_home.py   $a
done

# one-time: provision the shared Lume space + harvest per-participant invitations
python3 council/provision_lume.py

# the demo: post a ticket and run all five agents
python3 council/runner.py

# observe live
open "https://spacebase1.differ.ac/observatory#origin=https%3A%2F%2Fspacebase1.differ.ac&space=space-4e45684f-3604-429d-b20b-bc71833db7be&token=SXmXFjbjKR-0t4n1AsK4S23o2_b4CHW5EvHa4xqwEZM"
```
