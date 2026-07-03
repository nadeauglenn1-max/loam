"""The cognition seam.

A `Model` turns an agent's situation into a short inner voice — one line of what
it's thinking as it acts. `MockModel` is deterministic and free (CI-safe, the
default); `ClaudeModel` calls a real Claude at whatever tier the world asks for.

The mechanical decision (who to speak to, what to want) lives in the world; the
model supplies the *interiority*. Deepening the model into the decision itself
is the next milestone — the seam is here so that swap is one class, not a
rewrite.
"""
from __future__ import annotations

import hashlib
import os
from typing import Protocol

from . import config


class Model(Protocol):
    def inner_voice(self, *, tier: str, system: str, situation: str) -> str:
        """Return one short line — the agent's thought this tick."""
        ...


# A stock of terse interior lines the mock draws from, so a world feels alive
# offline. Deterministic per situation, so reloads replay identically.
_MOODS = (
    "I want this more than I can say.",
    "Does anyone hear me?",
    "The words come out wrong every time.",
    "Maybe they'll understand if I try again.",
    "I am tired of being alone in my own tongue.",
    "There is something I almost recognized just now.",
    "If I could only make myself plain.",
    "I keep circling the same need.",
    "One of them looked at me like they knew.",
    "I'll reach for it once more.",
)


class MockModel:
    """Free, deterministic cognition. No network, no key."""

    def inner_voice(self, *, tier: str, system: str, situation: str) -> str:
        h = hashlib.sha256(situation.encode("utf-8")).hexdigest()
        return _MOODS[int(h[:8], 16) % len(_MOODS)]


class ClaudeModel:
    """Live cognition via Claude, tiered by the world's attention economy."""

    def __init__(self) -> None:
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover - only on --real without dep
            raise RuntimeError(
                "Live cognition needs the anthropic SDK: pip install 'loam[real]'"
            ) from e
        key = next((os.environ[v] for v in config.API_KEY_ENV_VARS if os.environ.get(v)), None)
        if not key:
            raise RuntimeError(
                "No API key found. Set one of: " + ", ".join(config.API_KEY_ENV_VARS)
            )
        self._client = anthropic.Anthropic(api_key=key)

    def inner_voice(self, *, tier: str, system: str, situation: str) -> str:
        resp = self._client.messages.create(
            model=tier,
            max_tokens=60,
            system=system,
            messages=[{"role": "user", "content": situation}],
        )
        for block in resp.content:
            if block.type == "text":
                return block.text.strip().split("\n")[0]
        return "..."
