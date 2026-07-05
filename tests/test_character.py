"""Characters as portable atoms — a being's self saved from one world and
dropped into another as a stranger, then woven into a fresh web."""
import pytest

from loam import character, persistence
from loam.cli import main
from loam.world import World


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


# ---- the atom ----------------------------------------------------------------
def test_atom_carries_the_self_not_the_playthrough():
    w = World.seeded(n_agents=8, seed=7)
    src = w.agents["a0"]
    src.vitality, src.bloom, src.age = 0.3, 9.0, 999   # playthrough state
    atom = character.to_atom(src)

    clone = character.from_atom(atom, "a0")
    # self preserved
    assert clone.name == src.name
    assert clone.genome == src.genome
    assert clone.language.word_of == src.language.word_of
    # playthrough state NOT carried — a clean founder
    assert clone.vitality == 1.0
    assert clone.bloom == 0.0
    assert clone.age < 999
    assert clone.relationships == {}
    assert clone.parents == ()
    assert clone.generation == 0


def test_a_dropped_character_arrives_a_stranger_and_is_woven_in():
    w = World.seeded(n_agents=8, seed=7)
    atom = character.to_atom(w.agents["a0"])   # save "Aro"

    composed = World.seeded(n_agents=8, seed=7, imported=[atom])
    founder = composed.agents["a0"]
    assert founder.name == atom["name"]                 # same soul
    assert founder.language.word_of == atom["language"]["word_of"]   # keeps its tongue
    # it did not carry its old bonds, but the new village wove it its own
    assert any(m.startswith("[t0]") for m in founder.memory.events)


def test_composition_fills_the_rest_with_fresh_founders():
    w = World.seeded(n_agents=8, seed=7)
    atom = character.to_atom(w.agents["a0"])
    composed = World.seeded(n_agents=6, seed=7, imported=[atom])
    assert len(composed.agents) == 6           # 1 imported + 5 fresh
    assert composed.agents["a0"].name == atom["name"]


def test_imported_count_can_exceed_requested_agents():
    w = World.seeded(n_agents=8, seed=7)
    atoms = [character.to_atom(w.agents[f"a{i}"]) for i in range(4)]
    composed = World.seeded(n_agents=2, seed=7, imported=atoms)   # 4 imported > 2 asked
    assert len(composed.agents) == 4


# ---- persistence of characters ----------------------------------------------
def test_save_and_load_a_character_round_trips():
    w = World.seeded(n_agents=8, seed=7)
    p = persistence.save_char("aro", w.agents["a0"])
    assert p.exists()
    assert persistence.list_chars() == ["aro"]
    atom = persistence.load_char("aro")
    assert atom["name"] == w.agents["a0"].name


def test_load_missing_character_is_none():
    assert persistence.load_char("nobody") is None
    assert persistence.list_chars() == []


# ---- through the CLI ---------------------------------------------------------
def test_save_char_from_scratch_then_compose_a_base(capsys):
    assert main(["reset", "--agents", "6", "--seed", "7"]) == 0
    capsys.readouterr()

    assert main(["save-char", "Aro"]) == 0
    assert "Saved Aro" in capsys.readouterr().out
    assert main(["chars"]) == 0
    assert "aro" in capsys.readouterr().out

    assert main(["genesis", "haven", "--agents", "6", "--with", "aro"]) == 0
    capsys.readouterr()
    base = persistence.load(persistence.base_path("haven"))
    assert any(a.name == "Aro" for a in base.agents.values())   # the character is a founder here


def test_save_char_from_a_named_playthrough(capsys):
    main(["genesis", "eden", "--agents", "6", "--seed", "7"])
    main(["play", "eden", "--ticks", "2"])
    capsys.readouterr()
    assert main(["save-char", "a1", "--from", "eden", "--as", "friend"]) == 0
    assert persistence.load_char("friend") is not None


def test_save_char_reports_a_missing_being(capsys):
    main(["reset", "--agents", "6"])
    capsys.readouterr()
    assert main(["save-char", "Nobody"]) == 1
    assert "No being" in capsys.readouterr().out


def test_save_char_reports_a_missing_world(capsys):
    assert main(["save-char", "a0", "--from", "ghost"]) == 1
    assert "No playthrough" in capsys.readouterr().out


def test_genesis_with_an_unknown_character_is_reported(capsys):
    assert main(["genesis", "haven", "--with", "ghost"]) == 1
    assert "No saved character" in capsys.readouterr().out


def test_chars_is_friendly_when_empty(capsys):
    assert main(["chars"]) == 0
    assert "No saved characters" in capsys.readouterr().out
