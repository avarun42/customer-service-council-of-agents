# Why intent-space (and not a queue / pub-sub / workflow engine)

Customer support coordination systems exist. We could have built this
on a message queue. We could have built it on a workflow engine. We
could have built it on pub/sub. We didn't, and the reason is specific.

## The dissent loop is the disqualifying example

The headline behavior — Cass disputes Bex's refund denial publicly,
Bex's loop reads Cass's reasoning, Bex reverses — *cannot be expressed*
on:

### A queue

Tickets are units of work; a worker pulls one and processes it. Once
Bex processes the refund decision, that work item is gone. Cass would
need a separate appeal queue, and Bex would need a separate "review
appeals" loop. The reasoning behind the appeal lives in a different
work item than the original decision. The audit trail is fragmented
across queues.

### A workflow engine

A workflow has states. The refund-decision step transitions to "denied"
or "approved." A retention reviewer might insert a "needs review" state
before the transition is finalized. But that's pre-decision review, not
post-decision dispute. Reversing a denied decision requires a
purpose-built "appeal" workflow with its own state machine. You end up
encoding "Cass can dispute" as a state transition, not as Cass
exercising her own judgment.

### Pub/sub

Cass would subscribe to "refund-denial" events. Bex would publish one.
Cass would publish a "retention-objection" event. Bex would subscribe
to that. But subscribing means *committing in advance* to caring about
those events. The whole point of intent-space is that capability is
**not declared globally** — agents read what's in front of them and
self-select.

## What intent-space gives us specifically

1. **One shared substrate.** All agents read and write the same tree.
   No federation across queues / topics / workflows.

2. **Reasoning is in the data.** A pub/sub event has a payload, but the
   convention is that payloads are minimal — a notification, an id, a
   tag. Intent-space encourages putting the actual reasoning into the
   intent content, because the next agent that reads it will use it as
   input to its own LLM call. The reasoning *is* the message.

3. **Append-only consensus.** When Bex reverses, she doesn't edit her
   prior decision. She posts a new intent that supersedes it. Both are
   visible. The audit trail is structurally complete, by construction.

4. **Self-selection.** No agent has to declare ahead of time that it
   cares about retention disputes. Cass reads each ticket, applies her
   judgment, posts when she has something to add.

5. **Composability via nesting.** Adding a "Quality Auditor" agent that
   comments on the resolution quality — without changing any other
   agent's code — is trivial. The auditor scans, decides, posts. The
   other agents keep doing what they're doing.

## When this is the wrong choice

We're not arguing intent-space is universally better. It's not. If you
need:

- Strict ordering of consumers
- Bounded backlogs with backpressure
- At-most-once or exactly-once delivery semantics
- Sub-millisecond fan-out

… you want a queue or a stream. Intent-space is for *coordination*, not
delivery. Specifically, coordination that involves visible reasoning
between independent reasoning agents.

That's what the customer council is. So that's why we used it.
