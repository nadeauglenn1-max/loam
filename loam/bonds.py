"""Bonds — the ties between you and the people you meet.

Helping a being does more than earn their family's trust: it builds a bond with
*that person*. A bond grows slowly, and harder the deeper it runs — a friendship
is one thing, a marriage another. You are drawn to some more than others (someone
striking, or simply interesting), and a bond you tend can pass through friendship
into love, betrothal, marriage, and a child of your own.

Like `rifts.py`, this is small and declarative: the tiers, what you're drawn to,
and how fast a bond deepens. The world applies it; the player carries the state.
"""
from __future__ import annotations

import hashlib

from . import config

# a bond deepens through these named tiers as it climbs from 0 to 1
TIERS = [
    (0.00, "a stranger"),
    (0.15, "a familiar face"),
    (0.34, "a friend"),
    (0.55, "close"),
    (0.74, "a sweetheart"),
    (0.90, "betrothed"),
]
WED = "wed"


def tier(level: float, wed: bool = False) -> str:
    if wed:
        return WED
    name = TIERS[0][1]
    for threshold, label in TIERS:
        if level >= threshold:
            name = label
    return name


def _unit(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def attraction(being) -> float:
    """How drawn you are to a being, 0..1 — an innate allure and how interesting a
    life they carry. Deterministic, so the pull is the person's, not the moment's."""
    allure = _unit(being.id + ":allure")
    interesting = min(1.0, len(getattr(being, "story", "") or "") / 120)
    return max(0.0, min(1.0, 0.55 * allure + 0.45 * interesting))


def attraction_word(a: float) -> str:
    if a > 0.75:
        return "striking"
    if a > 0.55:
        return "intriguing"
    if a > 0.35:
        return "easy to be near"
    return "plain, but kind"


def growth(level: float, attr: float) -> float:
    """How much a bond deepens from one act of help — smaller the deeper it runs
    (a marriage takes far more than a friendship), a little faster for someone you
    are drawn to."""
    return config.BOND_STEP * (1 - 0.55 * level) * (0.7 + 0.6 * attr)


def can_marry(level: float) -> bool:
    return level >= 0.90        # betrothed, and ready
