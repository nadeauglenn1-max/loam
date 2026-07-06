"""Monsters as data-driven entities that fight by the same combat engine."""
import random

from conftest import ScriptedRandom

from loam import bestiary, combat, persistence
from loam.world import World


def _w():
    return World.seeded(n_agents=4, seed=7)


def test_registry_and_spawn():
    assert "wolf" in bestiary.list_kinds()
    m = bestiary.spawn("wolf", "the thornwood")
    assert m.kind == "wolf" and m.location == "the thornwood" and m.alive
    assert m.vitality == m.max_vitality > 0 and m.xp_reward >= 1


def test_higher_level_is_tougher_and_worth_more():
    weak, strong = bestiary.spawn("wolf", level=1), bestiary.spawn("wolf", level=5)
    assert strong.max_vitality > weak.max_vitality
    assert strong.xp_reward > weak.xp_reward


def test_a_monster_fights_by_the_same_engine():
    being = _w().agents["a0"]
    beast = bestiary.spawn("the beast")
    assert combat.hit_damage(being, beast, ScriptedRandom()) > 0     # being hits monster
    assert combat.hit_damage(beast, being, ScriptedRandom()) > 0     # monster hits being


def test_world_spawns_and_locates_monsters():
    w = _w()
    assert w.spawn_monster("nope", "the meadow") is None             # unknown kind
    m = w.spawn_monster("boar", "the meadow")
    assert m in w.monsters
    assert w.monsters_at("the meadow") == [m]
    assert w.monsters_at("the hearth") == []


def test_a_being_fells_a_monster_and_gains_xp():
    w = _w()
    hero = w.agents["a0"]
    hero.genome.attack, hero.xp, hero.level = 1.0, 0, 1
    rat = w.spawn_monster("cave rat", hero.location)
    rat.vitality = 0.05                       # a finishing blow
    r = w.strike(hero, rat, random.Random(0))
    assert r["slain"] and not rat.alive and rat not in w.monsters
    assert hero.xp > 0 or hero.level > 1
    assert w.tally.get("monsters_felled", 0) == 1


def test_a_monster_can_slay_a_being():
    w = _w()
    victim = w.agents["a0"]
    victim.vitality = 0.02
    troll = w.spawn_monster("cave troll", victim.location)
    r = w.strike(troll, victim, random.Random(0))
    assert r["slain"] and not victim.alive and "a0" not in w.agents   # routed through the death path


def test_monsters_survive_a_save_and_load(tmp_path):
    w = _w()
    w.spawn_monster("lurker", "the deepwood", level=2)
    path = tmp_path / "w.json"
    persistence.save(w, path)
    m = persistence.load(path).monsters[0]
    assert m.kind == "lurker" and m.level == 2 and m.location == "the deepwood"


def test_monster_condition_reads_its_wounds():
    m = bestiary.spawn("boar")
    assert m.condition == "prowling"
    m.vitality = m.max_vitality * 0.5
    assert m.condition == "hurt"
    m.vitality = m.max_vitality * 0.1
    assert m.condition == "wounded"
