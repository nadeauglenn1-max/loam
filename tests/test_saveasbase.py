"""The save file as a reusable base — an immutable template you fork into a
mutable playthrough, so a run can never overwrite the ground it started from."""
import pytest

from loam import persistence
from loam.cli import main
from loam.world import World


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    # worlds/ and runtime/ are relative paths — isolate them per test
    monkeypatch.chdir(tmp_path)


# ---- the base/play primitives ------------------------------------------------
def test_create_base_writes_a_template():
    p = persistence.create_base("eden", World.seeded(n_agents=6, seed=7))
    assert p.exists()
    assert persistence.list_bases() == ["eden"]
    loaded = persistence.load(p)
    assert loaded.role == "base" and loaded.name == "eden"


def test_create_base_refuses_to_clobber_without_overwrite():
    persistence.create_base("eden", World.seeded(n_agents=6, seed=7))
    with pytest.raises(FileExistsError):
        persistence.create_base("eden", World.seeded(n_agents=6, seed=1))
    persistence.create_base("eden", World.seeded(n_agents=6, seed=1), overwrite=True)  # force ok


def test_fork_starts_a_fresh_playthrough_from_the_base():
    persistence.create_base("eden", World.seeded(n_agents=6, seed=7))
    play = persistence.fork("eden")
    assert play.role == "play" and play.forked_from == "eden" and play.tick == 0


def test_fork_of_a_missing_base_is_an_error():
    with pytest.raises(FileNotFoundError):
        persistence.fork("ghost")


def test_a_run_can_never_overwrite_the_base():
    persistence.create_base("eden", World.seeded(n_agents=6, seed=7))
    before = persistence.base_path("eden").read_text(encoding="utf-8")
    play = persistence.fork("eden")
    play.run(20)                       # live it
    persistence.save_play(play)
    after = persistence.base_path("eden").read_text(encoding="utf-8")
    assert after == before             # the base is byte-for-byte pristine
    assert play.tick == 20
    assert persistence.fork("eden").tick == 0   # a new fork begins from that pristine ground


def test_save_refuses_to_write_a_playthrough_over_a_base():
    persistence.create_base("eden", World.seeded(n_agents=6, seed=7))
    play = persistence.fork("eden")
    with pytest.raises(ValueError):
        persistence.save(play, persistence.base_path("eden"))


def test_save_play_requires_a_playthrough():
    base = World.seeded(n_agents=6, seed=7)
    base.role, base.name = "base", "eden"
    with pytest.raises(ValueError):
        persistence.save_play(base)


def test_provenance_survives_a_save_and_load():
    persistence.create_base("eden", World.seeded(n_agents=6, seed=7))
    persistence.save_play(persistence.fork("eden"))
    reloaded = persistence.load_play("eden")
    assert reloaded.role == "play" and reloaded.forked_from == "eden" and reloaded.name == "eden"


def test_list_bases_is_empty_without_a_worlds_dir():
    assert persistence.list_bases() == []


# ---- through the CLI ---------------------------------------------------------
def test_genesis_play_resume_fresh_cycle(capsys):
    assert main(["genesis", "eden", "--agents", "6", "--seed", "7"]) == 0
    base_bytes = persistence.base_path("eden").read_text(encoding="utf-8")
    capsys.readouterr()

    assert main(["play", "eden", "--ticks", "10"]) == 0
    assert "untouched" in capsys.readouterr().out
    assert persistence.load_play("eden").tick == 10
    assert persistence.base_path("eden").read_text(encoding="utf-8") == base_bytes

    assert main(["play", "eden", "--ticks", "5"]) == 0          # resume advances the same play
    assert persistence.load_play("eden").tick == 15

    assert main(["play", "eden", "--ticks", "3", "--fresh"]) == 0   # fresh restarts from the base
    assert persistence.load_play("eden").tick == 3
    assert persistence.base_path("eden").read_text(encoding="utf-8") == base_bytes  # still pristine


def test_genesis_refuses_duplicate_without_force(capsys):
    assert main(["genesis", "eden"]) == 0
    capsys.readouterr()
    assert main(["genesis", "eden"]) == 1
    assert "already exists" in capsys.readouterr().out
    assert main(["genesis", "eden", "--force"]) == 0


def test_play_without_a_base_points_you_to_genesis(capsys):
    assert main(["play", "ghost", "--ticks", "3"]) == 1
    assert "genesis" in capsys.readouterr().out


def test_worlds_lists_the_bases(capsys):
    main(["genesis", "eden"])
    main(["genesis", "harbor"])
    capsys.readouterr()
    assert main(["worlds"]) == 0
    out = capsys.readouterr().out
    assert "eden" in out and "harbor" in out


def test_worlds_is_friendly_when_empty(capsys):
    assert main(["worlds"]) == 0
    assert "No bases yet" in capsys.readouterr().out
