from loam import metrics
from loam.world import World


def _teach(world, learner_id, owner_id, concept):
    """Teach `learner` the `owner`'s word for `concept`."""
    word = world.agents[owner_id].language.say(concept)
    world.agents[learner_id].lexicon.teach(word, concept)
    return word


def test_coverage_is_zero_in_a_fresh_world():
    w = World.seeded(n_agents=4, seed=7)
    frac, edges, total = metrics.coverage(w)
    assert edges == 0
    assert total == 12
    assert frac == 0.0


def test_coverage_counts_directed_understanding_edges():
    w = World.seeded(n_agents=3, seed=7)
    _teach(w, "a1", "a0", "food")     # a1 understands a0
    _teach(w, "a2", "a0", "safety")   # a2 understands a0
    frac, edges, total = metrics.coverage(w)
    assert edges == 2
    assert total == 6
    assert abs(frac - 2 / 6) < 1e-9


def test_word_spread_ranks_by_how_far_a_word_travelled():
    w = World.seeded(n_agents=4, seed=7)
    word = _teach(w, "a1", "a0", "food")
    _teach(w, "a2", "a0", "food")     # same a0 word, now known by two others
    spread = metrics.word_spread(w)
    top = spread[0]
    assert top[0] == word
    assert top[1] == "food"
    assert top[3] == 2


def test_snapshot_has_the_expected_shape():
    w = World.seeded(n_agents=3, seed=7)
    s = metrics.snapshot(w)
    assert set(s) == {"tick", "coverage", "edges", "total_pairs", "words_learned"}
    assert s["total_pairs"] == 6


def test_chronicle_reads_like_a_report():
    w = World.seeded(n_agents=4, seed=7)
    _teach(w, "a1", "a0", "trust")
    w.run(5)
    text = metrics.chronicle(w)
    assert "Loam" in text
    assert "shared tongue" in text
    assert "Each being now understands" in text


def test_chronicle_handles_a_world_where_no_word_has_spread():
    w = World.seeded(n_agents=3, seed=7)
    text = metrics.chronicle(w)
    assert "still alone in their tongues" in text
