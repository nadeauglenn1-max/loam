"""Vocations — the trades given a place in the living village."""
import random

from conftest import ScriptedRandom

from loam import cast, crafts
from loam.cognition import Decision, RuleCognition
from loam.world import World


def test_founders_and_born_and_children_all_have_a_trade():
    w = cast.build_base(seed=7)
    assert all(a.vocation for a in w.agents.values())
    # a story-named craft is honored; a family default otherwise
    assert next(a for a in w.agents.values() if a.name == "Odile").vocation == "weaving"
    assert next(a for a in w.agents.values() if a.name == "Odo").vocation == "fishing"
    # a plain-born being takes up a gather trade (no inputs needed to start)
    from loam.agent import Agent
    born = Agent.born(99)
    assert born.vocation in crafts.GATHER_TRADES


def test_a_child_takes_up_a_parents_trade():
    from loam.agent import Agent
    mother = Agent.born(1)
    mother.vocation = "smithing"
    father = Agent.born(2)
    child = Agent.child("a3", mother, father, random.Random(0))
    assert child.vocation == "smithing"


def _villager(vocation, vitality=1.0, location="the hearth"):
    w = World.seeded(n_agents=4, seed=7)
    a = w.agents["a0"]
    a.vocation, a.vitality, a.location = vocation, vitality, location
    a.age, a.bloom = 10, 5.0        # a sated child: past no food/breed/give branches
    w.tick = 12                     # midday, not night
    return w, a


# work sits after seek: script the seek draw to miss (0.99), the work draw to hit (0.0)
def test_a_well_fed_villager_works_a_gather_where_they_stand():
    w, a = _villager("husbandry", location="the hearth")   # husbandry works at the hearth
    d = RuleCognition().decide(a, w, ScriptedRandom([0.99, 0.0]))
    assert d.kind == "work"


def test_a_villager_travels_to_safe_ground_for_their_trade():
    w, a = _villager("herbalism", location="the hearth")   # herbalism is at the safe meadow
    d = RuleCognition().decide(a, w, ScriptedRandom([0.99, 0.0]))
    assert d.kind == "move" and d.place == "the meadow"


def test_a_villager_will_not_travel_to_risky_ground_but_works_it_if_there():
    # fishing is at the mire (risky): a villager won't march there to fish…
    w, a = _villager("fishing", location="the hearth")
    assert RuleCognition().decide(a, w, ScriptedRandom([0.99, 0.0])).kind != "work"
    # …but if the food loop already has them at the mire, they'll fish it
    w2, a2 = _villager("fishing", location="the mire")
    assert RuleCognition().decide(a2, w2, ScriptedRandom([0.99, 0.0])).kind == "work"


def test_a_perilous_trade_is_not_worked_automatically():
    w, a = _villager("mining", location="the deepwood")    # mining is dangerous — player-only
    d = RuleCognition().decide(a, w, ScriptedRandom([0.99, 0.0]))
    assert d.kind != "work"


def test_a_hungry_villager_will_not_stop_to_work():
    w, a = _villager("husbandry", vitality=0.3, location="the hearth")
    a.bloom = 0.0
    d = RuleCognition().decide(a, w, ScriptedRandom([0.0]))
    assert d.kind != "work"                                 # survival comes first


def test_working_produces_goods_through_the_world():
    w, a = _villager("husbandry", location="the hearth")
    w._apply(a, Decision("work"), random.Random(0))
    assert a.goods.get("meat", 0) > 0 or a.goods.get("wool", 0) > 0
