"""Heterogeneous, evolving wants — the social pressure that gives life meaning
beyond survival.

Appetites (how hard each want pulls) are heritable: they come from the genome,
not from here. A being's *current* want shifts as desires are met.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .config import CONCEPTS


@dataclass
class Wants:
    agent_id: str
    appetite: dict[str, float] = field(default_factory=dict)
    focus: str = ""
    intensity: float = 1.0

    @classmethod
    def of(cls, agent_id: str, appetites: dict[str, float]) -> "Wants":
        appetite = dict(appetites)
        focus = max(appetite, key=appetite.get) if appetite else CONCEPTS[0]
        return cls(agent_id=agent_id, appetite=appetite, focus=focus, intensity=1.0)

    def satisfy(self, amount: float = 0.5) -> None:
        """Meet the current want a little. When spent, a new focus rises —
        weighted by appetite but never the same one twice running."""
        self.intensity -= amount
        if self.intensity <= 0:
            prev = self.focus
            ranked = sorted(CONCEPTS, key=lambda c: self.appetite.get(c, 0.0), reverse=True)
            self.focus = next((c for c in ranked if c != prev), ranked[0])
            self.intensity = 1.0

    def describe(self) -> str:
        return f"{self.focus} ({self.intensity:.1f})"
