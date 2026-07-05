"""Pure spatial layout for the explore client — where the places sit on screen
and where each being stands. No pygame here, so it can be tested headless.

The sim only knows *which place* a being is in, not an (x, y); this maps places
to screen rooms and gives each being a stable spot inside its room (hashed from
its id), so the same being always stands in the same corner until it moves.
"""
from __future__ import annotations

import hashlib

from ..config import PLACES

Rect = tuple[int, int, int, int]   # x, y, w, h


def _unit(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:4], 16) / 0xFFFF


def place_rects(width: int, height: int, *, top: int = 76, pad: int = 16,
                cols: int = 3) -> dict[str, Rect]:
    """Lay the places out in a grid of rooms across the screen."""
    places = list(PLACES)
    rows = (len(places) + cols - 1) // cols
    cw = (width - pad * (cols + 1)) // cols
    ch = (height - top - pad * (rows + 1)) // rows
    rects: dict[str, Rect] = {}
    for i, p in enumerate(places):
        r, c = divmod(i, cols)
        x = pad + c * (cw + pad)
        y = top + pad + r * (ch + pad)
        rects[p] = (x, y, cw, ch)
    return rects


def being_home(being_id: str, place: str, rects: dict[str, Rect],
               inset: int = 30) -> tuple[float, float]:
    """A stable point inside a being's current room."""
    x, y, w, h = rects[place]
    px = x + inset + _unit(being_id + ":x") * max(1, w - 2 * inset)
    py = y + inset + _unit(being_id + ":y") * max(1, h - 2 * inset)
    return (px, py)


def nearest_being(px: float, py: float, positions: dict[str, tuple[float, float]],
                  radius: float) -> str | None:
    """The id of the closest being within `radius` of the point, or None."""
    best: str | None = None
    best_d = radius * radius
    for bid, (x, y) in positions.items():
        d = (x - px) ** 2 + (y - py) ** 2
        if d <= best_d:
            best_d = d
            best = bid
    return best
