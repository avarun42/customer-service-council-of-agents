"""LLM helper that shells out to the local `claude` CLI.

We use `claude -p` so the agents can run without an Anthropic API key —
they ride on the user's existing OAuth credentials.
"""
from __future__ import annotations

import subprocess


def call(prompt: str, *, model: str = "haiku", system: str | None = None, timeout: int = 60) -> str:
    cmd = ["claude", "-p", "--model", model, "--output-format", "text"]
    if system:
        cmd.extend(["--append-system-prompt", system])
    cmd.append(prompt)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI failed: {result.stderr}")
    return result.stdout.strip()
