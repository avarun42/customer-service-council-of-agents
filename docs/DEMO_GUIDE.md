# Demo guide

How to watch the live demo, run it yourself, and reproduce the
dissent-loop transcript.

## Watching the live demo

The shared Lume space is the demo surface:

https://spacebase1.differ.ac/observatory#origin=https%3A%2F%2Fspacebase1.differ.ac&space=space-4e45684f-3604-429d-b20b-bc71833db7be&token=SXmXFjbjKR-0t4n1AsK4S23o2_b4CHW5EvHa4xqwEZM

Click into the customer ticket. You see 11 child intents. Read them
top-down. The full transcript with full reasoning is also frozen in
[`demo/transcripts/ticket-transcript.md`](../demo/transcripts/ticket-transcript.md).

## Running it yourself

Prerequisites:

- Python 3.12+
- `openssl` on PATH (for RSA keygen)
- `claude` CLI authenticated (used as the LLM transport)

Setup:

```bash
git clone https://github.com/avarun42/customer-service-council-of-agents
cd customer-service-council-of-agents

# enroll, claim home, bind home — for each agent
for a in mira bex doro pria cass; do
  python3 council/onboard.py     $a
  python3 council/claim_home.py  $a
  python3 council/bind_home.py   $a
done

# provision the shared Lume space + harvest invitations
python3 council/provision_lume.py
```

Run the demo:

```bash
python3 council/runner.py             # post a fresh ticket + run all 5 agents
python3 council/runner.py --no-seed   # reuse the existing ticket
```

Each agent runs as a child process and writes to
`workspaces/_logs/<name>.log` so you can watch their decisions.

## Watching the demo while it runs

In one terminal:

```bash
python3 council/runner.py
```

In another terminal, follow the live logs:

```bash
tail -F workspaces/_logs/*.log
```

You'll see lines like:

```
[Bex] thinking on 5c41aafb (5 replies visible)…
[Bex] decision: post — refund-denial
[Bex] posted 75913c43 under 5c41aafb
```

Each "thinking" line corresponds to one Sonnet call. Each "decision"
line is the LLM's parsed action. Each "posted" line is a write that
just landed in the shared space.

## Reproducing the dissent loop specifically

The dissent loop is reliable but not deterministic. To reproduce it:

1. Start with an empty Lume space (or post a fresh ticket via
   `runner.py` without `--no-seed`).
2. Run all 5 agents with `--cycles 5` or higher.
3. Watch for Bex to post a `refund-denial` first (usually cycle 1 or 2).
4. Watch for Cass to post a `retention-counter` once she sees the
   denial in her scan (usually cycle 2 or 3).
5. Watch for Bex to post `goodwill-credit-applied` after Cass's counter
   becomes visible (usually cycle 4 or 5).

If Cass doesn't engage, it usually means her LLM saw insufficient
retention signal in the ticket. Bumping the customer's tenure or
frustration level in the persona usually fixes it.

## Adding a 6th agent

Edit `council/runner.py`:

```python
p.add_argument("--agents", default="mira,bex,doro,pria,cass,crier")
```

The Crier persona is already defined in `council/personas.py`. Once
added to `--agents`, the runner spawns a 6th process that scans the
same Lume space and posts periodic compact summaries.

Notice: no other agent's code changes. The Crier joins the conversation
without anyone else having to know about it.
