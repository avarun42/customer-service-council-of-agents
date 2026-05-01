"""Parse a JSON decision out of the LLM's natural-language response."""
from __future__ import annotations

import json
import re


def parse_decision(text: str) -> dict:
    """Extract a JSON action object from the LLM response, leniently."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except Exception:
            pass
    start = text.rfind("{")
    if start >= 0:
        try:
            return json.loads(text[start:])
        except Exception:
            pass
    return {"action": "skip", "reasoning": "could not parse LLM output"}
