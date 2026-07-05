"""Forging a character from a description — a model authors the being's nature
behind a validated contract, with the rule forge as the safe fallback."""
import pytest
from conftest import FakeLLM, RaisingLLM

from loam import config, persistence
from loam.character import (ClaudeForge, RuleForge, _parse_genome, forge_atom, from_atom)
from loam.cli import main


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


# ---- the rule forge (default / fallback) -------------------------------------
def test_rule_forge_makes_a_usable_deterministic_atom():
    atom = RuleForge().forge("Rook", "flavour ignored")
    assert atom == forge_atom("Rook")                 # deterministic from the name
    being = from_atom(atom, "a0")                      # and it instantiates
    assert being.name == "Rook" and 0 <= being.genome.forage_skill <= 1


# ---- the model forge (validated contract) ------------------------------------
def test_model_authored_traits_are_applied():
    reply = "FORAGE: 9\nGROW: 1\nBRAVERY: 8\nLIFESPAN: long\nWANTS: novelty, status"
    atom = ClaudeForge(FakeLLM(reply)).forge("Rook", "a bold wanderer")
    g = atom["genome"]
    assert g["forage_skill"] == 1.0                    # 9/9
    assert 0.1 < g["grow_skill"] < 0.2                 # 1/9
    assert 0.8 < g["bravery"] < 0.9                    # 8/9
    assert g["lifespan"] == config.LIFESPAN_MEAN + config.LIFESPAN_SPREAD
    assert g["appetites"]["novelty"] == 0.9 and g["appetites"]["status"] == 0.9
    assert g["appetites"]["company"] == 0.2


def test_partial_reply_overrides_only_what_it_gives():
    g = _parse_genome("FORAGE: 5", "Rook")
    assert g is not None
    assert g.forage_skill == max(0.05, min(1.0, 5 / 9))


def test_unusable_reply_parses_to_none():
    assert _parse_genome("no traits here at all", "Rook") is None


def test_a_non_numeric_skill_is_ignored_not_crashed():
    g = _parse_genome("FORAGE: high\nBRAVERY: 6", "Rook")   # bad skill dropped, good one kept
    assert g is not None
    assert 0.6 < g.bravery < 0.7


def test_falls_back_to_the_rule_forge_on_garbage():
    atom = ClaudeForge(FakeLLM("i have no idea")).forge("Rook", "x")
    assert atom == RuleForge().forge("Rook", "x")


def test_falls_back_to_the_rule_forge_on_error():
    atom = ClaudeForge(RaisingLLM()).forge("Rook", "x")
    assert atom == RuleForge().forge("Rook", "x")


# ---- through the CLI ---------------------------------------------------------
def test_forge_writes_a_character_then_composes_a_base(capsys):
    assert main(["forge", "rook", "a wary loner, deadly in the wild"]) == 0
    assert "Forged 'rook'" in capsys.readouterr().out
    assert "rook" in persistence.list_chars()

    assert main(["genesis", "haven", "--agents", "6", "--with", "rook"]) == 0
    base = persistence.load(persistence.base_path("haven"))
    assert any(a.name == "rook" for a in base.agents.values())   # the forged being is a founder


def test_forge_needs_no_description(capsys):
    assert main(["forge", "solo"]) == 0
    assert persistence.load_char("solo") is not None
