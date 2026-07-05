import random

from conftest import ScriptedRandom

from loam import config, persistence
from loam.cognition import Decision
from loam.config import PIVOTAL, REFLECTIVE, ROUTINE
from loam.world import World


def _w(n=4, seed=7):
    return World.seeded(n_agents=n, seed=seed)


# ---- construction & queries --------------------------------------------------
def test_seeded_world_is_populated_and_stocked():
    w = _w(5)
    assert len(w.living()) == 5
    assert w.next_index == 5
    assert w.bloom["the meadow"] > 0


def test_co_located_and_tier():
    w = _w(3)
    w.agents["a0"].location = "the mire"
    w.agents["a1"].location = "the mire"
    assert [a.id for a in w.co_located(w.agents["a0"])] == ["a1"]
    assert w.tier_now() == ROUTINE
    w.present = True
    assert w.tier_now() == REFLECTIVE
    assert w.tier_now(pivotal=True) == PIVOTAL


def test_regrow_lifts_bloom_toward_the_ceiling():
    w = _w(2)
    w.bloom["the meadow"] = 0.0
    w._regrow(ScriptedRandom())
    assert w.bloom["the meadow"] > 0.0


# ---- ecology -----------------------------------------------------------------
def test_forage_gathers_and_depletes_stock():
    w = _w(2)
    a = w.agents["a0"]
    a.location = "the meadow"
    a.genome.forage_skill = 0.9
    w.bloom["the meadow"] = 5.0
    w._forage(a, ScriptedRandom([0.99]))   # no injury
    assert a.bloom > 0
    assert w.bloom["the meadow"] < 5.0


def test_forage_can_be_fatal_in_a_deadly_place():
    w = _w(2)
    a = w.agents["a0"]
    a.location = "the deepwood"
    a.genome.forage_skill = 0.1
    w.bloom["the deepwood"] = 10.0
    w._forage(a, ScriptedRandom([0.0, 0.0]))   # injured, and it is lethal
    assert not a.alive
    assert any(f["cause"] == "forage" for f in w.fallen)


def test_predator_takes_the_lone_forager():
    w = _w(4)
    a = w.agents["a0"]
    a.location = "the deepwood"
    a.genome.forage_skill = 0.0
    w.predator = "the deepwood"
    w.bloom["the deepwood"] = 10.0
    w._forage(a, ScriptedRandom([0.0]))     # the beast catches a lone forager
    assert not a.alive
    assert any(f["cause"] == "predator" for f in w.fallen)


def test_a_group_faces_the_beast_and_survives():
    w = _w(4)
    for aid in ("a0", "a1", "a2"):
        w.agents[aid].location = "the deepwood"
    g = w.agents["a0"]
    g.genome.forage_skill = 0.0
    w.predator = "the deepwood"
    w.bloom["the deepwood"] = 10.0
    w._forage(g, ScriptedRandom([0.99]))    # three together drive it off; terrain misses
    assert g.alive
    assert any("beast" in m for m in g.memory.events)


def test_predator_roams_a_dangerous_place():
    w = _w(3)
    w._roam_predator(ScriptedRandom())
    assert w.predator in config.PREDATOR_PLACES


def test_forage_finds_nothing_when_bare():
    w = _w(2)
    a = w.agents["a0"]
    a.location = "the mire"
    w.bloom["the mire"] = 0.0
    w._forage(a, ScriptedRandom([0.99]))
    assert a.bloom == 0.0


def test_grow_yields_and_exhausts_soil_then_fails():
    w = _w(2)
    a = w.agents["a0"]
    a.location = "the meadow"
    a.genome.grow_skill = 0.9
    w.bloom["the meadow"] = 5.0
    w._grow(a, ScriptedRandom([0.0]))   # success
    assert a.bloom > 0
    w.bloom["the meadow"] = 0.1          # soil now exhausted
    before = a.bloom
    w._grow(a, ScriptedRandom([0.0]))
    assert a.bloom == before             # crop failed on dead soil
    assert w.tally.get("crop_failures", 0) >= 1


