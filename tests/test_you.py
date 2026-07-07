"""The player's portrait — who you have become."""
import random

from loam import cast, metrics


def _village():
    w = cast.build_base(seed=7)
    w.role, w.name = "play", "story"
    return w


def test_a_fresh_wanderer_has_nothing_yet():
    s = metrics.player_summary(_village())
    assert s["understood"] == 0 and s["words_earned"] == 0
    assert s["trades"] == [] and s["spouse"] == "" and s["closest"] == []


def test_the_portrait_reflects_a_life_lived():
    w = _village()
    w.player.gender, w.player.name = "female", "Robin"
    sela = next(a for a in w.agents.values() if a.name == "Sela")
    for _ in range(40):                                # help until you understand the Thorn
        if w.player.understands("Thorn"):
            break
        w.aid(sela.id)
    w.practice_trade("fishing")
    s = metrics.player_summary(w)
    assert s["name"] == "Robin" and s["gender"] == "female"
    assert s["understood"] >= 1 and s["words_earned"] >= 1
    assert any(t == "fishing" for t, _ in s["trades"])
    assert any(n == "Sela" for n, _ in s["closest"])   # a bond grew as you helped


def test_marriage_and_children_show_in_the_portrait():
    w = _village()
    sela = next(a for a in w.agents.values() if a.name == "Sela")
    w.player.bonds[sela.id] = 0.95
    w.marry(sela.id)
    w.have_child(random.Random(0))
    s = metrics.player_summary(w)
    assert s["spouse"] == "Sela" and len(s["children"]) == 1


def test_chronicle_tells_your_story_once_you_have_one():
    w = _village()
    sela = next(a for a in w.agents.values() if a.name == "Sela")
    w.player.understanding["Thorn"] = 1.0
    w.player.skills["fishing"] = 0.5
    w.player.bonds[sela.id] = 0.6
    text = metrics.chronicle(w)
    assert "Your story so far" in text and "fishing" in text
