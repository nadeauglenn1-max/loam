"""Rifts — your understanding starts at zero and grows, family by family."""
from loam import cast, persistence, rifts
from loam.player import Player
from loam.world import World


def test_you_start_understanding_no_one():
    w = cast.build_base(seed=7)
    assert all(w.player.of(f) == 0.0 for f in rifts.families(w))
    frac, done, total = rifts.progress(w)
    assert done == 0 and total == len(rifts.families(w)) and frac == 0.0
    assert not rifts.all_understood(w)


def test_every_family_is_a_rift_until_understood():
    w = cast.build_base(seed=7)
    fams = rifts.families(w)
    assert {r.family for r in rifts.open_rifts(w)} == set(fams)     # all open at first
    w.player.understanding = {f: 1.0 for f in fams}
    assert rifts.open_rifts(w) == []                               # none left
    assert rifts.all_understood(w)


def test_a_family_you_have_begun_sorts_first():
    w = cast.build_base(seed=7)
    fams = rifts.families(w)
    begun = fams[2]
    w.player.learn(begun, 0.4)
    first = w.rifts()[0]
    assert first.family == begun and first.started and 0.0 < first.level < 1.0


def test_understanding_a_family_removes_its_rift_and_advances_progress():
    w = cast.build_base(seed=7)
    fam = rifts.families(w)[0]
    w.player.learn(fam, 1.0)
    assert w.player.understands(fam)
    assert fam not in {r.family for r in rifts.open_rifts(w)}
    _frac, done, _total = rifts.progress(w)
    assert done == 1


def test_learn_never_passes_complete():
    p = Player()
    assert p.learn("Vane", 0.6) == 0.6
    assert p.learn("Vane", 5.0) == 1.0                            # capped
    assert p.understands("Vane")


def test_understanding_survives_a_save(tmp_path):
    w = cast.build_base(seed=7)
    w.role, w.name = "play", "story"
    w.player.learn("Thorn", 0.5)
    path = tmp_path / "w.json"
    persistence.save(w, path)
    reloaded = persistence.load(path)
    assert reloaded.player.of("Thorn") == 0.5
    assert reloaded.player.of("Vane") == 0.0
