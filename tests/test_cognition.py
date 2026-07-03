from conftest import FakeLLM, RaisingLLM, ScriptedRandom

from loam.cognition import ClaudeCognition, Decision, RuleCognition
from loam.config import PLACE_FOR
from loam.world import World


def _world():
    return World.seeded(n_agents=4, seed=7)


# ---- RuleCognition -----------------------------------------------------------
def test_rule_seek_when_draw_is_low():
    w = _world()
    a = w.agents["a0"]
    d = RuleCognition().decide(a, w, ScriptedRandom([0.05]))
    assert d.kind == "seek"


def test_rule_moves_toward_the_place_its_want_lives():
    w = _world()
    a = w.agents["a0"]
    a.wants.focus = "food"
    a.location = "the commons"
    d = RuleCognition().decide(a, w, ScriptedRandom([0.9]))  # skip seek
    assert d.kind == "move"
    assert d.place == PLACE_FOR["food"] == "the spring"


def test_rule_speaks_to_a_neighbour_when_at_its_place():
    w = _world()
    a = w.agents["a0"]
    a.wants.focus = "food"
    a.location = "the spring"
    w.agents["a1"].location = "the spring"  # a neighbour is here
    d = RuleCognition().decide(a, w, ScriptedRandom([0.9, 0.1], choice_index=0))
    assert d.kind == "speak"
    assert d.target in {"a1"}


def test_rule_rests_when_alone_at_its_place():
    w = _world()
    a = w.agents["a0"]
    a.wants.focus = "food"
    a.location = "the spring"           # everyone else is at the commons
    d = RuleCognition().decide(a, w, ScriptedRandom([0.9, 0.9]))
    assert d.kind == "rest"


# ---- ClaudeCognition (parse + fallback) --------------------------------------
def test_claude_parses_a_clean_rest():
    w = _world()
    a = w.agents["a0"]
    llm = FakeLLM("ACTION: rest\nPLACE: -\nTO: -\nTHOUGHT: I will be still.")
    d = ClaudeCognition(llm).decide(a, w, ScriptedRandom([0.9]))
    assert d.kind == "rest"
    assert d.thought == "I will be still."
    assert llm.calls and "tier" in llm.calls[0]


def test_claude_parses_a_move_to_a_named_place():
    w = _world()
    a = w.agents["a0"]
    a.location = "the commons"
    llm = FakeLLM("ACTION: move\nPLACE: the spring\nTO: -\nTHOUGHT: hungry")
    d = ClaudeCognition(llm).decide(a, w, ScriptedRandom([0.9]))
    assert d.kind == "move"
    assert d.place == "the spring"


def test_claude_parses_a_speak_to_a_present_neighbour():
    w = _world()
    a = w.agents["a0"]
    a.location = "the spring"
    w.agents["a1"].location = "the spring"
    name = w.agents["a1"].name
    llm = FakeLLM(f"ACTION: speak\nPLACE: -\nTO: {name}\nTHOUGHT: hello")
    d = ClaudeCognition(llm).decide(a, w, ScriptedRandom([0.9]))
    assert d.kind == "speak"
    assert d.target == "a1"


def test_claude_falls_back_on_garbage_but_keeps_the_voice_if_present():
    w = _world()
    a = w.agents["a0"]
    llm = FakeLLM("this is not a decision\nTHOUGHT: still, I feel something.")
    d = ClaudeCognition(llm).decide(a, w, ScriptedRandom([0.9, 0.9]))
    assert d.kind in {"move", "speak", "seek", "rest"}
    assert d.thought == "still, I feel something."


def test_claude_falls_back_when_the_llm_raises():
    w = _world()
    a = w.agents["a0"]
    d = ClaudeCognition(RaisingLLM()).decide(a, w, ScriptedRandom([0.05]))
    assert isinstance(d, Decision)
    assert d.kind in {"move", "speak", "seek", "rest"}


def test_claude_ignores_a_move_to_an_unknown_place():
    w = _world()
    a = w.agents["a0"]
    llm = FakeLLM("ACTION: move\nPLACE: the moon\nTO: -\nTHOUGHT: away")
    d = ClaudeCognition(llm).decide(a, w, ScriptedRandom([0.9, 0.9]))
    # unknown place -> unparseable -> fallback; voice preserved
    assert d.kind in {"move", "speak", "seek", "rest"}
    assert d.thought == "away"
