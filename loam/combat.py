"""Combat & leveling — how a fight resolves, and how fighters grow.

Health is a being's **vitality** (the same bar hunger and the wild already drain),
so there is one source of truth for how alive something is. **Attack** and
**defense** are heritable genome aptitudes; **level** and earned **xp** raise a
fighter's effective power. Resolution is deterministic given the rng, so the
engine is free, testable, and shared by villagers, monsters, and the player alike.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from . import config

if TYPE_CHECKING:  # pragma: no cover
    import random

    from .agent import Agent


def _level_scale(level: int) -> float:
    return 1 + config.LEVEL_POWER_GAIN * (level - 1)


def attack_power(f) -> float:
    return f.combat_attack * _level_scale(f.level)


def defense_power(f) -> float:
    return f.combat_defense * _level_scale(f.level)


def hit_damage(attacker: "Agent", defender: "Agent", rng: "random.Random") -> float:
    """Vitality a single blow takes — attack weighed against defense, with a swing.
    Evenly matched, a clean hit costs about ``ATTACK_DAMAGE``."""
    atk, dfn = attack_power(attacker), defense_power(defender)
    ratio = atk / (atk + dfn) if (atk + dfn) else 0.5
    swing = 1 + rng.uniform(-config.COMBAT_VARIANCE, config.COMBAT_VARIANCE)
    return max(0.0, config.ATTACK_DAMAGE * 2 * ratio * swing)


def xp_to_next(level: int) -> int:
    return config.XP_PER_LEVEL * level


def award_xp(fighter: "Agent", amount: int) -> int:
    """Add xp and return how many levels were gained."""
    fighter.xp += amount
    gained = 0
    while fighter.xp >= xp_to_next(fighter.level):
        fighter.xp -= xp_to_next(fighter.level)
        fighter.level += 1
        gained += 1
    return gained
