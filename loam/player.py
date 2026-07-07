"""You — the one who comes to understand, and who starts knowing nothing.

Two things grow in you, both from zero:

* **skills** — you are no martial expert, no fisher, no smith at the start. You
  learn a trade only by doing it (you don't know how to fight until you've been
  punched a few times). Each trade is its own skill, grown through use.
* **understanding** of each family — won slowly, against their distrust. A word of
  theirs is a *prize*, not a handout: families do not trust a stranger, and only
  come to as your understanding of them deepens. Advance a family's trade and you
  advance with that family.

This is playthrough state — your progress — and it persists with the playthrough.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import config
from .config import CONCEPTS


@dataclass
class Player:
    understanding: dict[str, float] = field(default_factory=dict)   # family -> 0..1, against distrust
    skills: dict[str, float] = field(default_factory=dict)          # trade -> 0..1, grown by doing
    words: dict[str, list] = field(default_factory=dict)            # family -> concepts earned (prizes)

    # ---- understanding a family (slow, distrust-gated, prizes) ------------
    def of(self, family: str) -> float:
        return self.understanding.get(family, 0.0)

    def understands(self, family: str) -> bool:
        return self.of(family) >= 1.0

    def earned(self, family: str) -> list:
        return self.words.get(family, [])

    def trust_gain(self, family: str, step: float) -> float:
        """A family gives little at first — they distrust a stranger — and more as
        your understanding of them grows."""
        return step * (config.DISTRUST_FLOOR + (1 - config.DISTRUST_FLOOR) * self.of(family))

    def deepen(self, family: str, step: float) -> str | None:
        """Advance your understanding of a family a small, trust-gated step. When
        it crosses a milestone you *earn one of their words* — a prize. Returns the
        concept earned this step, or None."""
        before = self.of(family)
        after = min(1.0, before + self.trust_gain(family, step))
        self.understanding[family] = after
        return self._prize(family, before, after)

    def _prize(self, family: str, before: float, after: float) -> str | None:
        n = len(CONCEPTS)
        if int(after * n) <= int(before * n):
            return None
        for concept in CONCEPTS:
            if concept not in self.earned(family):
                self.words.setdefault(family, []).append(concept)
                return concept
        return None

    # ---- skill in a trade (novice -> master, through use) -----------------
    def skill(self, trade: str) -> float:
        return self.skills.get(trade, 0.0)

    def practice(self, trade: str) -> float:
        """Grow a skill by doing it — fast while you're a novice, slower to master.
        Returns the new level."""
        cur = self.skill(trade)
        level = min(1.0, cur + config.SKILL_STEP * (1 - 0.7 * cur))
        self.skills[trade] = level
        return level
