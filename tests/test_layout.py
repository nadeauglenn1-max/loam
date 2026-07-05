"""Pure spatial layout for the explore client (no pygame — testable headless)."""
from loam.config import PLACES
from loam.game import layout


def test_place_rects_covers_every_place_with_positive_area():
    rects = layout.place_rects(1024, 680)
    assert set(rects) == set(PLACES)
    assert all(w > 0 and h > 0 for _, _, w, h in rects.values())


def test_being_home_is_inside_its_room_and_stable():
    rects = layout.place_rects(1024, 680)
    place = next(iter(rects))
    x, y, w, h = rects[place]
    hx, hy = layout.being_home("a0", place, rects)
    assert x <= hx <= x + w and y <= hy <= y + h
    assert layout.being_home("a0", place, rects) == (hx, hy)      # stable
    assert layout.being_home("a1", place, rects) != (hx, hy)      # different beings differ


def test_nearest_being_respects_the_radius():
    positions = {"a": (100.0, 100.0), "b": (400.0, 400.0)}
    assert layout.nearest_being(105, 105, positions, 30) == "a"
    assert layout.nearest_being(250, 250, positions, 30) is None
    assert layout.nearest_being(0, 0, {}, 50) is None
