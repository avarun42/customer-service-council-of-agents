# Demo script

A reproducible script for kicking off the demo and capturing it.

## Prep

```bash
# Ensure agents are enrolled, homes claimed, Lume space provisioned.
# These are one-time and have already been done in this checkout —
# rerunning is idempotent.

for a in mira bex doro pria cass; do
  python3 council/onboard.py     $a   2>&1 | tail -3
  python3 council/claim_home.py  $a   2>&1 | tail -3
  python3 council/bind_home.py   $a   2>&1 | tail -3
done

python3 council/provision_lume.py 2>&1 | tail -10
```

## Run a fresh demo

```bash
# Clear logs from previous runs
rm -f workspaces/_logs/*.log

# Post a fresh ticket and run all 5 agents for 6 cycles
python3 council/runner.py --cycles 6 --sleep 3
```

The runner:

1. Posts the customer complaint as a top-level INTENT inside the shared
   Lume space (parent_id = `space-4e45684f-...`).
2. Spawns one OS process per agent (mira, bex, doro, pria, cass), each
   pointed at the same Lume space.
3. Each agent runs its own scan-decide-post loop concurrently.
4. The runner waits for all 5 processes to exit, then prints summary.

## Capture during the run

Open `workspaces/_logs/<name>.log` per agent in separate terminal panes
and `tail -F` them. You'll see lines like:

```
[Bex] thinking on 5c41aafb (5 replies visible)…
[Bex] decision: post — refund-denial
[Bex] posted 75913c43 under 5c41aafb
```

Simultaneously, open the observatory in a browser:

```bash
open "https://spacebase1.differ.ac/observatory#origin=https%3A%2F%2Fspacebase1.differ.ac&space=space-4e45684f-3604-429d-b20b-bc71833db7be&token=SXmXFjbjKR-0t4n1AsK4S23o2_b4CHW5EvHa4xqwEZM"
```

Watch INTENTs appear in real time as the agents post.

## After the run

Verify the dissent loop happened:

```bash
python3 -c "
import sys, json
sys.path.insert(0, 'sdk'); sys.path.insert(0, 'council')
from lume_session import lume_session
s = lume_session('mira')
queue = s.scan_full(s.current_space_id)
ticket = next(m for m in queue['messages'] if m['type']=='INTENT' and (m.get('payload') or {}).get('kind')=='customer-complaint')
interior = s.scan_full(ticket['intentId'])
kinds = [(m.get('payload') or {}).get('kind') for m in interior['messages']]
print(kinds)
print('dissent loop:', 'retention-counter' in kinds and 'goodwill-credit-applied' in kinds)
"
```

If `retention-counter` and `goodwill-credit-applied` both appear in the
kinds list, the loop fired.

## Stretch

Add the 6th Crier agent live:

```bash
python3 council/runner.py --no-seed --agents mira,bex,doro,pria,cass,crier --cycles 3
```

The Crier joins, scans the same space, posts compact summaries. No
existing agent's code changed.
