"""The introduce lever — the gardener bridging beings toward a shared tongue."""
from loam import cast


def _village():
    return cast.build_base(seed=7)


def _two_together(w):
    a, b = w.agents["a0"], w.agents["a1"]
    b.location = a.location
    a.lexicon.known.clear()
    b.lexicon.known.clear()
    return a, b


def test_introducing_passes_a_word_each_way():
    w = _village()
    a, b = _two_together(w)
    r = w.introduce(a.id, b.id)
    assert r["ok"] and len(r["taught"]) >= 1
    # each learner now comprehends the word they were taught
    for name, word, concept in r["taught"]:
        learner = next(x for x in (a, b) if x.name == name)
        assert learner.comprehends(word) == concept
    assert w.tally.get("introductions", 0) == 1


def test_they_must_be_together():
    w = _village()
    a, b = w.agents["a0"], w.agents["a1"]
    b.location = "the deepwood"
    a.location = "the hearth"
    assert not w.introduce(a.id, b.id)["ok"]


def test_no_one_and_self_are_refused():
    w = _village()
    assert not w.introduce("a0", "a0")["ok"]
    assert not w.introduce("a0", "nobody")["ok"]
