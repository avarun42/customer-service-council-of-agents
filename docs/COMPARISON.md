# Comparison: orchestrator vs. intent-space council

A side-by-side of how the same demo would look on a triage-then-dispatch
orchestrator versus our intent-space council.

## The customer ticket

> "Restore my deleted thread, refund my $20, cancel going forward, I've
> been a customer 4 years."

## On a triage-then-dispatch orchestrator

```
ticket → router
        └ classify: [billing, data-recovery, retention-risk]
        ├ enqueue → billing.cancel-subscription (Bex)
        ├ enqueue → billing.refund-decision    (Bex)
        ├ enqueue → data-ops.thread-recovery   (Doro)
        │           └ requires-approval(privacy)
        │             └ enqueue → privacy.review (Pria)
        └ enqueue → retention.advisory         (Cass)
                    ↓
                    Cass's task is "review the resolution and flag risk."
                    But by the time Cass runs, Bex has already closed
                    the refund task as denied. Cass's flag goes into a
                    "review queue" that triggers an appeals workflow.
                    Bex picks up the appeal, sees a "review reason" tag,
                    and re-evaluates.
```

**Audit trail:** scattered across multiple work items, each with its
own state transitions. Reasoning is in tags and free-text fields on
disparate records.

**Adding a 6th agent:** requires creating a new task type, hooking it
into the router, defining where in the pipeline it inserts.

## On our intent-space council

```
ticket (top-level INTENT in shared Lume space)
  ├ Doro: data-pending-privacy           ; reads ticket, decides she's relevant
  ├ Bex:  cancellation                   ; reads ticket, decides she's relevant
  ├ Pria: privacy-approval               ; reads queue, sees Doro's escalation
  ├ Bex:  refund-denial                  ; same agent, second issue, second post
  ├ Mira: customer-followup
  ├ Doro: data-recovered
  ├ Cass: retention-counter              ; reads tree, sees Bex's denial, disputes
  ├ Bex:  refund-denial (continuation)
  ├ Mira: customer-followup
  ├ Cass: retention-counter              ; presses the point
  └ Bex:  goodwill-credit-applied        ; reverses #4, cites #7
```

**Audit trail:** the tree itself, with reasoning written into every
intent's content, in plain English, append-only.

**Adding a 6th agent:** import the persona block, add the name to
`runner.py`. Done. The new agent sees the same tree the others see and
posts when it has something to add.

## Concrete differences

| concern | orchestrator | intent-space council |
|---|---|---|
| where work is "assigned" | router classifier | nowhere; agents self-select |
| where reasoning lives | tags, custom fields, separate logs | the intent's content, in plain English |
| how dispute is expressed | escalate workflow / appeal queue | sibling intent under the same ticket |
| how reversal is recorded | state transition on the original record | new intent that supersedes the old one |
| auditability | reconstruct from multiple records | read the tree |
| extensibility (new agent) | router config + queue + handler | new persona block |

## What the orchestrator does better

We're being honest: the orchestrator wins on:

- **Strict SLAs.** Queues give you per-step latency budgets. Trees don't.
- **Bounded backlogs.** Queues drop or backpressure when overloaded. The
  intent-space council just posts more intents into the same space.
- **Mature tooling.** Workflow engines have UIs, observability,
  integrations. We have an observatory and a CLI.

For coordination tasks where the *content of the reasoning* is the work
product — multi-agent customer support being a clean example — the
trade is worth it.
