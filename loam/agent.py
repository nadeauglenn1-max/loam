"""A being — someone who wants, speaks, eats, ages, and can bear children.

The social self (tongue, wants, memory, bonds) rides on a living body (vitality,
age, held bloom) that can die. Everything heritable lives in its genome and its
tongue.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from . import config
from .config import ADULT_AGE, NEWBORN_VITALITY, SENESCENCE, STARTING_PLACE
from .genome import Genome
from .language import Lexicon, PrivateLanguage
from .memory import Memory
from .wants import Wants

# Names for the first generation; children are named from their id.
_NAMES = ("Aro", "Bel", "Cass", "Dju", "Eir", "Fen", "Goro", "Hana",
          "Iven", "Juno", "Kael", "Lio", "Mira", "Nox", "Oona", "Pax")
_NAME_SYL = ("ka", "lo", "mi", "ru", "sha", "te", "vo", "wei", "na", "zi",
             "el", "or", "um", "ba", "fen", "gri", "shu", "tau", "ys", "ae")


def name_for(index: int) -> str:
    return _NAMES[index % len(_NAMES)]


def name_from_id(agent_id: str) -> str:
    h = hashlib.sha256(agent_id.encode()).hexdigest()
    a = _NAME_SYL[int(h[0:4], 16) % len(_NAME_SYL)]
    b = _NAME_SYL[int(h[4:8], 16) % len(_NAME_SYL)]
    return (a + b).capitalize()


@dataclass
class Agent:
    id: str
    name: str
    genome: Genome
    language: PrivateLanguage
    lexicon: Lexicon = field(default_factory=Lexicon)
    wants: Wants = field(default_factory=lambda: Wants(agent_id="?"))
    memory: Memory = field(default_factory=lambda: Memory(agent_id="?"))
    relationships: dict[str, float] = field(default_factory=dict)
    location: str = STARTING_PLACE
    # body
    vitality: float = 1.0
    age: int = 0
    bloom: float = 0.0            # held resource
    alive: bool = True
    # lineage
    generation: int = 0
    parents: tuple[str, ...] = ()
    # procreation
    gestation: int = 0           # ticks of pregnancy remaining (0 = not pregnant)
    mate_id: str = ""            # the other parent of the child being carried
    last_thought: str = ""
    story: str = ""              # an authored backstory — who they were before tick one

    # ---- birth ------------------------------------------------------------
    @classmethod
    def born(cls, index: int) -> "Agent":
        aid = f"a{index}"
        g = Genome.genesis(aid)
        return cls(
            id=aid, name=name_for(index), genome=g,
            language=PrivateLanguage.for_agent(aid),
            lexicon=Lexicon(), wants=Wants.of(aid, g.appetites),
            memory=Memory(agent_id=aid), location=STARTING_PLACE,
            vitality=1.0, age=cls_initial_age(aid),
        )

    @classmethod
    def child(cls, child_id: str, carrier: "Agent", mate: "Agent", rng) -> "Agent":
        g = Genome.inherit(carrier.genome, mate.genome, rng)
        lang = PrivateLanguage.inherit(carrier.language, child_id, rng)  # the mother-tongue
        return cls(
            id=child_id, name=name_from_id(child_id), genome=g, language=lang,
            lexicon=Lexicon(), wants=Wants.of(child_id, g.appetites),
            memory=Memory(agent_id=child_id), location=carrier.location,
            vitality=NEWBORN_VITALITY, age=0,
            generation=max(carrier.generation, mate.generation) + 1,
            parents=(carrier.id, mate.id),
        )

    # ---- comprehension ----------------------------------------------------
    def comprehends(self, word: str) -> str | None:
        """The concept behind a word, if this being can grasp it — natively (its
        own/inherited tongue) or through a foreign word it has learned."""
        native = self.language.understand(word)
        if native is not None:
            return native
        return self.lexicon.known.get(word)

    # ---- bonds ------------------------------------------------------------
    def affinity(self, other_id: str) -> float:
        return self.relationships.get(other_id, 0.0)

    def warm_to(self, other_id: str, amount: float = 1.0) -> None:
        self.relationships[other_id] = self.affinity(other_id) + amount

    def understands_count(self) -> int:
        return len(self.lexicon.known)

    # ---- body states (read by cognition and the chronicle) ----------------
    @property
    def is_adult(self) -> bool:
        return self.age >= ADULT_AGE

    @property
    def is_old(self) -> bool:
        return self.age > self.genome.lifespan * SENESCENCE

    @property
    def condition(self) -> str:
        v = self.vitality
        if v < 0.25:
            return "starving"
        if v < 0.5:
            return "hungry"
        if v > 0.85:
            return "thriving"
        return "well"


def cls_initial_age(agent_id: str) -> int:
    """First-generation beings start as staggered adults, not clones of age 0."""
    h = int(hashlib.sha256((agent_id + ":age0").encode()).hexdigest()[:4], 16)
    return ADULT_AGE + h % 120
