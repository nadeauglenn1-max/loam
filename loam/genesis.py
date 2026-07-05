"""Genesis — the web a village is born into.

A world does not begin as a crowd of strangers. Before the first tick, its
founders are already tangled in one another: old friends and kin, a debt of
kindness owed, a rivalry never settled, a wrong never forgiven. These starting
bonds are not decoration — cognition already reads affinity, so from the first
breath a being feeds its friends, breeds with those it trusts, and preys on
those it resents. The story starts warm.

The weave is deterministic in the world's seed, so a base world is reproducible:
the same seed always wakes the same village into the same web.
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

from . import config

if TYPE_CHECKING:  # pragma: no cover
    from .agent import Agent

# Each archetype is (what the first feels about the second, what the second feels
# about the first). Bonds warm both ways; frictions chafe both ways. The two
# lines can differ — a debt runs in one direction even when the fondness is
# mutual.
_BONDS = (
    ("grew up alongside {name}", "grew up alongside {name}"),
    ("owes {name} an old kindness", "once carried {name} through a hard season"),
    ("has trusted {name} for as long as they can remember",
     "has trusted {name} for as long as they can remember"),
    ("came up through hard years beside {name}",
     "came up through hard years beside {name}"),
)
_FRICTIONS = (
    ("has never forgiven {name} for an old wrong",
     "knows {name} still holds it against them"),
    ("bristles at {name} — a rivalry with no clear start",
     "bristles at {name} — a rivalry with no clear start"),
    ("keeps a wary distance from {name}", "keeps a wary distance from {name}"),
)


def weave_web(agents, seed: int) -> tuple[int, int]:
    """Tangle a fresh village into a web of bonds and frictions.

    Mutates each being's relationships and plants a founding memory of every tie.
    Returns (bonds, frictions) woven. Deterministic in `seed`. A web is a
    property of a village: below ``WEB_MIN_VILLAGE`` beings, nothing is woven.
    """
    beings = list(agents)
    n = len(beings)
    if n < config.WEB_MIN_VILLAGE:
        return (0, 0)
    rng = random.Random(f"{seed}:web")
    target = round(n * config.WEB_TIES_PER_BEING)
    made: set[frozenset[str]] = set()
    bonds = frictions = 0
    attempts = 0
    while len(made) < target and attempts < target * 8:
        attempts += 1
        a, b = rng.sample(beings, 2)
        key = frozenset((a.id, b.id))
        if key in made:
            continue
        made.add(key)
        if rng.random() < config.WEB_BOND_FRACTION:
            _tie(a, b, _BONDS, config.WEB_BOND_RANGE, +1, rng)
            bonds += 1
        else:
            _tie(a, b, _FRICTIONS, config.WEB_TENSION_RANGE, -1, rng)
            frictions += 1
    return (bonds, frictions)


def _tie(a: "Agent", b: "Agent", archetypes, mag_range, sign: int,
         rng: random.Random) -> None:
    line_a, line_b = rng.choice(archetypes)
    lo, hi = mag_range
    base = rng.uniform(lo, hi)
    # one side may feel the tie more than the other — asymmetry keeps stories
    # alive (she adores him; he only tolerates her), but never flips its sign.
    other = base * (1 - rng.uniform(0.0, config.WEB_ASYMMETRY))
    a.warm_to(b.id, sign * base)
    b.warm_to(a.id, sign * other)
    a.memory.remember(0, line_a.format(name=b.name))
    b.memory.remember(0, line_b.format(name=a.name))