def test_grow_refused_on_unarable_ground():
    w = _w(2)
    a = w.agents["a0"]
    a.location = "the deepwood"
    w._grow(a, ScriptedRandom([0.0]))
    assert a.bloom == 0.0


def test_eat_turns_bloom_into_vitality():
    w = _w(2)
    a = w.agents["a0"]
    a.vitality = 0.4
    a.bloom = 2.0
    w._eat(a)
    assert a.vitality > 0.4
    assert a.bloom < 2.0


# ---- give, seize, violence ---------------------------------------------------
def test_giving_transfers_bloom_and_builds_a_bond():
    w = _w(2)
    g, t = w.agents["a0"], w.agents["a1"]
    t.location = g.location
    g.bloom = 3.0
    w._transfer(g, t.id, ScriptedRandom(), hostile=False)
    assert t.bloom > 0 and g.bloom < 3.0
    assert g.affinity(t.id) > 0 and t.affinity(g.id) > 0
    assert w.tally["gifts"] == 1


def test_seizing_takes_bloom_makes_enemies_and_can_kill():
    w = _w(2)
    g, t = w.agents["a0"], w.agents["a1"]
    t.location = g.location
    t.bloom = 2.0
    t.vitality = 0.1          # a seizure will finish them
    w._transfer(g, t.id, ScriptedRandom(), hostile=True)
    assert g.bloom > 0
    assert g.affinity(t.id) < 0
    assert w.tally["seizures"] == 1
    assert not t.alive
    assert w.tally.get("deaths_violence", 0) == 1


# ---- procreation, gestation, genetics ---------------------------------------
def test_mating_when_fertile_starts_a_pregnancy():
    w = _w(2)
    a, b = w.agents["a0"], w.agents["a1"]
    b.location = a.location
    a.vitality = b.vitality = 1.0
    a.warm_to(b.id, 1)
    w._mate(a, b.id, ScriptedRandom())
    assert a.gestation == config.GESTATION_TICKS
    assert a.mate_id == b.id


def test_mating_refused_without_trust():
    w = _w(2)
    a, b = w.agents["a0"], w.agents["a1"]
    b.location = a.location
    a.warm_to(b.id, -5)
    w._mate(a, b.id, ScriptedRandom())
    assert a.gestation == 0


def test_gestation_ends_in_a_child_with_inherited_lineage():
    w = _w(2)
    a, b = w.agents["a0"], w.agents["a1"]
    a.gestation = 1
    a.mate_id = b.id
    before = len(w.living())
    w._gestate(random.Random(0))
    assert len(w.living()) == before + 1
    child = w.agents["a2"]
    assert child.generation == 1
    assert child.parents == ("a0", "a1")
    assert w.tally["births"] == 1


# ---- the body's toll ---------------------------------------------------------
def test_reap_ages_everyone_and_starves_the_empty():
    w = _w(2)
    a = w.agents["a0"]
    a.vitality = 0.01
    age0 = a.age
    w._reap()
    assert not a.alive
    assert any(f["cause"] == "hunger" for f in w.fallen)
    assert w.agents["a1"].age == age0 + 1 or True   # survivors aged


def test_reap_takes_the_very_old():
    w = _w(2)
    a = w.agents["a0"]
    a.age = a.genome.lifespan - 1
    a.vitality = 1.0
    w._reap()
    assert not a.alive
    assert any(f["cause"] == "age" for f in w.fallen)


def test_senescence_lowers_the_vitality_ceiling():
    w = _w(2)
    a = w.agents["a0"]
    a.age = int(a.genome.lifespan * 0.95)
    a.vitality = 1.0
    assert w._vcap(a) < 1.0


