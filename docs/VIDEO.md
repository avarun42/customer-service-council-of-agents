# Video walkthrough

The live demo is itself the video — the observatory at spacebase1
streams the framed acts as they happen, so any viewer with the
observatory URL can watch the conversation unfold in real time.

## Live video walkthrough URL

https://spacebase1.differ.ac/observatory#origin=https%3A%2F%2Fspacebase1.differ.ac&space=space-4e45684f-3604-429d-b20b-bc71833db7be&token=SXmXFjbjKR-0t4n1AsK4S23o2_b4CHW5EvHa4xqwEZM

The observatory renders the recursive thread tree, attributes
participants by friendly name, refreshes without flashing, and tints
each top-level INTENT's left bar by outcome.

## What to watch for in the video

1. **Ticket arrives** as a top-level INTENT in the Lume space.
2. **Doro and Bex engage in parallel** — they post in different
   sub-areas of the ticket interior, almost simultaneously. The
   observatory shows both.
3. **Pria approves** Doro's privacy-pending escalation; Doro posts the
   restored-thread URL after.
4. **Cass disputes** Bex's refund denial. The observatory shows the
   sibling intent appear under the ticket — *not* nested under Bex's
   denial, intentionally, to keep the dispute peer-to-peer rather than
   threaded.
5. **Bex's reversal** appears as a new intent superseding her own
   earlier denial. The audit trail shows both, in order.

## Frozen transcript (post-demo)

If you don't want to watch live, the full transcript with all 11
replies and their full reasoning is at
[`demo/transcripts/ticket-transcript.md`](../demo/transcripts/ticket-transcript.md).

## Recording your own video

The observatory is screencast-friendly — running the demo with
`python3 council/runner.py` against a fresh ticket while screencasting
the observatory produces a 2-3 minute video covering the entire
dissent-and-resolution arc.

Recommended capture: macOS Screen Recording or `asciinema` for the
terminal-side `tail -F` view.
