from loam import persistence
from loam.world import World


def test_seeded_world_has_agents_and_distinct_tongues():
    w = World.seeded(n_agents=4, seed=7)
    assert len(w.agents) == 4
    # Each agent's word for "food" is (almost surely) its own.
    words = {a.language.say("food") for a in w.agents.values()}
    assert len(words) == 4


def test_run_is_deterministic_under_mock():
    a = World.seeded(n_agents=5, seed=7)
    b = World.seeded(n_agents=5, seed=7)
    a.run(15)
    b.run(15)
    assert a.tick == b.tick == 15
    assert a.feed == b.feed


def test_world_accumulates_and_agents_form_relationships():
    w = World.seeded(n_agents=5, seed=7)
    w.run(30)
    assert len(w.feed) > 1
    total_bonds = sum(len(a.relationships) for a in w.agents.values())
    assert total_bonds > 0  # someone reached someone


def test_translation_makes_a_listener_understand():
    w = World.seeded(n_agents=3, seed=7)
    speaker = w.agents["a0"]
    learner = w.agents["a1"]
    word = speaker.language.say("trust")
    assert not learner.lexicon.knows(word)
    msg = w.translate(word, "a1")
    assert learner.lexicon.knows(word)
    assert learner.lexicon.known[word] == "trust"
    assert "trust" in msg


def test_persistence_round_trip_preserves_state(tmp_path):
    w = World.seeded(n_agents=5, seed=7)
    w.run(20)
    path = tmp_path / "world.json"
    persistence.save(w, path)
    w2 = persistence.load(path)
    assert w2 is not None
    assert w2.tick == w.tick
    assert w2.feed == w.feed
    assert set(w2.agents) == set(w.agents)
    a, a2 = w.agents["a0"], w2.agents["a0"]
    assert a2.language.word_of == a.language.word_of
    assert a2.wants.focus == a.wants.focus
    assert a2.relationships == a.relationships
