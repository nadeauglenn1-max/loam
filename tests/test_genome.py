import random

from loam import config
from loam.config import CONCEPTS
from loam.genome import Genome


def test_genesis_is_deterministic():
    a = Genome.genesis("a3")
    b = Genome.genesis("a3")
    assert a == b
    assert set(a.appetites) == set(CONCEPTS)
    assert 0.05 <= a.forage_skill <= 1.0
    assert 0.05 <= a.grow_skill <= 1.0


def test_genesis_differs_between_beings():
    assert Genome.genesis("a1") != Genome.genesis("a2")


def test_genesis_lifespan_in_range():
    for i in range(20):
        g = Genome.genesis(f"a{i}")
        assert abs(g.lifespan - config.LIFESPAN_MEAN) <= config.LIFESPAN_SPREAD


def test_inheritance_blends_within_bounds():
    a = Genome.genesis("a1")
    b = Genome.genesis("a2")
    rng = random.Random(0)
    child = Genome.inherit(a, b, rng)
    for c in CONCEPTS:
        assert 0.05 <= child.appetites[c] <= 1.0
    assert 0.05 <= child.forage_skill <= 1.0
    assert child.lifespan >= 120


def test_inheritance_varies_run_to_run():
    a, b = Genome.genesis("a1"), Genome.genesis("a2")
    kids = {Genome.inherit(a, b, random.Random(s)).lifespan for s in range(10)}
    assert len(kids) > 1  # mutation makes children differ
