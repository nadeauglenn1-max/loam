"""You — the one who comes to understand.

At the start you understand no one. This is the reframe at the heart of Loam's
story: you do not begin as the keeper of every tongue, you *become* them. Your
understanding of a family grows as you help them, family by family, until — if
you see it through — you understand everyone.

This is playthrough state (your progress), not part of a base. It rides on the
World and persists with the playthrough.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Player:
    understanding: dict[str, float] = field(default_factory=dict)   # family -> 0..1

    def of(self, family: str) -> float:
        """How completely you understand a family, 0 (strangers) to 1 (fully)."""
        return self.understanding.get(family, 0.0)

    def understands(self, family: str) -> bool:
        return self.of(family) >= 1.0

    def learn(self, family: str, amount: float) -> float:
        """Deepen your understanding of a family, never past complete. Returns the
        new level."""
        level = max(0.0, min(1.0, self.of(family) + amount))
        self.understanding[family] = level
        return level
