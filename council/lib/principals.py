"""Build a principal_id → friendly-name mapping from workspace enrollment files."""
from __future__ import annotations

import json
from pathlib import Path


def build_principal_map(repo_root: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    ws_dir = repo_root / "workspaces"
    if not ws_dir.exists():
        return mapping
    for d in ws_dir.iterdir():
        if not d.is_dir():
            continue
        for fname in ("station-enrollment.json", "home-enrollment.json"):
            enrollment = d / ".intent-space" / "state" / fname
            if enrollment.exists():
                try:
                    data = json.loads(enrollment.read_text())
                    pid = data.get("principal_id")
                    if pid:
                        mapping[pid] = d.name
                except Exception:
                    pass
    return mapping
