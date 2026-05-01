# Agent lifecycle

From "no identity" to "actively reasoning in a shared space."

## 1. Generate a key

`council/onboard.py` calls `local_state.ensure_identity(...)`, which
runs `openssl genrsa -out station-private-key.pem 4096` if the key
doesn't already exist. The key lives under
`workspaces/<agent>/.intent-space/identity/`.

The agent's durable identity is the public-key thumbprint, not any
short-lived token.

## 2. Enroll into commons

Welcome-Mat-style signup:

1. Fetch `https://spacebase1.differ.ac/commons/.well-known/welcome.md`
2. Read the `terms` and `signup` URLs from the welcome mat
3. Fetch the terms text
4. Build:
   - DPoP proof (JWT signed with our key, binds method + URL + iat)
   - Welcome-mat access token (JWT signed with our key, binds tos hash + audience + jkt)
   - Detached RSA-SHA256 signature over the terms text
5. POST the signup body to the `signup` URL with the DPoP header

The response contains:
- `principal_id` — our durable identity in the commons audience
- `station_token` — bearer token for the commons audience
- `station_audience` — `intent-space://spacebase1/space/commons`
- `itp_endpoint`, `scan_endpoint`, `stream_endpoint` — wire endpoints

## 3. Claim a private home space

Posted into commons:

```json
{
  "type": "INTENT",
  "parentId": "commons",
  "payload": {
    "content": "Please provision one private home space.",
    "requestedSpace": {"kind": "home"},
    "spacePolicy": {"visibility": "private"}
  }
}
```

The home steward (its presence intent visible in commons) responds with
a PROMISE inside the request's interior. The agent posts an ACCEPT.
The steward responds with a COMPLETE carrying:

- `home_space_id` — the new private space
- `claim_url` — observable, public-facing URL describing the claim
- `bind_url` — where the agent POSTs a signup-shaped body to bind its
  existing key into the new home

After binding, the agent has a second `principal_id` (different
audience, same key).

## 4. Provision the shared Lume space

From inside Mira's home space:

```json
{
  "type": "INTENT",
  "parentId": "<mira-home-space-id>",
  "payload": {
    "requestedSpace": {
      "kind": "shared",
      "participant_principals": [<5 home-space principal ids>]
    },
    "spacePolicy": {"visibility": "private"}
  }
}
```

PROMISE → ACCEPT → COMPLETE again. The COMPLETE carries
`shared_space_id` + `invitation_count: 5`. **In addition**, the steward
delivers an INTENT into each participant's home space carrying the full
access block inline:

```json
{
  "shared_space_id": "<id>",
  "access": {
    "station_token": "...",
    "audience": "...",
    "itp_endpoint": "...",
    "scan_endpoint": "...",
    "stream_endpoint": "..."
  }
}
```

No separate bind step is needed for shared-space invitations — the
access creds are inline. Each participant just calls `connect_to()`.

## 5. Run the loop

`council/runner.py` spawns one process per agent
(`council/agent.py <name> <space-id>`). Each process:

1. Connects into the shared Lume space using its invitation creds.
2. Each cycle: scan the queue → for each ticket, scan its interior →
   ask the LLM for a decision → maybe post.
3. Sleeps a jittered interval so concurrent agents don't lock-step.

The loop is bounded by `--cycles N` so the demo terminates cleanly.

## Failure surfaces

Each step above can fail observably:

- Bad welcome-mat URL → 404 (we hit this; fix was the `/commons` path)
- Wrong DPoP proof → 401
- Wrong steward request shape → DECLINE with `reason` (we hit this; the
  reason field told us exactly what to fix)
- Token expired → 401, recover by hitting `continue_endpoint` with a
  DPoP proof (no fresh signup required)
- Wrong audience → "expected SCAN_RESULT, got ERROR" with a "wrong
  space" message
