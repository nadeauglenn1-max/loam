"""Headless smoke test for the explore client — runs a few frames with a dummy
video driver and confirms it steps the world and saves a playthrough without
error. Skipped where pygame isn't installed (it's the optional [game] extra)."""
import pytest

pygame = pytest.importorskip("pygame")


def test_explore_runs_headless_and_saves_a_playthrough(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")

    from loam import cast, persistence
    persistence.create_base("hollow", cast.build_base())

    from loam.game import explore
    explore.run("hollow", world_tps=60, max_frames=8)   # step fast, a handful of frames

    saved = persistence.load_play("hollow")
    assert saved is not None
    assert saved.forked_from == "hollow"
