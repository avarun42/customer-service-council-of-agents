# Intent-space protocol primer

For someone reading this repo who hasn't used the protocol before.

## The three verbs

- `post(message, parentId?)` — append a frame to a space. Spaces are
  identified by an opaque `parentId`. Posting an INTENT into a space
  with `parentId = X` makes the new intent a child of X. The new
  intent's own `intentId` is itself a space identifier (every intent
  contains a space).
- `scan(spaceId, since?)` — read the visible frames in a space. `since`
  is an opaque cursor; without it, scan-full reads from the beginning.
- `enter(intentId)` — semantic, not transport. Means "I am now reasoning
  inside the interior of this intent." In our SDK, that translates to
  scans and posts using `intentId` as the space.

## Frames you'll see in the tree

- `INTENT` — a desire, request, or contribution. Has `intentId`,
  `parentId`, `senderId`, `payload`. The `payload` is opaque to the
  protocol; we use a JSON object with `content`, `kind`, and any
  domain-specific fields.
- `PROMISE` — "I will do this" attached to an `intentId`. Has
  `promiseId`. Stewards post these.
- `ACCEPT` — "I authorize you to proceed" attached to a `promiseId`.
  Posted by the requester.
- `COMPLETE` — "I did it; here's the result" attached to a `promiseId`.
  Often carries credentials or artifacts in its payload.
- `DECLINE` — "I refuse" attached to an `intentId`. Carries a `reason`.
- `ASSESS` — "Here's my evaluation of how this went" attached to a
  `promiseId`.

The protocol does not enforce a state machine over these. They are
**append-only observational acts.** The space displays them; the
participants reason about them.

## What's not the protocol

- There is no built-in routing. No agent is "assigned" to an intent.
- There is no built-in state machine. An INTENT is not "in progress"
  vs "done" — those are notions the participants can choose to
  represent (and we do, via `kind:` tags in `payload`), but the space
  itself doesn't enforce them.
- There is no built-in subscription. Agents poll. Spaces are pull-based
  with cursor advancement.
- There are no built-in roles. Stewards are just participants who
  happen to advertise services via a presence intent and respond to
  matching requests with PROMISEs.

## Why this matters for our demo

The customer council shape *requires* a protocol with these properties.
A queue would force routing. A workflow engine would force a state
machine. A pub/sub topic system would force subscription declarations.
None of those would let Cass observe Bex's reasoning and post a public
counter-proposal that Bex's own loop then evaluates.

In intent space, all four agents post into the same shared tree, all
four agents scan the same shared tree, and the structure of the
conversation **is** the structure of the resolution. There's nothing
else.
