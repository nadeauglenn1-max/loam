"""Heterogeneous, evolving wants — the pressure that makes a world a story.

No two agents want the same things in the same order, and what an agent wants
changes: satisfy a desire and a new one rises in its place. Wants are the
engine; the language barrier is the friction they must overcome.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from .config import CONCEPTS


def _weight(agent_id: str, concept: str) -> float:
    """Deterministic per-agent appetite for a concept, in [0.05, 1.0]."""
    h = hashlib.sha256(f"{agent_id}:appetite:{concept}".encode()).hexdigest()
    return 0.05 + (int(h[:8], 16) % 1000) / 1000.0 * 0.95


@dataclass
class Wants:
    """An agent's desire state: a personality (fixed appetites) and a current
    focus that shifts as desires are met."""
    agent_id: str
    appetite: dict[str, float] = field(default_factory=dict)
    focus: str = ""
    intensity: float = 1.0

    @classmethod
    def for_agent(cls, agent_id: str) -> "Wants":
        appetite = {c: _weight(agent_id, c) for c in CONCEPTS}
        focus = max(appetite, key=appetite.get)
        return cls(agent_id=agent_id, appetite=appetite, focus=focus, intensity=1.0)

    def satisfy(self, amount: float = 0.5) -> None:
        """Meet the current want a little. When spent, a new focus rises —
        weighted by appetite but never the same one twice running."""
        self.intensity -= amount
        if self.intensity <= 0:
            prev = self.focus
            ranked = sorted(CONCEPTS, key=lambda c: self.appetite[c], reverse=True)
            self.focus = next((c for c in ranked if c != prev), ranked[0])
            self.intensity = 1.0

    def describe(self) -> str:
        return f"{self.focus} ({self.intensity:.1f})"
