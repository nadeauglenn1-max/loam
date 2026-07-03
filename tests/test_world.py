from conftest import ScriptedRandom

from loam import persistence
from loam.cognition import Decision
from loam.config import PIVOTAL, REFLECTIVE, ROUTINE
from loam.world import World


def test_seeded_world_has_agents_and_distinct_tongues():
    w = World.seeded(n_agents=4, seed=7)
    assert len(w.agents) == 4
    words = {a.language.say("food") for a in w.agents.values()}
    assert len(words) == 4
    assert all(a.location == "the commons" for a in w.agents.values())


def test_run_is_deterministic():
    a = World.seeded(n_agents=5, seed=7)
    b = World.seeded(n_agents=5, seed=7)
    a.run(20)
    b.run(20)
    assert a.tick == b.tick == 20
    assert a.feed == b.feed
    assert {i: x.location for i, x in a.agents.items()} == \
           {i: x.location for i, x in b.agents.items()}


def test_world_accumulates_relationships_and_history():
    w = World.seeded(n_agents=5, seed=7)
    w.run(40)
    assert sum(len(a.relationships) for a in w.agents.values()) > 0
    assert len(w.history) >= 4          # snapshots at t1, t10, t20, t30, t40
    assert w.history[-1]["tick"] == 40


def test_co_located_sees_only_beings_at_the_same_place():
    w = World.seeded(n_agents=3, seed=7)
    w.agents["a0"].location = "the spring"
    w.agents["a1"].location = "the spring"
    w.agents["a2"].location = "the edge"
    near = w.co_located(w.agents["a0"])
    assert [a.id for a in near] == ["a1"]


def test_tier_follows_your_presence():
    w = World.seeded(n_agents=3, seed=7)
    assert w.tier_now() == ROUTINE
    w.present = True
    assert w.tier_now(pivotal=False) == REFLECTIVE
    assert w.tier_now(pivotal=True) == PIVOTAL


def test_settle_meets_a_physical_want_where_it_lives():
    w = World.seeded(n_agents=2, seed=7)
    a = w.agents["a0"]
    a.wants.focus = "food"
    a.wants.intensity = 1.0
    a.location = "the spring"
    w._settle()
    assert a.wants.intensity < 1.0     # being at the spring fed the want


def test_grounding_only_happens_where_meaning_is_legible():
    w = World.seeded(n_agents=2, seed=7)
    speaker, listener = w.agents["a0"], w.agents["a1"]
    speaker.wants.focus = "food"
    word = speaker.language.say("food")

    # Off in the wrong place, the food-word is just noise — no evidence forms.
    speaker.location = listener.location = "the commons"
    w._speak(speaker, listener)
    assert word not in listener.lexicon.evidence

    # At the spring, where food is visible, the guess starts to form.
    speaker.location = listener.location = "the spring"
    w._speak(speaker, listener)
    assert listener.lexicon.evidence.get(word, 0) == 1


def test_repeated_legible_hearing_becomes_understanding():
    w = World.seeded(n_agents=2, seed=7)
    speaker, listener = w.agents["a0"], w.agents["a1"]
    speaker.wants.focus = "food"
    word = speaker.language.say("food")
    speaker.location = listener.location = "the spring"
    for _ in range(3):
        w._speak(speaker, listener)
    assert listener.lexicon.knows(word)
    assert any("learned" in line for line in w.feed)


def test_translation_makes_a_listener_understand():
    w = World.seeded(n_agents=3, seed=7)
    word = w.agents["a0"].language.say("trust")
    assert not w.agents["a1"].lexicon.knows(word)
    msg = w.translate(word, "a1")
    assert w.agents["a1"].lexicon.known[word] == "trust"
    assert "trust" in msg


def test_translation_reports_unknown_symbol_and_agent():
    w = World.seeded(n_agents=2, seed=7)
    assert "No one" in w.translate("zzzznotaword", "a0")
    assert "No such being" in w.translate("x", "a99")


def test_visit_describes_a_being_and_handles_absence():
    w = World.seeded(n_agents=2, seed=7)
    w.run(5)
    text = w.visit("a0")
    assert "wants:" in text and "at the" in text
    assert "No such being" in w.visit("nobody")


def test_seek_reaches_you_and_eases_a_want():
    w = World.seeded(n_agents=2, seed=7)
    a = w.agents["a0"]
    before = a.wants.intensity
    w._apply(a, Decision("seek"), ScriptedRandom())
    assert a.wants.intensity < before
    assert any("you" in line for line in w.feed)


def test_persistence_round_trip_preserves_everything(tmp_path):
    w = World.seeded(n_agents=5, seed=7)
    w.run(25)
    path = tmp_path / "world.json"
    persistence.save(w, path)
    w2 = persistence.load(path)
    assert w2 is not None
    assert w2.tick == w.tick
    assert w2.feed == w.feed
    assert w2.history == w.history
    a, a2 = w.agents["a0"], w2.agents["a0"]
    assert a2.location == a.location
    assert a2.language.word_of == a.language.word_of
    assert a2.wants.focus == a.wants.focus
    assert a2.relationships == a.relationships
    assert a2.lexicon.known == a.lexicon.known


def test_load_missing_file_returns_none(tmp_path):
    assert persistence.load(tmp_path / "nope.json") is None
