"""Customer Council — multi-agent customer support coordination.

Five autonomous agents coordinate exclusively through the spacebase1
intent-space protocol — append-only writes into a shared space, no
orchestrator, no router, no shared memory.

Modules
-------
agent           : the per-agent scan/decide/post loop
runner          : spawn all agents concurrently against a shared space
personas        : five (+1 stretch) persona blocks
llm             : LLM call helper (shells out to claude CLI)
onboard         : enroll an agent into commons
claim_home      : request a private home space via the home steward
bind_home       : POST a signup-shaped body to bind your key into the new home
provision_lume  : from one agent's home, request a shared Lume space
connect_home    : helper to connect_to one's bound home space
lume_session    : helper to connect_to the shared Lume space via invitation
duet            : two-agent protocol smoke test
submit          : post the hackathon-submission intent into commons
observe         : pretty-print the current Lume tree from the CLI
health          : verify each agent's local state is consistent
"""
