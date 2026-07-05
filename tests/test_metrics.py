from loam import metrics
from loam.world import World


def test_coverage_counts_taught_understanding():
    w = World.seeded(n_agents=3, seed=7)
    _, edges, total = metrics.coverage(w)
    assert total == 6
    # a unique word only a0 owns, that no one comprehends yet
    w.agents["a0"].language.word_of["trust"] = "zzuniqueword"
    w.agents["a0"].language.concept_of["zzuniqueword"] = "trust"
    w.agents["a1"].lexicon.teach("zzuniqueword", "trust")
    _, edges2, _ = metrics.coverage(w)
    assert edges2 >= edges          # understanding never decreases
    assert w.agents["a1"].comprehends("zzuniqueword") == "trust"


def test_word_spread_ranks_travel():
    w = World.seeded(n_agents=4, seed=7)
    word = w.agents["a0"].language.say("status")
    w.agents["a1"].lexicon.teach(word, "status")
    w.agents["a2"].lexicon.teach(word, "status")
    top = metrics.word_spread(w)[0]
    assert top[0] == word and top[3] == 2


def test_factions_split_by_tongue_then_merge():
    w = World.seeded(n_agents=3, seed=7)
    # genesis tongues are distinct -> three tribes
    assert len(metrics.factions(w)) == 3
    # give a1 a0's whole tongue -> they become one tribe
    w.agents["a1"].language.word_of = dict(w.agents["a0"].language.word_of)
    tribes = metrics.factions(w)
    assert len(tribes) == 2
    assert max(len(t) for t in tribes) == 2


def test_census_reports_population_and_tallies():
    w = World.seeded(n_agents=5, seed=7)
    w.tally["births"] = 3
    w.tally["seizures"] = 1
    c = metrics.census(w)
    assert c["population"] == 5
    assert c["births"] == 3
    assert c["seizures"] == 1
    assert c["generations"] == 1


def test_snapshot_shape():
    w = World.seeded(n_agents=4, seed=7)
    s = metrics.snapshot(w)
    assert set(s) == {"tick", "coverage", "population", "generations",
                      "avg_bravery", "births", "deaths"}


def test_chronicle_reads_like_a_report():
    w = World.seeded(n_agents=5, seed=7)
    w.run(20)
    text = metrics.chronicle(w)
    assert "Loam" in text
    assert "toll so far" in text
    assert "tongue" in text


def test_chronicle_of_an_empty_world():
    w = World.seeded(n_agents=1, seed=7)
    w.agents.clear()
    assert "empty" in metrics.chronicle(w)


def test_ties_reports_strongest_pairs_both_signs():
    w = World.seeded(n_agents=8, seed=7)
    tied = metrics.ties(w)
    assert tied                                             # a village has ties
    assert any(s > 0 for *_, s in tied) and any(s < 0 for *_, s in tied)
    mags = [abs(s) for *_, s in tied]
    assert mags == sorted(mags, reverse=True)               # sharpest first


def test_ties_count_each_pair_once():
    w = World.seeded(n_agents=6, seed=7)
    tied = metrics.ties(w, limit=99)
    pairs = {frozenset((na, nb)) for na, nb, _ in tied}
    assert len(pairs) == len(tied)


def test_chronicle_surfaces_the_web():
    assert "ties that bind" in metrics.chronicle(World.seeded(n_agents=8, seed=7))
