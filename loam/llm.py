"""Thin wrapper over live Claude — the only place that touches the network.

Cognition (loam/cognition.py) asks this for a completion at whatever tier the
world's attention economy has chosen for the moment. Everything else in Loam
runs with zero dependencies and no key.
"""
from __future__ import annotations

import os

from . import config


class LiveLLM:
    """A live Claude client. Constructed only when the world runs with --real."""

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

    def complete(self, *, tier: str, system: str, user: str, max_tokens: int = 120) -> str:
        resp = self._client.messages.create(
            model=tier,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        parts = [b.text for b in resp.content if b.type == "text"]
        return "\n".join(parts).strip()
