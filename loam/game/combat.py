"""The combat scene's state machine — a real-time fight you can play.

Kept thin and apart: `arena.py` is the pure model (the numbers, and how skill
grows), this holds only the *timing* of a fight — your strike cooldown, the foe's
telegraphed blows, and bracing — and `game/explore.py` drives and draws it. The
cadences below are the **feel**, the thing meant to be tuned by playing.
"""
from __future__ import annotations

import random

from .. import arena


class Fight:
    STRIKE_CD = 0.40        # your blow recovers this fast (seconds)
    ENEMY_CADENCE = 1.45    # the foe strikes about this often
    TELEGRAPH = 0.50        # and winds up (a flash) this long before each blow

    def __init__(self, world, monster) -> None:
        self.world = world
        self.you = arena.player_fighter(world.player)
        self.foe = monster
        self.cooldown = 0.0
        self.enemy_timer = self.ENEMY_CADENCE
        self.telegraph = 0.0
        self.bracing = False
        self.over: str | None = None      # None | "won" | "lost" | "fled"
        self.reward = 0
        self.log: list[str] = []
        self._rng = random.Random(f"{world.tick}:{monster.kind}:{monster.vitality:.3f}")

    def strike(self) -> None:
        if self.over or self.cooldown > 0 or self.bracing:
            return
        dmg = arena.resolve_blow(self.you, self.foe, self._rng)
        self.cooldown = self.STRIKE_CD
        self.log.append(f"you strike for {dmg:.2f}")
        if self.foe.vitality <= 0:
            self.over = "won"
            self.reward = arena.reward_win(self.world.player, self.foe.level)
            self._record()

    def flee(self) -> None:
        if not self.over:
            self.over = "fled"
            self._record()

    def update(self, dt: float) -> None:
        if self.over:
            return
        self.cooldown = max(0.0, self.cooldown - dt)
        self.enemy_timer -= dt
        self.telegraph = self.enemy_timer if 0 < self.enemy_timer <= self.TELEGRAPH else 0.0
        if self.enemy_timer <= 0:
            dmg = arena.resolve_blow(self.foe, self.you, self._rng, bracing=self.bracing)
            self.log.append(f"{self.foe.name} strikes for {dmg:.2f}")
            self.enemy_timer = self.ENEMY_CADENCE
            if self.you.vitality <= 0:
                self.over = "lost"
                self._record()

    def _record(self) -> None:
        """Leave a mark on the world — a fight should show in the logs and the
        chronicle, not vanish with the scene."""
        foe, lvl = self.foe.name, self.foe.level
        if self.over == "won":
            self.world._bump("felled_by_you")
            self.world._log(f"You felled a {foe} (level {lvl}); +{self.reward}% at arms.")
        elif self.over == "lost":
            self.world._bump("beaten_back")
            self.world._log(f"A {foe} (level {lvl}) beat you back.")
        elif self.over == "fled":
            self.world._log(f"You fled from a {foe}.")
