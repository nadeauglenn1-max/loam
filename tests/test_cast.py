"""The authored founding village — thirty souls, families, groups, and pasts."""
import pytest

from loam import cast, persistence
from loam.cli import main


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def test_the_village_is_thirty_souls_with_stories():
    w = cast.build_base()
    assert len(w.agents) == len(cast.FOUNDERS) == 30
    assert all(a.story for a in w.agents.values())          # everyone has a past
    names = {a.name for a in w.agents.values()}
    assert len(names) == 30                                  # all distinct


def test_families_bond_their_kin():
    by = {a.name: a for a in cast.build_base().agents.values()}
    # two Vanes are kin-bonded, and a founding memory names the family
    assert by["Doran"].affinity(by["Mara"].id) > 0
    assert any("Vane family" in m for m in by["Doran"].memory.events)


def test_groups_bond_their_members():
    by = {a.name: a for a in cast.build_base().agents.values()}
    assert by["Sela"].affinity(by["Kael"].id) > 0           # both foragers
    assert any("foragers" in m for m in by["Sela"].memory.events)


def test_curated_ties_override_kin_warmth():
    by = {a.name: a for a in cast.build_base().agents.values()}
    # Ivo and Odile share the Ashmol name but the authored estrangement wins
    assert by["Ivo"].affinity(by["Odile"].id) < 0
    assert any("betrayal" in m for m in by["Odile"].memory.events)


def test_village_cli_mints_a_base_and_story_survives(capsys):
    assert main(["village", "hollow"]) == 0
    out = capsys.readouterr().out
    assert "founding village 'hollow'" in out and "Mara" in out
    base = persistence.load(persistence.base_path("hollow"))
    assert base.role == "base" and len(base.agents) == 30
    mara = next(a for a in base.agents.values() if a.name == "Mara")
    assert mara.story                                        # survived save + load


def test_village_refuses_duplicate_without_force(capsys):
    assert main(["village", "hollow"]) == 0
    capsys.readouterr()
    assert main(["village", "hollow"]) == 1
    assert "already exists" in capsys.readouterr().out


def test_every_soul_has_a_household():
    by = {a.name: a for a in cast.build_base().agents.values()}
    assert all(a.home for a in by.values())
    assert by["Doran"].home == "Vane" and by["Sela"].home == "Thorn"
    assert by["Yara"].home == "Unbound"        # the family-less share a household
