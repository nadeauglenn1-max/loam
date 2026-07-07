"""The arena — a fight resolved, apart from the world.

Combat happens in its own scene you *enter*: you against one foe, to the finish.
This module is the pure model of that fight — who the fighters are and how a blow
lands — so it is free and testable; the pygame scene (game/combat.py) draws it and
takes your input, and tunes the *feel*.

You are no warrior at the start. Your power in a fight comes from your combat
skill, which grows only by fighting — you learn to fight by being fought. So the
first rats are a real test, and a troll is a long way off.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import combat, config


@dataclass
class Fighter:
    name: str
    combat_attack: float
    combat_defense: float
    vitality: float
    max_vitality: float
    level: int = 1

    @property
    def condition(self) -> str:
        r = self.vitality / self.max_vitality if self.max_vitality else 0.0
        return "beaten" if r <= 0 else "reeling" if r < 0.3 else "hurt" if r < 0.7 else "steady"


def player_fighter(player, name: str = "You") -> Fighter:
    """Your fighting self, built from your combat skill (and no more — a novice is
    weak, and grows only by fighting)."""
    skill = player.skill("combat")
    atk = min(1.0, config.FIGHT_BASE_ATTACK + config.FIGHT_SKILL_ATTACK * skill)
    dfn = min(1.0, config.FIGHT_BASE_DEFENSE + config.FIGHT_SKILL_DEFENSE * skill)
    hp = config.FIGHT_BASE_VIGOR + config.FIGHT_SKILL_VIGOR * skill
    return Fighter(name, atk, dfn, hp, hp)


def resolve_blow(attacker, defender, rng, bracing: bool = False) -> float:
    """One blow: damage off the defender's vitality (a braced defender takes far
    less). Returns the damage dealt."""
    dmg = combat.hit_damage(attacker, defender, rng)
    if bracing:
        dmg *= config.FIGHT_BRACE
    defender.vitality = max(0.0, defender.vitality - dmg)
    return dmg


def reward_win(player, foe_level: int) -> int:
    """Fighting is how you learn to fight: a win grows your combat skill (more from
    a tougher foe). Returns the whole-percent your skill rose."""
    before = player.skill("combat")
    for _ in range(max(1, foe_level)):
        player.practice("combat")
    return round((player.skill("combat") - before) * 100)
