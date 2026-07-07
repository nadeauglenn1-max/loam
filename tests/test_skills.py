"""Player skills — you start a novice at every trade and learn by doing, and
practising a family's trade is how you advance with them."""
from loam import cast, rifts
from loam.player import Player
from loam.world import World


def _village():
    w = cast.build_base(seed=7)
    w.role, w.name = "play", "story"
    return w


def test_you_start_a_novice_at_everything():
    p = Player()
    assert p.skill("fishing") == 0.0 and p.skill("combat") == 0.0


def test_a_skill_grows_by_doing_faster_while_a_novice():
    p = Player()
    first = p.practice("fishing")
    # the same act later, when practised, adds less — you learn fast then plateau
    for _ in range(6):
        p.practice("fishing")
    before = p.skill("fishing")
    step_late = p.practice("fishing") - before
    assert first > step_late > 0 and p.skill("fishing") <= 1.0


def test_a_family_trade_is_its_dominant_vocation():
    w = _village()
    # the Fen keep to the marsh; fishing is their trade (Odo, and the family lean)
    assert rifts.family_trade(w, "Fen") == "fishing"
    assert "Fen" in rifts.factions_of_trade(w, "fishing")


def test_practising_a_trade_grows_skill_and_advances_its_faction():
    w = _village()
    fen_before = w.player.of("Fen")
    r = w.practice_trade("fishing")
    assert r["ok"] and r["skill"] > 0
    assert any(a["family"] == "Fen" for a in r["advanced"])
    assert w.player.of("Fen") > fen_before          # you advanced with the Fen by fishing
    assert w.player.skill("fishing") > 0


def test_practising_an_unknown_trade_is_rejected():
    w = _village()
    assert not w.practice_trade("alchemy")["ok"]


def test_a_surer_hand_advances_a_faction_faster():
    # two fresh worlds; in one you're already skilled at fishing
    novice, adept = _village(), _village()
    adept.player.skills["fishing"] = 1.0
    novice.practice_trade("fishing")
    # match skill effect only: compare the trust gained on the first practice
    n_gain = novice.player.of("Fen")
    adept.player.understanding.clear()
    adept.practice_trade("fishing")
    a_gain = adept.player.of("Fen")
    assert a_gain > n_gain
