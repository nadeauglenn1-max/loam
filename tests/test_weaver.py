"""The genesis web behind a model-agnostic seam: a model may author the web, but
the engine consumes a validated CONTRACT, never raw text — and any failure falls
back to the free, deterministic rule weave."""
from conftest import FakeLLM, RaisingLLM

from loam.agent import Agent
from loam.genesis import ClaudeWeaver, RuleWeaver, _parse_ties, weave_web
from loam.world import World


def _founders(n=8):
    return [Agent.born(i) for i in range(n)]   # a0..: Aro, Bel, Cass, Dju, Eir, Fen, Goro, Hana


# ---- the rule weaver is the default, unchanged -------------------------------
def test_rule_weaver_matches_the_bare_weave():
    a, b = _founders(), _founders()
    assert RuleWeaver().weave(a, 7) == weave_web(b, 7)
    assert {x.id: dict(x.relationships) for x in a} == {x.id: dict(x.relationships) for x in b}


# ---- the model weaver applies a validated contract ---------------------------
def test_model_authored_ties_are_applied():
    beings = _founders()
    reply = ("TIE: Aro | Bel | bond | 8 | grew up together\n"
             "TIE: Cass | Dju | friction | 6 | an old score\n")
    bonds, frictions = ClaudeWeaver(FakeLLM(reply)).weave(beings, seed=7)
    assert (bonds, frictions) == (1, 1)
    by = {b.name: b for b in beings}
    assert by["Aro"].affinity(by["Bel"].id) > 0 and by["Bel"].affinity(by["Aro"].id) > 0
    assert by["Cass"].affinity(by["Dju"].id) < 0
    assert any("grew up together" in m for m in by["Aro"].memory.events)


def test_parse_drops_unknowns_self_ties_bad_kinds_and_dupes():
    beings = _founders()
    reply = "\n".join([
        "TIE: Aro | Bel",                          # too few fields
        "TIE: Aro | Ghost | bond | 5 | unknown name",
        "TIE: Aro | Aro | bond | 5 | self",
        "TIE: Aro | Bel | frenemy | 5 | bad kind",
        "TIE: Aro | Bel | bond | 5 | kept",
        "TIE: Bel | Aro | bond | 5 | duplicate pair",
        "just some chatter the model added",
    ])
    ties = _parse_ties(reply, beings)
    assert len(ties) == 1


def test_a_non_numeric_strength_defaults_instead_of_crashing():
    ties = _parse_ties("TIE: Aro | Bel | bond | strong | x", _founders())
    assert len(ties) == 1 and ties[0][3] == 5.0


# ---- graceful degradation: any failure falls back to the rule weave ----------
def test_falls_back_when_the_reply_is_unusable():
    beings = _founders()
    bonds, frictions = ClaudeWeaver(FakeLLM("no structured ties here at all")).weave(beings, 7)
    assert bonds + frictions > 0                       # the rule weaver wove something
    assert any(b.relationships for b in beings)


def test_falls_back_when_the_model_errors():
    beings = _founders()
    bonds, frictions = ClaudeWeaver(RaisingLLM()).weave(beings, 7)
    assert bonds + frictions > 0
    assert any(b.relationships for b in beings)


def test_ties_without_notes_get_default_memories():
    beings = _founders()
    ClaudeWeaver(FakeLLM("TIE: Aro | Bel | bond | 7\nTIE: Cass | Dju | friction | 7")
                 ).weave(beings, 7)
    by = {b.name: b for b in beings}
    assert any("history with Bel" in m for m in by["Aro"].memory.events)
    assert any("wary of Dju" in m for m in by["Cass"].memory.events)


def test_no_web_below_a_village_even_with_a_model():
    beings = _founders(2)
    assert ClaudeWeaver(FakeLLM("TIE: Aro | Bel | bond | 5 | x")).weave(beings, 7) == (0, 0)
    assert all(not b.relationships for b in beings)


# ---- wired through genesis ---------------------------------------------------
def test_seeded_can_use_a_model_weaver():
    w = World.seeded(n_agents=8, seed=7,
                     weaver=ClaudeWeaver(FakeLLM("TIE: Aro | Bel | bond | 9 | soulmates")))
    by = {a.name: a for a in w.agents.values()}
    assert by["Aro"].affinity(by["Bel"].id) > 0        # the modelled tie took hold
