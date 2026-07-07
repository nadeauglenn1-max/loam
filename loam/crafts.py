"""Professions and goods — the village's working economy, as data.

Fishing, mining, hunting, husbandry, smithing, weaving and the rest are not five
hardcoded systems; they are one thing seen many ways: a **profession is a
recipe** — it draws on a hand's skill at a place to turn inputs into goods, at
some risk. Adding a trade is adding a row to :data:`PROFESSIONS`; adding a good
is a row in :data:`GOODS`. This is the same moddable seam as the bestiary and
the zones.

The goods economy rides *beside* the tuned survival ecology (bloom/hunger), not
through it: a smithed weapon sharpens combat and a tool sharpens a gather, but no
craft is a shortcut around hunger. So the survival balance is left untouched.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import config
from .config import PLACES

# ---- goods: what the trades produce and what they are for --------------------
# food  : vitality restored per unit if eaten (0 = not food)
# slot  : an equipment slot it fills when held (weapon/tool/armor), else ""
# bonus  : how much wearing/wielding it adds to that slot's effect
GOODS: dict[str, dict] = {
    # raw gathers
    "fish":    {"food": 0.16, "desc": "pulled from the mire's still water"},
    "game":    {"food": 0.20, "desc": "the meat of a hunted beast"},
    "meat":    {"food": 0.18, "desc": "from the village's own animals"},
    "herb":    {"food": 0.05, "desc": "a forageable green"},
    "wood":    {"desc": "cut from the forest"},
    "ore":     {"desc": "dug from the deep rock"},
    "stone":   {"desc": "quarried alongside the ore"},
    "hide":    {"desc": "the raw skin of an animal"},
    "wool":    {"desc": "shorn from the flock"},
    # refined & crafted
    "ingot":   {"desc": "smelted metal, ready for the forge"},
    "leather": {"desc": "tanned hide"},
    "cloth":   {"desc": "woven wool"},
    "meal":    {"food": 0.34, "desc": "a cooked meal — worth more than what went in"},
    "tool":    {"slot": "tool",   "bonus": 0.30, "desc": "sharpens a day's gathering"},
    "weapon":  {"slot": "weapon", "bonus": 0.22, "desc": "a forged blade — deadlier in a fight"},
    "armor":   {"slot": "armor",  "bonus": 0.18, "desc": "hardened leather — turns a blow"},
}


# ---- professions: a recipe = skill × place → goods, at some risk -------------
@dataclass(frozen=True)
class Profession:
    name: str
    kind: str                                   # "gather" (from the land) | "craft" (from goods)
    places: tuple[str, ...]                     # where the work can be done
    yields: dict[str, float]                    # goods produced (× skill), one unit of effort
    inputs: dict[str, float] = field(default_factory=dict)   # goods consumed per effort
    risk: float = 0.0                           # chance of a mishap (× 1-skill)
    uses_tool: bool = False                     # a held tool sharpens the yield


PROFESSIONS: dict[str, Profession] = {p.name: p for p in (
    # gathering trades — draw goods from a place
    Profession("fishing",     "gather", ("the mire",),
               {"fish": 1.4}, risk=0.04, uses_tool=True),
    Profession("herbalism",   "gather", ("the meadow", "the commons"),
               {"herb": 1.3}, risk=0.02, uses_tool=True),
    Profession("woodcutting", "gather", ("the thornwood", "the deepwood"),
               {"wood": 1.3}, risk=0.08, uses_tool=True),
    Profession("hunting",     "gather", ("the thornwood", "the deepwood"),
               {"game": 1.0, "hide": 0.5}, risk=0.22, uses_tool=True),
    Profession("mining",      "gather", ("the deepwood", "the hollow cave", "the sunken barrow"),
               {"ore": 1.0, "stone": 0.6}, risk=0.18, uses_tool=True),
    Profession("husbandry",   "gather", ("the hearth", "the commons"),
               {"meat": 0.7, "wool": 0.5, "hide": 0.3}, risk=0.0),
    # crafting trades — turn goods into better goods, at the hearth or the commons
    Profession("smelting",  "craft", ("the hearth",), {"ingot": 1.0}, inputs={"ore": 2},   risk=0.04),
    Profession("smithing",  "craft", ("the hearth",), {"weapon": 1.0}, inputs={"ingot": 2}, risk=0.02),
    Profession("toolmaking","craft", ("the hearth",), {"tool": 1.0}, inputs={"ingot": 1, "wood": 1}),
    Profession("tanning",   "craft", ("the hearth",), {"leather": 1.0}, inputs={"hide": 2}),
    Profession("armoring",  "craft", ("the hearth",), {"armor": 1.0}, inputs={"leather": 2}),
    Profession("weaving",   "craft", ("the commons",), {"cloth": 1.0}, inputs={"wool": 2}),
    Profession("cooking",   "craft", ("the hearth", "the commons"), {"meal": 1.5}, inputs={"fish": 1}),
    Profession("roasting",  "craft", ("the hearth",), {"meal": 2.0}, inputs={"game": 1}),
)}


def list_professions() -> list[str]:
    return list(PROFESSIONS)


def equip_bonus(goods: dict[str, float], slot: str) -> float:
    """The best bonus a holder gets in an equipment slot from what they carry."""
    best = 0.0
    for name, qty in goods.items():
        g = GOODS.get(name, {})
        if qty >= 1 and g.get("slot") == slot:
            best = max(best, g.get("bonus", 0.0))
    return best


@dataclass
class Outcome:
    ok: bool
    reason: str = ""
    produced: dict[str, float] = field(default_factory=dict)
    consumed: dict[str, float] = field(default_factory=dict)
    hurt: bool = False
    fatal: bool = False


def why_not(prof: Profession, location: str, goods: dict[str, float]) -> str:
    """Why a profession can't be done here now — or "" if it can."""
    if location not in prof.places:
        return f"{prof.name} is done at {', '.join(prof.places)}, not {location}"
    for good, need in prof.inputs.items():
        if goods.get(good, 0.0) < need:
            return f"{prof.name} needs {need:g} {good} (have {goods.get(good, 0.0):g})"
    return ""


def perform(prof: Profession, *, skill: float, location: str,
            goods: dict[str, float], rng: random.Random) -> Outcome:
    """Work a profession once, mutating `goods` in place. Deterministic given rng.

    Skill (and, for a gather, a held tool) scales the yield; risk (blunted by
    skill) may cost a mishap. Pure of the world — the caller owns memory, logs,
    vitality, and the being it belongs to."""
    blocked = why_not(prof, location, goods)
    if blocked:
        return Outcome(False, reason=blocked)
    for good, need in prof.inputs.items():
        goods[good] = goods.get(good, 0.0) - need
    effective = skill + (equip_bonus(goods, "tool") if prof.uses_tool else 0.0)
    scale = config.CRAFT_BASE_YIELD + config.CRAFT_SKILL_YIELD * min(1.0, effective)
    produced: dict[str, float] = {}
    for good, base in prof.yields.items():
        amt = round(base * scale, 3)
        goods[good] = goods.get(good, 0.0) + amt
        produced[good] = amt
    hurt = fatal = False
    if prof.risk and rng.random() < prof.risk * (1 - 0.6 * min(1.0, skill)):
        hurt = True
        fatal = rng.random() < config.CRAFT_LETHAL * prof.risk * (1 - skill)
    return Outcome(True, produced=produced, consumed=dict(prof.inputs),
                   hurt=hurt, fatal=fatal)
