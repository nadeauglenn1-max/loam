"""Genome — the heritable core of a being.

Carries what a child can inherit (with drift): its appetites (which wants pull
hardest), its skills at foraging and growing, and how long it may live. Language
is heritable too, but lives in language.py.

Genesis genomes are deterministic from an id (a world reloads identically).
Inherited genomes are stochastic — a child blends its parents and mutates, so it
may echo them or diverge sharply.
"""
from __future__ import annotations

import hashlib
import random as _random
from dataclasses import dataclass, field

from . import config
from .config import CONCEPTS


def _unit(seed: str) -> float:
    """Deterministic float in [0, 1) from a string seed."""
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _clamp(x: float, lo: float = 0.05, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


@dataclass
class Genome:
    appetites: dict[str, float] = field(default_factory=dict)  # per-concept pull
    forage_skill: float = 0.5                                  # 0..1
    grow_skill: float = 0.5                                    # 0..1
    lifespan: int = config.LIFESPAN_MEAN

    @classmethod
    def genesis(cls, agent_id: str) -> "Genome":
        appetites = {c: _clamp(0.1 + 0.9 * _unit(f"{agent_id}:app:{c}")) for c in CONCEPTS}
        # A being tends to be gifted at one of the two ways of getting bloom.
        lean = _unit(f"{agent_id}:lean")
        forage = _clamp(0.25 + 0.6 * lean + 0.15 * _unit(f"{agent_id}:forage"))
        grow = _clamp(0.25 + 0.6 * (1 - lean) + 0.15 * _unit(f"{agent_id}:grow"))
        span = config.LIFESPAN_MEAN + int((_unit(f"{agent_id}:span") - 0.5) * 2 * config.LIFESPAN_SPREAD)
        return cls(appetites=appetites, forage_skill=forage, grow_skill=grow, lifespan=span)

    @classmethod
    def inherit(cls, a: "Genome", b: "Genome", rng: _random.Random) -> "Genome":
        """Blend two parents with mutation. Each gene is drawn from one parent,
        then nudged — so a child may take after either, both, or neither."""
        appetites = {}
        for c in CONCEPTS:
            base = rng.choice((a.appetites[c], b.appetites[c]))
            appetites[c] = _clamp(base + rng.gauss(0, config.APPETITE_MUTATION))
        forage = _clamp(rng.choice((a.forage_skill, b.forage_skill))
                        + rng.gauss(0, config.SKILL_MUTATION))
        grow = _clamp(rng.choice((a.grow_skill, b.grow_skill))
                      + rng.gauss(0, config.SKILL_MUTATION))
        span = int((a.lifespan + b.lifespan) / 2 + rng.gauss(0, config.LIFESPAN_MUTATION))
        span = max(120, span)
        return cls(appetites=appetites, forage_skill=forage, grow_skill=grow, lifespan=span)
