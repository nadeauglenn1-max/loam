"""Zones — the dangerous places, as data.

A zone is content: a named area, a danger level, and a **spawn table** of which
monsters appear there and at what strength. "Build a cave or a dungeon" is
adding a row to ``ZONES`` — the same moddable seam as the :mod:`bestiary`.

A zone that overlays a map place inherits that place's danger, so danger lives
in exactly one spot; a standalone zone — a cave, a barrow, somewhere you travel
to and fight — carries its own. Its monsters are the same entities the one
combat engine already resolves, so a populated zone is a place you can fight
through the moment the client lets you enter it.
"""
from __future__ import annotations

import random

from . import bestiary, config
from .config import PLACES

# A spawn table is a tuple of rules: (monster kind, weight, min level, max level).
# Weight sets how often a kind is rolled; the level range scales its strength.
ZONES: dict[str, dict] = {
    # overlays on the wild map — danger is inherited from the place it covers
    "the mire": {
        "place": "the mire", "kind": "wild",
        "spawns": (("cave rat", 3, 1, 2), ("wolf", 2, 1, 2)),
    },
    "the thornwood": {
        "place": "the thornwood", "kind": "wild",
        "spawns": (("wolf", 3, 1, 3), ("boar", 2, 1, 2)),
    },
    "the deepwood": {
        "place": "the deepwood", "kind": "wild",
        # the beast that haunts the forage is also a foe you can face here
        "spawns": (("boar", 2, 1, 3), ("lurker", 2, 2, 4), ("the beast", 1, 2, 4)),
    },
    # standalone areas you travel to and fight — add a row like these to build one
    "the hollow cave": {
        "danger": 0.60, "kind": "cave",
        "spawns": (("cave rat", 4, 1, 3), ("lurker", 2, 2, 4)),
    },
    "the sunken barrow": {
        "danger": 0.85, "kind": "dungeon",
        "spawns": (("lurker", 2, 3, 5), ("cave troll", 1, 3, 6)),
    },
}


def list_zones() -> list[str]:
    return sorted(ZONES)


def location_of(name: str) -> str:
    """Where a zone's monsters live: the place it overlays, or the zone itself."""
    return ZONES[name].get("place", name)


def danger_of(name: str) -> float:
    z = ZONES[name]
    return PLACES[z["place"]]["danger"] if "place" in z else z["danger"]


def spawn_table(name: str) -> tuple:
    return ZONES[name]["spawns"]


def populate(name: str, rng: random.Random, count: int | None = None) -> list[bestiary.Monster]:
    """Roll a zone's spawn table into live monsters. Deterministic given `rng`."""
    table = spawn_table(name)
    loc = location_of(name)
    kinds = [r[0] for r in table]
    weights = [r[1] for r in table]
    if count is None:
        count = config.ZONE_SPAWN_DEFAULT
    out: list[bestiary.Monster] = []
    for _ in range(count):
        kind = rng.choices(kinds, weights=weights, k=1)[0]
        _, _, lo, hi = next(r for r in table if r[0] == kind)
        out.append(bestiary.spawn(kind, loc, rng.randint(lo, hi)))
    return out
