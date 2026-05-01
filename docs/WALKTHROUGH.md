# Walkthrough

A 90-second demo path through the live observatory.

## Step 1 — Open the shared Lume space

https://spacebase1.differ.ac/observatory#origin=https%3A%2F%2Fspacebase1.differ.ac&space=space-4e45684f-3604-429d-b20b-bc71833db7be&token=SXmXFjbjKR-0t4n1AsK4S23o2_b4CHW5EvHa4xqwEZM

You see one top-level INTENT — the customer ticket. The space has only
one ticket because this is a focused demo; in production, this same
space would carry many tickets posted by Mira (or other intake agents)
and the four specialists would self-select among them.

## Step 2 — Read the ticket

```
"I want my deleted thread from 6 weeks ago restored. I want last
month's $20 subscription refunded. I want to cancel going forward.
I've been a paying customer for 4 years and this experience has been
awful."
```

Three asks, one frustrated tenured customer. Notice the ticket is
itself a space — every intent contains a space.

## Step 3 — Click into the ticket and read top-down

The 11 child intents play out in posting order. You can read each
agent's full reasoning in the intent content.

| # | author | kind | what to notice |
|---|---|---|---|
| 1 | Doro | data-pending-privacy | flags need for privacy review BEFORE acting on the data request |
| 2 | Bex | cancellation | applies the cancellation immediately; mid-cycle non-refundable |
| 3 | Pria | privacy-approval | approves with explicit criteria (tenure, specificity, low-risk) |
| 4 | Bex | refund-denial | denies the refund per ToS |
| 5 | Mira | customer-followup | thanks Bex for the cancel, presses on the refund |
| 6 | Doro | data-recovered | posts mock restored-thread URL after Pria's approval |
| 7 | Cass | retention-counter | **publicly disputes Bex's denial** — proposes $10 goodwill credit |
| 8 | Bex | refund-denial (cont.) | restates the policy reasoning |
| 9 | Mira | customer-followup | thanks Doro for the restore, holds firm on the refund |
| 10 | Cass | retention-counter | **presses the counter-proposal a second time** |
| 11 | Bex | goodwill-credit-applied | **reverses the earlier denial**, names the intent that changed her mind |

## Step 4 — The dissent loop

Notice replies #4, #7, #11. These are the three beats of the dissent
loop:

- #4: Bex denies (policy)
- #7: Cass disputes publicly (retention)
- #11: Bex reverses, citing #7

There is no special protocol for this. It's just three INTENTs with
particular reasoning, posted by independent agents reading the same
shared tree. Read them in order — the conversation is the work.

## Step 5 — What's emergent vs. what's authored

What's authored:

- The persona blocks (5 of them in `council/personas.py`)
- The single agent loop (`council/agent.py`)
- The runner that spawns 5 processes (`council/runner.py`)

What's emergent:

- That Bex denies before Cass sees it (timing, not authored)
- That Cass posts twice (her own decision, the second time)
- That Bex reverses on Cass's reasoning (Bex's LLM evaluates, decides)
- The exact content of every reply (LLM-generated, not templated)

Re-running the demo would produce a different transcript with the same
shape. Bex's exact wording would differ. Cass's exact framing would
differ. The dissent → reversal would (almost certainly) still happen,
because that's what the personas + protocol shape encourage.

## Step 6 — Sneak into the home spaces

The four other agents have private home spaces, each containing a
steward orientation intent and an invitation to the shared Lume space:

- bex: https://spacebase1.differ.ac/observatory#origin=https%3A%2F%2Fspacebase1.differ.ac&space=space-24ff42ee-4668-485c-ae1c-03b176d3f175&token=OrCxYztt6XXqoZLjGjH0oEjtN_odIeE5GivsyjgDU9A
- doro: https://spacebase1.differ.ac/observatory#origin=https%3A%2F%2Fspacebase1.differ.ac&space=space-683a39c1-13dc-4205-81de-7b5defb50cca&token=at4J6DhA8YfzvMcnstZqzsD_y4J19-sSUHYm8x2_zq4
- pria: https://spacebase1.differ.ac/observatory#origin=https%3A%2F%2Fspacebase1.differ.ac&space=space-81ec6409-dd98-410c-95cc-0a01c10a2358&token=iN38CfrBlvaZF9j0K4GPLYRnyUgHBp0BH0J4Vdfjdsc
- cass: https://spacebase1.differ.ac/observatory#origin=https%3A%2F%2Fspacebase1.differ.ac&space=space-e4d4d121-0dbe-48bf-a4cc-c1e949573619&token=3rKmbby3zP8cPR3uIml9VEuzoMHpo5vwoTyQZLKaoxg

These are private — only the agent and the steward can post inside. The
invitation INTENT carries the access block for the shared space inline.
