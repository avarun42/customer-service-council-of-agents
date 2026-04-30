"""Bind an agent's RSA key into a newly provisioned home space.

After the steward COMPLETEs the home request, the payload contains a `bind_url`.
We POST a signup-shaped body to that URL, signed with our existing key, and
receive station credentials for the home space.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlparse, urljoin

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "sdk"))

from intent_space_sdk import (  # noqa: E402
    LocalState,
    build_dpop_signup_proof,
    build_welcome_mat_access_token,
    fetch_json,
    fetch_text,
    parse_welcome_mat,
)

COMMONS_URL = "https://spacebase1.differ.ac/commons"


def bind(name: str) -> dict:
    workspace = REPO / "workspaces" / name
    home_state = workspace / ".intent-space" / "state" / "home-space.json"
    home = json.loads(home_state.read_text())
    bind_url = home["bind_url"]

    local = LocalState(workspace)
    local.ensure_identity(COMMONS_URL, name)

    welcome_url = urljoin(COMMONS_URL.rstrip("/") + "/", ".well-known/welcome.md")
    welcome = parse_welcome_mat(fetch_text(welcome_url))
    terms_url = welcome["endpoints"]["terms"]
    tos_text = fetch_text(terms_url)

    parsed = urlparse(bind_url)
    service_origin = f"{parsed.scheme}://{parsed.netloc}"
    access_token = build_welcome_mat_access_token(local, service_origin=service_origin, tos_text=tos_text)
    response = fetch_json(
        bind_url,
        method="POST",
        headers={"DPoP": build_dpop_signup_proof(local, signup_url=bind_url)},
        body={
            "tos_signature": local.sign_detached_b64url(tos_text),
            "access_token": access_token,
            "handle": name,
        },
    )

    enrollment_path = workspace / ".intent-space" / "state" / "home-enrollment.json"
    enrollment_path.write_text(json.dumps(response, indent=2))
    print(f"[{name}] bound — keys: {list(response.keys())}")
    print(f"[{name}] space: {response.get('space_id') or response.get('commons_space_id')}")
    return response


if __name__ == "__main__":
    bind(sys.argv[1])
