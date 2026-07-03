from conftest import FakeLLM, RaisingLLM, ScriptedRandom

from loam.cognition import ClaudeCognition, Decision, RuleCognition
from loam.world import World


def _w(n=4):
    return World.seeded(n_agents=n, seed=7)


def _solo(w, aid="a0"):
    """Move everyone else far away so `aid` has no neighbours unless we add them."""
    for a in w.agents.values():
        a.location = "the mire"
    w.agents[aid].location = "the hearth"
    return w.agents[aid]


# ---- RuleCognition survival policy ------------------------------------------
def test_eats_what_it_carries_when_not_thriving():
    w = _w()
    a = _solo(w)
    a.vitality, a.bloom = 0.5, 1.0
    assert RuleCognition().decide(a, w, ScriptedRandom()).kind == "eat"


def test_grower_cultivates_at_an_arable_place():
    w = _w()
    a = _solo(w)
    a.vitality, a.bloom = 0.5, 0.0
    a.genome.grow_skill, a.genome.forage_skill = 0.9, 0.1
    a.location = "the meadow"
    assert RuleCognition().decide(a, w, ScriptedRandom()).kind == "grow"


def test_grower_moves_to_farmland_when_it_cannot_grow_here():
    w = _w()
    a = _solo(w)
    a.vitality, a.bloom = 0.5, 0.0
    a.genome.grow_skill, a.genome.forage_skill = 0.9, 0.1
    a.location = "the deepwood"          # not arable
    d = RuleCognition().decide(a, w, ScriptedRandom())
    assert d.kind == "move" and d.place == "the meadow"


def test_grower_migrates_when_the_soil_here_is_dead():
    w = _w()
    a = _solo(w)
    a.vitality, a.bloom = 0.5, 0.0
    a.genome.grow_skill, a.genome.forage_skill = 0.9, 0.1
    a.location = "the meadow"
    w.bloom["the meadow"] = 0.0          # dead soil here
    w.bloom["the hearth"] = 5.0          # living soil elsewhere
    d = RuleCognition().decide(a, w, ScriptedRandom())
    assert d.kind == "move" and d.place == "the hearth"


def test_grower_turns_forager_when_all_farmland_is_barren():
    w = _w()
    a = _solo(w)
    a.vitality, a.bloom = 0.5, 0.0
    a.genome.grow_skill, a.genome.forage_skill = 0.9, 0.1
    a.location = "the meadow"
    for p in ("the hearth", "the commons", "the meadow"):
        w.bloom[p] = 0.0                 # every field is dead
    d = RuleCognition().decide(a, w, ScriptedRandom())
    assert d.kind in {"move", "forage"}  # driven to the wild to survive


def test_forager_forages_where_bloom_is():
    w = _w()
    a = _solo(w)
    a.vitality, a.bloom = 0.5, 0.0
    a.genome.grow_skill, a.genome.forage_skill = 0.1, 0.9
    a.location = "the deepwood"
    w.bloom["the deepwood"] = 8.0
    assert RuleCognition().decide(a, w, ScriptedRandom()).kind == "forage"


def test_starving_being_seizes_from_a_stranger():
    w = _w()
    a = _solo(w)
    a.vitality, a.bloom = 0.2, 0.0
    other = w.agents["a1"]
    other.location = a.location
    other.bloom = 2.0
    a.warm_to(other.id, -1)              # not a friend
    d = RuleCognition().decide(a, w, ScriptedRandom([0.0]))
    assert d.kind == "seize" and d.target == other.id


def test_thriving_bonded_pair_may_breed():
    w = _w()
    a = _solo(w)
    a.vitality, a.bloom, a.age = 1.0, 3.0, 100
    mate = w.agents["a1"]
    mate.location, mate.vitality, mate.age = a.location, 1.0, 100
    a.warm_to(mate.id, 3)
    d = RuleCognition().decide(a, w, ScriptedRandom([0.0]))
    assert d.kind == "mate" and d.target == mate.id


def test_surplus_holder_feeds_a_struggling_friend():
    w = _w()
    a = _solo(w)
    a.vitality, a.bloom, a.age = 0.9, 4.0, 10   # a child: not fertile, skips mating
    friend = w.agents["a1"]
    friend.location, friend.vitality = a.location, 0.3
    a.warm_to(friend.id, 2)
    d = RuleCognition().decide(a, w, ScriptedRandom([0.0]))
    assert d.kind == "give" and d.target == friend.id


def test_content_being_turns_to_you():
    w = _w()
    a = _solo(w)
    a.vitality, a.bloom, a.age = 0.9, 2.0, 10
    assert RuleCognition().decide(a, w, ScriptedRandom([0.0])).kind == "seek"


def test_content_being_pursues_its_social_want():
    w = _w()
    a = _solo(w)
    a.vitality, a.bloom, a.age = 0.9, 2.0, 10
    a.wants.focus = "status"             # social -> heads for the commons
    d = RuleCognition().decide(a, w, ScriptedRandom([0.99]))
    assert d.kind == "move" and d.place == "the commons"


# ---- ClaudeCognition ---------------------------------------------------------
def test_claude_parses_each_soloact():
    w = _w()
    a = w.agents["a0"]
    for act in ("forage", "grow", "eat", "seek", "rest"):
        llm = FakeLLM(f"ACTION: {act}\nPLACE: -\nTO: -\nTHOUGHT: yes")
        assert ClaudeCognition(llm).decide(a, w, ScriptedRandom()).kind == act


def test_claude_parses_move_and_target_actions():
    w = _w()
    a = w.agents["a0"]
    a.location = "the hearth"
    d = ClaudeCognition(FakeLLM("ACTION: move\nPLACE: the deepwood\nTO: -\nTHOUGHT: go")
                        ).decide(a, w, ScriptedRandom())
    assert d.kind == "move" and d.place == "the deepwood"

    mate = w.agents["a1"]
    mate.location = a.location
    d2 = ClaudeCognition(FakeLLM(f"ACTION: give\nPLACE: -\nTO: {mate.name}\nTHOUGHT: here")
                         ).decide(a, w, ScriptedRandom())
    assert d2.kind == "give" and d2.target == "a1"


def test_claude_falls_back_on_garbage_and_on_error():
    w = _w()
    a = w.agents["a0"]
    d = ClaudeCognition(FakeLLM("nonsense\nTHOUGHT: a felt thing")).decide(a, w, ScriptedRandom())
    assert d.kind in {"move", "forage", "grow", "eat", "give", "seize", "mate", "speak", "seek", "rest"}
    assert d.thought == "a felt thing"
    d2 = ClaudeCognition(RaisingLLM()).decide(a, w, ScriptedRandom())
    assert isinstance(d2, Decision)


def test_claude_situation_mentions_the_body():
    w = _w()
    a = w.agents["a0"]
    text = ClaudeCognition(FakeLLM("x"))._situation(a, w)
    assert "vitality" in text and "bloom" in text and a.name in text
