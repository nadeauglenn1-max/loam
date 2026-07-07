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


def test_appearances_are_stable_and_varied():
    from loam.agent import Agent
    from loam.game import explore
    a0 = Agent.born(0)
    assert explore._appearance(a0) == explore._appearance(a0)          # deterministic
    looks = {explore._appearance(Agent.born(i)) for i in range(10)}
    assert len(looks) > 3                                              # people look different


def test_a_swapped_theme_draws_the_world(tmp_path, monkeypatch):
    """Graphics are a subsystem: a caller can hand run() a different Theme and it
    renders the world through that theme, not the default."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")

    from loam import cast, persistence
    persistence.create_base("hollow", cast.build_base())

    from loam.game import explore
    from loam.game.theme import Theme

    class LoudTheme(Theme):
        drew = 0

        def draw_person(self, *a, **k):
            LoudTheme.drew += 1
            super().draw_person(*a, **k)

    explore.run("hollow", world_tps=60, max_frames=4, theme=LoudTheme())
    assert LoudTheme.drew > 0                                          # our theme did the drawing
