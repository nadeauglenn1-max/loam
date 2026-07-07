"""The bestiary — monsters as data-driven entities.

A monster is an *entity* (its own vitality, stats, and place), spawned from a
**registry** of kinds. The registry is plain data, so adding a new monster is
adding a row — the seam that makes zones moddable later. Monsters carry the same
combat interface as beings (``combat_attack`` / ``combat_defense`` / ``level`` /
``vitality``), so the one combat engine resolves any fight, being or beast.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import config

# kind -> base stats. attack/defense are 0..1 (like a genome); hp is starting
# vitality (can exceed 1 for tanks); xp is the reward for felling it at level 1.
BESTIARY: dict[str, dict] = {
    "cave rat":     {"attack": 0.22, "defense": 0.18, "hp": 0.4, "xp": 1},
    "goblin":       {"attack": 0.30, "defense": 0.22, "hp": 0.5, "xp": 2},
    "wolf":         {"attack": 0.40, "defense": 0.28, "hp": 0.7, "xp": 2},
    "giant spider": {"attack": 0.44, "defense": 0.30, "hp": 0.8, "xp": 3},
    "boar":         {"attack": 0.48, "defense": 0.40, "hp": 1.0, "xp": 3},
    "bandit":       {"attack": 0.50, "defense": 0.44, "hp": 1.2, "xp": 4},
    "bog serpent":  {"attack": 0.52, "defense": 0.36, "hp": 1.1, "xp": 4},
    "lurker":       {"attack": 0.58, "defense": 0.46, "hp": 1.4, "xp": 5},
    "the beast":    {"attack": 0.60, "defense": 0.50, "hp": 1.6, "xp": 6},
    "bear":         {"attack": 0.64, "defense": 0.52, "hp": 1.9, "xp": 7},
    "wraith":       {"attack": 0.70, "defense": 0.40, "hp": 1.5, "xp": 9},
    "cave troll":   {"attack": 0.72, "defense": 0.68, "hp": 3.0, "xp": 12},
}


@dataclass
class Monster:
    kind: str
    name: str
    combat_attack: float
    combat_defense: float
    vitality: float          # current hp (damage comes off this, like a being's)
    max_vitality: float
    xp_reward: int           # xp granted to whoever fells it
    level: int = 1
    location: str = ""
    alive: bool = True

    @property
    def condition(self) -> str:
        r = self.vitality / self.max_vitality if self.max_vitality else 0.0
        return "wounded" if r < 0.35 else "hurt" if r < 0.7 else "prowling"


def list_kinds() -> list[str]:
    return sorted(BESTIARY)


def spawn(kind: str, location: str = "", level: int = 1, name: str | None = None) -> Monster:
    """Make a monster of `kind`. Higher level scales its hp; stronger foes give
    proportionally more xp."""
    s = BESTIARY[kind]
    hp = s["hp"] * (1 + config.LEVEL_POWER_GAIN * (level - 1))
    return Monster(kind=kind, name=name or kind, combat_attack=s["attack"],
                   combat_defense=s["defense"], vitality=hp, max_vitality=hp,
                   xp_reward=int(s["xp"] * level), level=level, location=location)