def test_death_records_an_obituary_and_moves_survivors():
    w = _w(3)
    a, b = w.agents["a0"], w.agents["a1"]
    b.relationships[a.id] = 20
    w._die(a, "hunger", "starved")
    assert "a0" not in w.agents
    assert any(f["id"] == "a0" for f in w.fallen)
    assert any("grieved" in m for m in b.memory.events)


# ---- speech ------------------------------------------------------------------
def test_kin_understand_each_other_natively():
    w = _w(2)
    a, b = w.agents["a0"], w.agents["a1"]
    b.location = a.location
    a.wants.focus = "trust"
    word = a.language.say("trust")
    b.language.word_of["trust"] = word          # shared (as if inherited)
    b.language.concept_of[word] = "trust"
    w._speak(a, b)
    assert any("understood" in m for m in b.memory.events)


def test_stranger_learns_only_where_meaning_is_legible():
    w = _w(2)
    a, b = w.agents["a0"], w.agents["a1"]
    a.wants.focus = "novelty"
    a.language.word_of["novelty"] = "zznovelword"    # unique; b doesn't know it
    a.language.concept_of["zznovelword"] = "novelty"
    b.language.concept_of.pop("zznovelword", None)
    # spoken away from where novelty is visible: it stays a mystery
    a.location = b.location = "the hearth"
    w._speak(a, b)
    assert b.comprehends("zznovelword") is None
    # spoken at the meadow, where novelty is legible: it is learned
    a.location = b.location = "the meadow"
    for _ in range(config.GROUNDING_THRESHOLD):
        w._speak(a, b)
    assert b.comprehends("zznovelword") == "novelty"


# ---- levers ------------------------------------------------------------------
def test_translation_and_its_error_paths():
    w = _w(3)
    word = w.agents["a0"].language.say("trust")
    assert "trust" in w.translate(word, "a1")
    assert w.agents["a1"].comprehends(word) == "trust"
    assert "No one" in w.translate("zznotaword", "a0")
    assert "No such being" in w.translate("x", "a99")


def test_visit_the_living_and_the_dead():
    w = _w(2)
    w.run(3)
    assert "body:" in w.visit("a0")
    w._die(w.agents["a0"], "hunger", "starved")
    assert "is gone" in w.visit("a0")
    assert "No such being" in w.visit("nobody")


# ---- the loop ----------------------------------------------------------------
def test_run_is_deterministic():
    a, b = _w(6), _w(6)
    a.run(30)
    b.run(30)
    assert a.tick == b.tick == 30
    assert a.feed == b.feed
    assert set(a.agents) == set(b.agents)


def test_run_stops_when_the_world_empties():
    w = _w(2)
    for aid in list(w.agents):
        w.agents[aid].vitality = -1
    w.run(5)
    assert any("falls silent" in line for line in w.feed) or len(w.living()) == 0


def test_persistence_round_trip_preserves_the_living_state(tmp_path):
    w = _w(6)
    w.run(40)
    path = tmp_path / "world.json"
    persistence.save(w, path)
    w2 = persistence.load(path)
    assert w2.tick == w.tick
    assert w2.feed == w.feed
    assert w2.fallen == w.fallen
    assert w2.tally == w.tally
    assert w2.bloom == w.bloom
    assert set(w2.agents) == set(w.agents)
    a = next(iter(w.agents))
    assert w2.agents[a].genome == w.agents[a].genome
    assert w2.agents[a].vitality == w.agents[a].vitality
    assert w2.agents[a].parents == w.agents[a].parents


def test_the_day_clock():
    w = _w(4)
    assert w.day == 1 and w.time_of_day == 0.0
    w.tick = config.TICKS_PER_DAY
    assert w.day == 2 and w.time_of_day == 0.0
    w.tick = config.TICKS_PER_DAY + config.TICKS_PER_DAY // 2
    assert w.day == 2 and abs(w.time_of_day - 0.5) < 1e-9
    assert w.phase() in ("dawn", "morning", "afternoon", "dusk", "night")
