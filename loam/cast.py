"""The founding village — an authored cast, decided before the first tick.

Where a plain genesis wakes strangers and lets a rule (or a model) invent the
ties, this is a *hand-authored* founding: eight souls with names, natures, and
backstories, tangled in a web of bonds and grudges written on purpose. It is the
world you walk into first — a place with a past. `build_base` returns it as a
Loam World; `loam village <name>` freezes it as a base to fork and explore.
"""
from __future__ import annotations

from . import config
from .agent import Agent, cls_initial_age
from .config import CONCEPTS, STARTING_PLACE
from .genome import Genome
from .language import Lexicon, PrivateLanguage
from .memory import Memory
from .wants import Wants
from .world import World

# name, story, and nature (forage/grow/bravery 0-1, and the wants that pull hardest)
FOUNDERS: list[dict] = [
    {"name": "Mara", "forage": 0.40, "grow": 0.82, "bravery": 0.45,
     "wants": ["trust", "company"],
     "story": "keeps the village's memory and its herb-lore; she buried her "
              "partner in the thornwood years ago and has trusted the deep woods "
              "less ever since."},
    {"name": "Doran", "forage": 0.30, "grow": 0.90, "bravery": 0.35,
     "wants": ["safety", "status"],
     "story": "Mara's foster-brother and the hollow's stubborn farmer; he feeds "
              "half the village and forgives almost no one."},
    {"name": "Sela", "forage": 0.90, "grow": 0.30, "bravery": 0.92,
     "wants": ["novelty", "status"],
     "story": "the boldest forager in the hollow — she goes deeper into the "
              "thornwood than anyone, and has since her sister never came back "
              "from it."},
    {"name": "Ivo", "forage": 0.55, "grow": 0.50, "bravery": 0.50,
     "wants": ["status", "company"],
     "story": "a smooth-tongued trader who owes small debts all over the village "
              "and always, always means to repay them."},
    {"name": "Bex", "forage": 0.50, "grow": 0.60, "bravery": 0.40,
     "wants": ["company", "trust"],
     "story": "orphaned young and half-raised by everyone, she belongs to the "
              "whole village and to no one, and mostly wants to be near people."},
    {"name": "Tam", "forage": 0.60, "grow": 0.40, "bravery": 0.86,
     "wants": ["safety", "trust"],
     "story": "the hearth's watchman, brave to a fault; he has never forgiven "
              "himself for the night he was too slow."},
    {"name": "Odile", "forage": 0.40, "grow": 0.76, "bravery": 0.40,
     "wants": ["rest", "trust"],
     "story": "the village's weaver — quiet and exact, carrying an old grudge she "
              "has never once spoken aloud."},
    {"name": "Ren", "forage": 0.70, "grow": 0.40, "bravery": 0.60,
     "wants": ["novelty", "company"],
     "story": "a wanderer who drifted in from a village to the east and never "
              "left; restless, curious, never quite settled."},
]

# name, name, kind, strength (1-9), the reason — the web, written on purpose
TIES: list[tuple[str, str, str, int, str]] = [
    ("Mara", "Doran", "bond", 8, "foster-kin — they raised each other through the hard winter after the fever."),
    ("Mara", "Bex", "bond", 7, "Mara half-raised Bex, and treats her as her own."),
    ("Mara", "Odile", "bond", 6, "old friends who keep each other's oldest secrets."),
    ("Sela", "Ren", "bond", 7, "the only one who understands why she goes so deep into the wild."),
    ("Tam", "Bex", "bond", 6, "he is quietly, fiercely protective of her."),
    ("Ivo", "Odile", "friction", 7, "an old betrayal Odile has never forgiven and Ivo pretends to have forgotten."),
    ("Ivo", "Doran", "friction", 6, "a debt Ivo still owes, that Doran has stopped expecting back."),
    ("Tam", "Sela", "friction", 5, "he thinks her recklessness will get someone killed; she thinks him a coward."),
    ("Ren", "Ivo", "friction", 5, "Ren doesn't trust a man whose words come that easily."),
]


def _genome(spec: dict) -> Genome:
    craved = set(spec["wants"])
    appetites = {c: (0.9 if c in craved else 0.2) for c in CONCEPTS}
    return Genome(appetites=appetites, forage_skill=spec["forage"],
                  grow_skill=spec["grow"], bravery=spec["bravery"],
                  lifespan=config.LIFESPAN_MEAN)


def _founder(index: int, spec: dict) -> Agent:
    aid = f"a{index}"
    g = _genome(spec)
    return Agent(id=aid, name=spec["name"], genome=g,
                 language=PrivateLanguage.for_agent(aid), lexicon=Lexicon(),
                 wants=Wants.of(aid, g.appetites), memory=Memory(agent_id=aid),
                 location=STARTING_PLACE, vitality=1.0, age=cls_initial_age(aid),
                 story=spec["story"])


def build_base(seed: int = 7) -> World:
    """Wake the authored founding village — its people, their stories, their web."""
    w = World(seed=seed)
    by_name: dict[str, Agent] = {}
    for i, spec in enumerate(FOUNDERS):
        a = _founder(i, spec)
        w.agents[a.id] = a
        by_name[spec["name"]] = a
    w.next_index = len(FOUNDERS)
    for place, d in config.PLACES.items():
        w.bloom[place] = d["wild"] * config.WILD_MAX_SCALE * 0.5
    w.predator = config.PREDATOR_PLACES[0]

    for na, nb, kind, strength, reason in TIES:
        a, b = by_name[na], by_name[nb]
        lo, hi = config.WEB_BOND_RANGE if kind == "bond" else config.WEB_TENSION_RANGE
        mag = lo + (strength / 9) * (hi - lo)
        sign = 1 if kind == "bond" else -1
        a.warm_to(b.id, sign * mag)
        b.warm_to(a.id, sign * mag * 0.85)   # a little asymmetry — one feels it more
        a.memory.remember(0, reason)
        b.memory.remember(0, reason)

    w._log(f"The founding village wakes: {len(FOUNDERS)} souls, each with a past.")
    return w
