"""Rifts — the gaps between you and the families you do not yet understand.

A rift is the story's atom: a family whose tongue is still closed to you. You
close it by helping them (the quest primitive, built next), and your
understanding of them rises toward complete. The tiers of the game are just the
families themselves — no hand-authored levels; the world's own households are the
ladder. Finish one, move to the next; when no rifts remain, you have become the
one who understands.
"""
from __future__ import annotations

from dataclasses import dataclass, field

UNBOUND = "Unbound"


def family_of(agent) -> str:
    return agent.home or UNBOUND


def families(world) -> list[str]:
    """Every household still alive in the world, in a stable order."""
    return sorted({family_of(a) for a in world.living()})


@dataclass
class Rift:
    family: str
    level: float                       # how far your understanding has come, 0..1
    members: list = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.members)

    @property
    def closed(self) -> bool:
        return self.level >= 1.0

    @property
    def started(self) -> bool:
        return 0.0 < self.level < 1.0


def open_rifts(world) -> list[Rift]:
    """The families you have not yet understood, the one you've already begun
    first (finish what you started), then the untouched by size."""
    rifts = []
    for fam in families(world):
        level = world.player.of(fam)
        if level >= 1.0:
            continue
        members = [a for a in world.living() if family_of(a) == fam]
        rifts.append(Rift(fam, level, members))
    rifts.sort(key=lambda r: (r.level == 0.0, -r.level, -r.size, r.family))
    return rifts


def progress(world) -> tuple[float, int, int]:
    """Your understanding across the village: (fraction, understood, total)."""
    fams = families(world)
    if not fams:
        return (0.0, 0, 0)
    understood = sum(1 for f in fams if world.player.understands(f))
    return (understood / len(fams), understood, len(fams))


def all_understood(world) -> bool:
    return bool(families(world)) and not open_rifts(world)
