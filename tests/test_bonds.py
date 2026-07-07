"""Bonds — helping builds a tie that can grow to love, marriage, and a child."""
import random

from loam import bonds, cast, config
from loam.player import Player
from loam.world import World


def _village():
    w = cast.build_base(seed=7)
    w.role, w.name = "play", "story"
    return w


def test_tiers_climb_from_stranger_to_betrothed():
    assert bonds.tier(0.0) == "a stranger"
    assert bonds.tier(0.4) == "a friend"
    assert bonds.tier(0.95) == "betrothed"
    assert bonds.tier(1.0, wed=True) == "wed"


def test_attraction_is_deterministic_and_bounded():
    w = _village()
    a = next(iter(w.agents.values()))
    assert bonds.attraction(a) == bonds.attraction(a)
    assert 0.0 <= bonds.attraction(a) <= 1.0
    assert bonds.attraction_word(0.9) == "striking"


def test_a_bond_deepens_slower_the_deeper_it_runs():
    early = bonds.growth(0.1, 0.5)
    late = bonds.growth(0.85, 0.5)
    assert early > late > 0                       # a marriage takes far more than a friendship


def test_you_are_drawn_faster_to_someone_you_like():
    assert bonds.growth(0.3, 0.9) > bonds.growth(0.3, 0.1)


def test_helping_builds_a_bond_with_the_person():
    w = _village()
    sela = next(a for a in w.agents.values() if a.name == "Sela")
    assert w.player.bond(sela.id) == 0.0
    r = w.aid(sela.id)
    assert r["bond"] > 0.0 and w.player.bond(sela.id) == r["bond"]


def test_marriage_must_be_grown_to():
    w = _village()
    sela = next(a for a in w.agents.values() if a.name == "Sela")
    assert not w.marry(sela.id)["ok"]             # a stranger — refused
    w.player.bonds[sela.id] = 0.95               # betrothed
    r = w.marry(sela.id)
    assert r["ok"] and w.player.spouse == sela.id
    # can't wed a second while already wed
    other = next(a for a in w.agents.values() if a.name == "Odile")
    w.player.bonds[other.id] = 0.95
    assert not w.marry(other.id)["ok"]


def test_a_child_is_born_of_you_and_your_spouse():
    w = _village()
    sela = next(a for a in w.agents.values() if a.name == "Sela")
    assert not w.bear_child(random.Random(0))["ok"]   # no spouse yet
    w.player.bonds[sela.id] = 0.95
    w.marry(sela.id)
    r = w.bear_child(random.Random(1))
    assert r["ok"]
    child = w.agents[r["child"]]
    assert child.parents == (sela.id, "you")
    assert r["child"] in w.player.children
    assert child.generation == sela.generation + 1


def test_bonds_survive_a_save(tmp_path):
    from loam import persistence
    w = _village()
    sela = next(a for a in w.agents.values() if a.name == "Sela")
    w.player.bonds[sela.id] = 0.6
    w.player.spouse = sela.id
    w.player.children = ["a99"]
    path = tmp_path / "w.json"
    persistence.save(w, path)
    p = persistence.load(path).player
    assert p.bond(sela.id) == 0.6 and p.spouse == sela.id and p.children == ["a99"]


def test_player_bond_helpers():
    p = Player()
    assert p.deepen_bond("x", 0.4) == 0.4
    assert p.deepen_bond("x", 5.0) == 1.0          # capped
