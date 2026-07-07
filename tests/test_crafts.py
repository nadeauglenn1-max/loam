"""Professions and goods — the working economy, as data on the one recipe engine."""
import random

from conftest import ScriptedRandom

from loam import config, crafts
from loam.world import World


def _w():
    return World.seeded(n_agents=4, seed=7)


def test_every_profession_references_real_goods_and_places():
    """The moddable contract: a trade may only use goods the registry knows and
    places the map (or a zone) actually has."""
    from loam import zones
    known_places = set(config.PLACES) | set(zones.ZONES)
    for name, p in crafts.PROFESSIONS.items():
        assert p.kind in ("gather", "craft")
        assert p.places and set(p.places) <= known_places, f"{name} at an unknown place"
        for good in {**p.inputs, **p.yields}:
            assert good in crafts.GOODS, f"{name} uses unknown good '{good}'"


def test_gather_produces_goods_scaled_by_skill():
    prof = crafts.PROFESSIONS["fishing"]
    goods: dict[str, float] = {}
    out = crafts.perform(prof, skill=1.0, location="the mire", goods=goods, rng=random.Random(0))
    assert out.ok and out.produced["fish"] > 0
    assert goods["fish"] == out.produced["fish"]
    # a more skilled hand yields more
    lo, hi = {}, {}
    crafts.perform(prof, skill=0.0, location="the mire", goods=lo, rng=random.Random(0))
    crafts.perform(prof, skill=1.0, location="the mire", goods=hi, rng=random.Random(0))
    assert hi["fish"] > lo["fish"]


def test_a_craft_consumes_its_inputs():
    prof = crafts.PROFESSIONS["smelting"]
    goods = {"ore": 5.0}
    out = crafts.perform(prof, skill=0.5, location="the hearth", goods=goods, rng=random.Random(1))
    assert out.ok and out.produced["ingot"] > 0
    assert goods["ore"] == 3.0                      # 2 ore consumed
    assert goods["ingot"] == out.produced["ingot"]


def test_a_craft_refuses_without_inputs_or_at_the_wrong_place():
    smith = crafts.PROFESSIONS["smithing"]
    assert not crafts.perform(smith, skill=1.0, location="the hearth",
                              goods={}, rng=random.Random(0)).ok          # no ingots
    assert not crafts.perform(smith, skill=1.0, location="the meadow",
                              goods={"ingot": 9}, rng=random.Random(0)).ok  # wrong place


def test_a_held_tool_sharpens_a_gather():
    prof = crafts.PROFESSIONS["mining"]
    bare, shod = {}, {"tool": 1.0}
    crafts.perform(prof, skill=0.4, location="the deepwood", goods=bare, rng=random.Random(2))
    crafts.perform(prof, skill=0.4, location="the deepwood", goods=shod, rng=random.Random(2))
    assert shod["ore"] > bare["ore"]


def test_a_wielded_weapon_sharpens_combat():
    hero = _w().agents["a0"]
    base = hero.combat_attack
    hero.goods["weapon"] = 1.0
    assert hero.combat_attack > base
    assert hero.combat_attack == min(1.0, hero.genome.attack + crafts.GOODS["weapon"]["bonus"])


def test_world_do_craft_records_and_produces():
    w = _w()
    smith = w.agents["a0"]
    smith.location = "the hearth"
    smith.goods["ore"] = 4.0
    out = w.do_craft(smith, "smelting", random.Random(0))
    assert out.ok and smith.goods["ingot"] > 0
    assert any("smelting" in m for m in smith.memory.recent())
    assert w.tally.get("craft_smelting", 0) == 1


def test_world_do_craft_rejects_unknown_trade():
    w = _w()
    assert not w.do_craft(w.agents["a0"], "alchemy", random.Random(0)).ok


def test_a_risky_trade_can_wound_but_not_kill():
    w = _w()
    a = w.agents["a0"]
    a.location, a.genome.craft_skill, a.vitality = "the deepwood", 0.0, 1.0
    # first draw triggers the mishap; second draw spares it from being fatal
    out = w.do_craft(a, "mining", ScriptedRandom([0.0, 0.99]))
    assert out.ok and out.hurt and not out.fatal
    assert a.alive and a.vitality == 1.0 - config.CRAFT_INJURY_COST


def test_a_grave_mishap_can_be_fatal():
    w = _w()
    a = w.agents["a0"]
    a.location, a.genome.craft_skill, a.vitality = "the deepwood", 0.0, 1.0
    out = w.do_craft(a, "mining", ScriptedRandom([0.0, 0.0]))
    assert out.fatal and not a.alive and "a0" not in w.agents


def test_goods_and_craft_skill_survive_a_save(tmp_path):
    from loam import persistence
    w = _w()
    a = w.agents["a0"]
    a.goods = {"ore": 3.0, "weapon": 1.0}
    a.vocation = "smithing"
    a.genome.craft_skill = 0.77
    path = tmp_path / "w.json"
    persistence.save(w, path)
    b = persistence.load(path).agents["a0"]
    assert b.goods == {"ore": 3.0, "weapon": 1.0}
    assert b.vocation == "smithing" and b.genome.craft_skill == 0.77
