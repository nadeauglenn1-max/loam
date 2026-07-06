"""Zones — dangerous areas as data, rolled into monsters by the one combat engine."""
import random

from loam import bestiary, config, zones
from loam.world import World


def test_every_zone_spawns_a_real_monster():
    """The moddable contract: a zone may only spawn kinds the bestiary knows."""
    for name in zones.list_zones():
        for kind, weight, lo, hi in zones.spawn_table(name):
            assert kind in bestiary.BESTIARY, f"{name} spawns unknown '{kind}'"
            assert weight > 0 and 1 <= lo <= hi


def test_overlay_zone_inherits_place_danger():
    # a wild zone restates no danger — it reads its place's, one source of truth
    assert "danger" not in zones.ZONES["the deepwood"]
    assert zones.danger_of("the deepwood") == config.PLACES["the deepwood"]["danger"]
    assert zones.location_of("the deepwood") == "the deepwood"


def test_standalone_zone_carries_its_own_danger_and_location():
    assert zones.danger_of("the hollow cave") == zones.ZONES["the hollow cave"]["danger"]
    # a cave isn't a map place — its monsters live at the zone itself
    assert zones.location_of("the hollow cave") == "the hollow cave"
    assert "the hollow cave" not in config.PLACES


def test_populate_rolls_the_table_at_the_zones_location():
    monsters = zones.populate("the sunken barrow", random.Random(1), count=6)
    assert len(monsters) == 6
    kinds = {m.kind for m in monsters}
    assert kinds <= {"lurker", "cave troll"}          # only what the table lists
    assert all(m.location == "the sunken barrow" for m in monsters)
    assert all(m.level >= 3 for m in monsters)         # the barrow spawns level 3+


def test_populate_is_deterministic_given_the_rng():
    a = zones.populate("the hollow cave", random.Random(4))
    b = zones.populate("the hollow cave", random.Random(4))
    assert [(m.kind, m.level) for m in a] == [(m.kind, m.level) for m in b]


def test_populate_defaults_to_the_configured_count():
    monsters = zones.populate("the mire", random.Random(0))
    assert len(monsters) == config.ZONE_SPAWN_DEFAULT


def test_world_populates_a_zone_and_locates_its_monsters():
    w = World.seeded(n_agents=4, seed=7)
    assert w.populate_zone("nowhere", random.Random(0)) == []      # unknown zone
    spawned = w.populate_zone("the hollow cave", random.Random(0), count=4)
    assert len(spawned) == 4
    assert all(m in w.monsters for m in spawned)
    assert w.monsters_at("the hollow cave") == spawned


def test_zone_monsters_survive_a_save_and_load(tmp_path):
    from loam import persistence
    w = World.seeded(n_agents=4, seed=7)
    w.populate_zone("the deepwood", random.Random(3))
    path = tmp_path / "w.json"
    persistence.save(w, path)
    reloaded = persistence.load(path)
    assert len(reloaded.monsters) == len(w.monsters)
    assert {m.kind for m in reloaded.monsters} == {m.kind for m in w.monsters}
