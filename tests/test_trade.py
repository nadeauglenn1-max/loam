"""Trade between beings — surplus goods circulate so the craft chains flow."""
from conftest import ScriptedRandom

from loam import crafts
from loam.cognition import Decision, RuleCognition
from loam.world import World


def _w():
    return World.seeded(n_agents=4, seed=7)


def test_needs_good_knows_who_can_use_a_good():
    assert crafts.needs_good("smithing", "ingot")      # smithing consumes ingots
    assert crafts.needs_good("weaving", "wool")
    assert not crafts.needs_good("weaving", "ore")     # weaving has no use for ore
    assert not crafts.needs_good("fishing", "wool")    # a gather consumes nothing


def test_hand_goods_moves_surplus_and_warms_the_bond():
    w = _w()
    a, b = w.agents["a0"], w.agents["a1"]
    a.relationships.clear(); b.relationships.clear()    # isolate from the genesis web
    b.location = a.location
    a.goods["wool"] = 5.0
    out = w.hand_goods(a, b.id, "wool", ScriptedRandom())
    assert out["ok"] and out["good"] == "wool"
    assert a.goods["wool"] == 3.0 and b.goods["wool"] == 2.0    # 2 handed over
    assert a.affinity(b.id) > 0 and b.affinity(a.id) > 0
    assert w.tally.get("trades", 0) == 1


def test_hand_goods_refuses_across_places_or_with_nothing():
    w = _w()
    a, b = w.agents["a0"], w.agents["a1"]
    b.location = "the deepwood"                                  # not beside a
    a.goods["wool"] = 5.0
    assert not w.hand_goods(a, b.id, "wool", ScriptedRandom())["ok"]
    b.location = a.location
    assert not w.hand_goods(a, b.id, "ore", ScriptedRandom())["ok"]   # holds no ore


def test_a_gatherer_hands_surplus_to_a_neighbour_who_needs_it():
    w = _w()
    a, b = w.agents["a0"], w.agents["a1"]
    a.vocation, b.vocation = "husbandry", "weaving"   # a makes wool; b weaves it
    a.location = b.location = "the commons"
    a.vitality, a.bloom, a.age = 0.9, 3.0, 10         # sated child: past food/breed/give
    w.tick = 12                                        # midday, not night
    a.relationships.clear(); a.warm_to(b.id, 2)
    a.goods["wool"] = 4.0
    # trade is the first branch that draws here — script it to fire
    d = RuleCognition().decide(a, w, ScriptedRandom([0.0]))
    assert d.kind == "trade" and d.target == b.id and d.good == "wool"


def test_trade_decision_is_applied_by_the_world():
    w = _w()
    a, b = w.agents["a0"], w.agents["a1"]
    b.location = a.location
    b.vocation = "weaving"
    a.goods["wool"] = 4.0
    w._apply(a, Decision("trade", target=b.id, good="wool"), ScriptedRandom())
    assert b.goods.get("wool", 0) > 0
