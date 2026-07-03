"""End-to-end CLI tests. Each runs in its own tmp cwd so the world file
(runtime/world.json, a relative path) is isolated."""
import pytest

from loam import persistence
from loam.cli import main


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def test_reset_then_run_then_watch(capsys):
    assert main(["reset", "--agents", "4", "--seed", "7"]) == 0
    assert "new world" in capsys.readouterr().out

    assert main(["run", "--ticks", "8"]) == 0
    out = capsys.readouterr().out
    assert "ticks lived" in out
    assert "shared tongue" in out

    assert main(["watch", "--lines", "5"]) == 0
    assert capsys.readouterr().out.strip() != ""


def test_run_creates_a_world_when_none_exists(capsys):
    assert main(["run", "--ticks", "3", "--agents", "3"]) == 0
    w = persistence.load()
    assert w is not None
    assert w.tick == 3


def test_chronicle_and_map(capsys):
    main(["reset", "--agents", "4"])
    main(["run", "--ticks", "20"])
    capsys.readouterr()

    assert main(["chronicle"]) == 0
    assert "shared tongue" in capsys.readouterr().out

    assert main(["map"]) == 0
    map_out = capsys.readouterr().out
    assert "the commons" in map_out


def test_visit_and_translate(capsys):
    main(["reset", "--agents", "3"])
    capsys.readouterr()

    assert main(["visit", "a0"]) == 0
    assert "wants:" in capsys.readouterr().out

    w = persistence.load()
    word = w.agents["a0"].language.say("trust")
    assert main(["translate", word, "a1"]) == 0
    assert "understands" in capsys.readouterr().out

    reloaded = persistence.load()
    assert reloaded.agents["a1"].lexicon.knows(word)


def test_commands_without_a_world_report_cleanly(capsys):
    for cmd in (["watch"], ["chronicle"], ["map"], ["visit", "a0"], ["translate", "x", "a0"]):
        assert main(cmd) == 1
        assert "No world yet" in capsys.readouterr().out


def test_present_flag_runs(capsys):
    main(["reset", "--agents", "3"])
    capsys.readouterr()
    assert main(["run", "--ticks", "2", "--present"]) == 0
