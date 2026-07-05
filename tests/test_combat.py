"""The combat & leveling engine — attack vs defense, damage off vitality, xp/levels."""
import random

from conftest import ScriptedRandom

from loam import combat
from loam.world import World


def _w():
    return World.seeded(n_agents=4, seed=7)


def test_stronger_attacker_hits_harder():
    w = _w()
    strong, weak, foe = w.agents["a0"], w.agents["a1"], w.agents["a2"]
    strong.genome.attack, weak.genome.attack = 0.9, 0.2
    foe.genome.defense = 0.5
    assert combat.hit_damage(strong, foe, ScriptedRandom()) > \
           combat.hit_damage(weak, foe, ScriptedRandom())


def test_defense_softens_the_blow():
    w = _w()
    a, tough, soft = w.agents["a0"], w.agents["a1"], w.agents["a2"]
    a.genome.attack = 0.6
    tough.genome.defense, soft.genome.defense = 0.9, 0.2
    assert combat.hit_damage(a, tough, ScriptedRandom()) < \
           combat.hit_damage(a, soft, ScriptedRandom())


def test_level_raises_power():
    a = _w().agents["a0"]
    base = combat.attack_power(a)
    a.level = 5
    assert combat.attack_power(a) > base
    assert combat.defense_power(a) > 0


def test_award_xp_levels_up_and_carries_the_remainder():
    a = _w().agents["a0"]
    a.level, a.xp = 1, 0
    gained = combat.award_xp(a, combat.xp_to_next(1) + 1)
    assert gained == 1 and a.level == 2 and a.xp == 1


def test_world_attack_wounds_then_slays():
    w = _w()
    a, t = w.agents["a0"], w.agents["a1"]
    t.location = a.location
    t.vitality = 1.0
    r = w.attack("a0", "a1", random.Random(0))
    assert r["ok"] and r["damage"] > 0 and t.vitality < 1.0

    t.vitality = 0.01                    # a finishing blow
    a.genome.attack = 1.0
    r2 = w.attack("a0", "a1", random.Random(0))
    assert r2["slain"] and not t.alive
    assert a.xp > 0 or a.level > 1       # the slayer earned something
    assert w.tally.get("attacks", 0) == 2


def test_attack_needs_the_two_to_be_together():
    w = _w()
    w.agents["a0"].location, w.agents["a1"].location = "the hearth", "the meadow"
    assert w.attack("a0", "a1", random.Random(0)) == {"ok": False}


def test_combat_stats_survive_a_save_and_load(tmp_path):
    from loam import persistence
    w = _w()
    w.agents["a0"].genome.attack = 0.77
    w.agents["a0"].level, w.agents["a0"].xp = 3, 2
    path = tmp_path / "w.json"
    persistence.save(w, path)
    a = persistence.load(path).agents["a0"]
    assert a.genome.attack == 0.77 and a.level == 3 and a.xp == 2
