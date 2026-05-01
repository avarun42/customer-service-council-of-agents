# Architecture

## High-level

```
spacebase1 commons (public)
   │
   ├── per-agent enrollment (RSA keypair + DPoP-bound station_token)
   │
   ├── home-space steward presence intent
   │
   └── private home space, per agent
        │   (claimed via PROMISE → ACCEPT → COMPLETE,
        │    then key-bound via POST to bind_url)
        │
        └── shared-space request INTENT (posted from Mira's home)
             │   payload.requestedSpace = {
             │     kind: "shared",
             │     participant_principals: [<5 home-space principal ids>]
             │   }
             ├── steward PROMISE
             ├── Mira's ACCEPT
             └── steward COMPLETE → returns shared_space_id, invitations dispatched

space-4e45684f-3604-429d-b20b-bc71833db7be (shared Lume Customer Support space)
   └── ticket: customer complaint                ← Mira posts as top-level
       └── 11 child INTENTs (the council reasons in public)
```

## Process model

Each council agent runs as an **independent OS process** (`subprocess.Popen`),
launched from `council/runner.py`. There is no shared memory between
agents. The only shared substrate is the intent space.

Each agent process has:

- a unique `agent_name` (mira, bex, doro, pria, cass)
- its own workspace directory under `workspaces/<name>/`
- its own `.intent-space/identity/station-private-key.pem` (4096-bit RSA)
- its own commons enrollment, home space, and Lume-space invitation
- its own `tool-steps.ndjson` step log and `tutorial-transcript.jsonl`

When the runner spawns agents, it staggers them by 500ms so they don't
all hit the station at the same instant. Each agent then runs its
`scan → decide → maybe post` loop on a jittered cadence so the agents
naturally interleave instead of lock-stepping.

## Authentication & identity

Three layers of identity material per agent:

1. **Durable key:** the 4096-bit RSA keypair under
   `.intent-space/identity/`. This is the long-term identity anchor.
2. **Per-audience principal:** the station maps the public-key thumbprint
   to a `principal_id` per audience. So Mira has a `_commons_…` principal
   for the commons audience, a `_space_<homeid>_…` principal for her
   home space audience, and (after invitation) a Lume-space principal
   too.
3. **Per-audience station_token:** a short-lived bearer token DPoP-bound
   to the durable key. Sent on the wire as `Authorization: DPoP <token>`
   plus a per-request `DPoP:` header signed with the durable key.

The station verifies the DPoP proof's `cnf.jkt` matches the bound key,
and that the proof hasn't been replayed. The result is **proof of
possession on every request** — bearer tokens alone are not sufficient.

## Provisioning

Two provisioning patterns appear in the demo:

### Home space (per agent, claim/bind flow)

```
agent → commons → INTENT (kind: home, visibility: private)
               ← PROMISE
agent → ACCEPT
               ← COMPLETE { claim_url, bind_url, claim_token, home_space_id }
agent → POST <bind_url> { tos_signature, access_token, handle }   ← signup-shaped body
               ← { station_token, station_audience, itp_endpoint, … }
```

The agent's existing commons RSA key is bound to the new home space —
not a fresh key. That's how same-agent continuity works across spaces.

### Shared space (provisioned from one agent's home, fan-out to peers)

```
mira (in her home) → INTENT (kind: shared, participant_principals: [...5...])
                   ← PROMISE
mira → ACCEPT
                   ← COMPLETE { shared_space_id, invitation_count: 5 }
                   + INTENT delivered into each participant's home space:
                       { shared_space_id, access: { station_token, audience, itp_endpoint } }
each participant → connect_to(access)   ← no separate bind step; creds are inline
```

The two patterns are visibly different in the code paths:
[`council/bind_home.py`](../council/bind_home.py) for home-space
binding, [`council/lume_session.py`](../council/lume_session.py) for
shared-space invitation pickup.

## Agent loop

```
while cycles_remaining:
    queue_scan = scan_full(LUME_SPACE_ID)
    for ticket in queue_scan.intents_typed:
        if not is_real_ticket(ticket): continue
        seed = find_seed(ticket)
        replies = scan_full(ticket.id)
        decision = llm(persona + seed + replies)
        if decision.action == "post":
            post(intent(decision.content,
                        parent_id=ticket.id,
                        payload={"kind": decision.kind, …}))
    sleep(jitter)
```

Per-cycle invariants:

- All work the agent considers must be **visible in the tree.** No
  hidden state.
- The decision is made by an LLM call that sees the persona AND the
  current public state of the ticket. Same persona + same tree +
  different time = (mostly) the same decision.
- If the LLM returns `"action": "skip"`, the cycle is a no-op. The
  decision and reasoning are not posted unless `action: "post"` —
  silence is meaningful.
- A reply is itself a space; the next cycle's scan_full returns it.

## Failure modes seen during development

- **Steward DECLINE for malformed payload.** Our first shared-space
  request used `spacePolicy.participants` (wrong field) instead of
  `requestedSpace.participant_principals`. The steward returned a
  DECLINE with a `reason` string telling us what to fix. Reading the
  tree was the debugging interface.
- **Empty agent silently skipping.** An early version of the cycle
  early-exited if there were no other intents in the ticket interior.
  Bex never engaged because she always saw an empty interior on first
  cycle. Fix: removed the early-exit; let the LLM decide.
- **Wrong space target.** First runs accidentally posted into commons
  before the shared space was provisioned. Caught by enforcing
  `lume_session()` as the only path to a posting session.
