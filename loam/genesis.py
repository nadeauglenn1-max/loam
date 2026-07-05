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
from typing import TYPE_CHECKING, Protocol

from . import config

if TYPE_CHECKING:  # pragma: no cover
    from .agent import Agent
    from .llm import LiveLLM

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


# ---- weavers: who authors the web -------------------------------------------
# The web can be woven two ways behind one seam (mirrors cognition.py): a free,
# deterministic RULE weaver (the default and the safe fallback), or a MODEL
# weaver where a chosen model authors the tensions. The engine consumes a
# CONTRACT — a validated list of ties — never the model's raw text; anything
# malformed falls back to the rule weave, so any model plugs in and the web
# degrades gracefully instead of breaking.


class Weaver(Protocol):
    def weave(self, agents, seed: int) -> tuple[int, int]:
        ...


class RuleWeaver:
    """The default: deterministic bonds and frictions from the seed."""

    def weave(self, agents, seed: int) -> tuple[int, int]:
        return weave_web(agents, seed)


_WEAVE_SYSTEM = (
    "You are the hidden history of a village. Given its founders, invent the ties "
    "that already run between them before the story starts — a few warm bonds and "
    "a few frictions, enough that the place feels lived-in (not every possible "
    "pair). Reply with one tie per line and NOTHING else, each EXACTLY:\n"
    "TIE: <NameA> | <NameB> | bond|friction | <strength 1-9> | <a short reason, from A's view>\n"
    "Use only the given names; do not invent people."
)


class ClaudeWeaver:
    """A model authors the web; the rule weaver catches every failure."""

    def __init__(self, llm: "LiveLLM", fallback: Weaver | None = None) -> None:
        self._llm = llm
        self._fallback = fallback or RuleWeaver()

    def weave(self, agents, seed: int) -> tuple[int, int]:
        beings = list(agents)
        if len(beings) < config.WEB_MIN_VILLAGE:
            return (0, 0)
        try:
            reply = self._llm.complete(
                tier=config.REFLECTIVE,
                system=_WEAVE_SYSTEM,
                user="The founders: " + ", ".join(b.name for b in beings) + ".",
                max_tokens=40 * len(beings),
            )
            ties = _parse_ties(reply, beings)
        except Exception:
            return self._fallback.weave(beings, seed)
        if not ties:                       # nothing usable came back — fall back
            return self._fallback.weave(beings, seed)
        return _apply_ties(ties)


def _parse_ties(reply: str, beings) -> list[tuple]:
    """Validate the model's reply into a list of ties the engine can apply.
    Unknown names, bad kinds, self-ties, and duplicate pairs are dropped."""
    names = {b.name.lower(): b for b in beings}
    ties: list[tuple] = []
    seen: set[frozenset[str]] = set()
    for line in reply.splitlines():
        line = line.strip()
        if not line.upper().startswith("TIE:"):
            continue
        parts = [p.strip() for p in line[4:].split("|")]
        if len(parts) < 4:
            continue
        a, b = names.get(parts[0].lower()), names.get(parts[1].lower())
        kind = parts[2].lower()
        if a is None or b is None or a is b or kind not in ("bond", "friction"):
            continue
        key = frozenset((a.id, b.id))
        if key in seen:
            continue
        seen.add(key)
        try:
            strength = float(parts[3].split()[0])
        except (ValueError, IndexError):
            strength = 5.0
        note = parts[4] if len(parts) >= 5 else ""
        ties.append((a, b, kind == "bond", strength, note))
    return ties


def _apply_ties(ties) -> tuple[int, int]:
    bonds = frictions = 0
    for a, b, is_bond, strength, note in ties:
        lo, hi = config.WEB_BOND_RANGE if is_bond else config.WEB_TENSION_RANGE
        mag = max(lo, min(hi, strength / 9 * hi))
        sign = 1 if is_bond else -1
        a.warm_to(b.id, sign * mag)
        b.warm_to(a.id, sign * mag)
        a.memory.remember(0, note or (f"has a history with {b.name}" if is_bond
                                      else f"is wary of {b.name}"))
        b.memory.remember(0, f"a history with {a.name}" if is_bond
                          else f"keeps a distance from {a.name}")
        bonds += is_bond
        frictions += not is_bond
    return (bonds, frictions)
