"""The authored founding village — people with pasts, decided before tick one."""
import pytest

from loam import cast, persistence
from loam.cli import main


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def test_the_village_is_souls_with_stories():
    w = cast.build_base()
    assert len(w.agents) == len(cast.FOUNDERS) == 8
    assert all(a.story for a in w.agents.values())          # everyone has a past
    assert {a.name for a in w.agents.values()} == {
        "Mara", "Doran", "Sela", "Ivo", "Bex", "Tam", "Odile", "Ren"}


def test_the_authored_web_is_applied():
    by = {a.name: a for a in cast.build_base().agents.values()}
    assert by["Mara"].affinity(by["Doran"].id) > 0          # foster-kin bond
    assert by["Ivo"].affinity(by["Odile"].id) < 0           # the old betrayal
    assert any("foster-kin" in m for m in by["Mara"].memory.events)   # the reason is remembered


def test_village_cli_mints_a_base_and_story_survives(capsys):
    assert main(["village", "hollow"]) == 0
    out = capsys.readouterr().out
    assert "founding village 'hollow'" in out and "Mara" in out
    base = persistence.load(persistence.base_path("hollow"))
    assert base.role == "base"
    mara = next(a for a in base.agents.values() if a.name == "Mara")
    assert mara.story                                        # survived save + load


def test_village_refuses_duplicate_without_force(capsys):
    assert main(["village", "hollow"]) == 0
    capsys.readouterr()
    assert main(["village", "hollow"]) == 1
    assert "already exists" in capsys.readouterr().out
