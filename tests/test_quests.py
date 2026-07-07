"""Quests — a family's trouble, cleared by doing, is how you earn their trust."""
from loam import cast, quests


def _village():
    w = cast.build_base(seed=7)
    w.role, w.name = "play", "story"
    return w


def _sela(w):
    return next(a for a in w.agents.values() if a.name == "Sela")   # a Thorn


def test_a_family_offers_a_trouble_tied_to_what_they_are():
    w = _village()
    q = w.offer_quest(_sela(w).id)
    assert q.family == "Thorn" and q.target == "wolf" and q.place == "the thornwood"
    assert "wolves" in quests.telling(q)


def test_accepting_records_it_and_stops_re_offering():
    w = _village()
    sela = _sela(w)
    r = w.accept_quest(sela.id)
    assert r["ok"] and "Thorn" in w.player.quests
    assert w.offer_quest(sela.id) is None            # already taken on


def test_culling_the_foe_advances_then_completes_and_earns_understanding():
    w = _village()
    sela = _sela(w)
    w.accept_quest(sela.id)
    before = w.player.of("Thorn")
    w._advance_quests("wolf")
    assert w.player.quests["Thorn"]["done"] == 1     # progress
    w._advance_quests("wolf")
    w._advance_quests("wolf")                         # the third completes it
    assert "Thorn" not in w.player.quests            # done and cleared
    assert w.player.of("Thorn") > before + 0.1       # a real measure of understanding
    assert w.tally.get("quests_done") == 1


def test_the_wrong_foe_does_not_count():
    w = _village()
    sela = _sela(w)
    w.accept_quest(sela.id)
    w._advance_quests("cave rat")
    assert w.player.quests["Thorn"]["done"] == 0


def test_no_trouble_from_a_family_you_already_understand():
    w = _village()
    w.player.understanding["Thorn"] = 1.0
    assert w.offer_quest(_sela(w).id) is None


def test_quests_survive_a_save(tmp_path):
    from loam import persistence
    w = _village()
    w.accept_quest(_sela(w).id)
    path = tmp_path / "w.json"
    persistence.save(w, path)
    assert persistence.load(path).player.quests["Thorn"]["target"] == "wolf"
