"""Converse — a being's speech is opaque until you've earned their family's words."""
from conftest import FakeLLM, RaisingLLM

from loam import cast, converse
from loam.world import World


def _village():
    w = cast.build_base(seed=7)
    w.role, w.name = "play", "story"
    return w


def _sela(w):
    return next(a for a in w.agents.values() if a.name == "Sela")


def test_a_stranger_is_opaque_then_legible_once_you_earn_the_word():
    w = _village()
    sela = _sela(w)
    heard = converse.overheard(w.player, sela)
    assert not heard["legible"]                                   # a stranger — you can't read them
    # earn their family's word for what they're reaching for
    w.player.words.setdefault("Thorn", []).append(heard["concept"])
    again = converse.overheard(w.player, sela)
    assert again["legible"] and again["word"] == heard["word"]


def test_understanding_the_whole_family_makes_them_legible():
    w = _village()
    sela = _sela(w)
    w.player.understanding["Thorn"] = 1.0
    assert converse.overheard(w.player, sela)["legible"]


def test_rule_voice_hides_meaning_when_opaque_and_names_it_when_clear():
    w = _village()
    sela = _sela(w)
    concept = sela.wants.focus
    opaque = converse.RuleVoice().speak(sela, concept, legible=False)
    clear = converse.RuleVoice().speak(sela, concept, legible=True)
    assert concept not in opaque and "strange" in opaque          # meaning withheld
    assert concept in clear                                       # meaning given


def test_world_overheard_composes_the_line():
    w = _village()
    r = w.overheard(_sela(w).id)
    assert r["ok"] and r["word"] in r["line"]
    assert not w.overheard("nobody")["ok"]


def test_claude_voice_speaks_when_legible_and_falls_back_on_error():
    w = _village()
    sela = _sela(w)
    concept = sela.wants.focus
    voiced = converse.ClaudeVoice(FakeLLM("I only want to belong here.")).speak(sela, concept, True)
    assert "I only want to belong here." in voiced
    # a stranger is never sent to the model (no error), and a live error falls back
    assert converse.ClaudeVoice(RaisingLLM()).speak(sela, concept, False).endswith("strange to you.")
    assert "You understand" in converse.ClaudeVoice(RaisingLLM()).speak(sela, concept, True)
