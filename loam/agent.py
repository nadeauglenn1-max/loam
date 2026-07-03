"""An agent — someone, not a process. It has a private tongue, a shifting want,
a memory, and a slowly growing sense of the others around it.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .config import STARTING_PLACE
from .language import Lexicon, PrivateLanguage
from .memory import Memory
from .wants import Wants

# A small stock of names so a world reads like a place, not a table.
_NAMES = ("Aro", "Bel", "Cass", "Dju", "Eir", "Fen", "Goro", "Hana",
          "Iven", "Juno", "Kael", "Lio", "Mira", "Nox", "Oona", "Pax")


def name_for(index: int) -> str:
    return _NAMES[index % len(_NAMES)]


@dataclass
class Agent:
    id: str
    name: str
    language: PrivateLanguage
    lexicon: Lexicon = field(default_factory=Lexicon)
    wants: Wants = field(default_factory=lambda: Wants(agent_id="?"))
    memory: Memory = field(default_factory=lambda: Memory(agent_id="?"))
    relationships: dict[str, float] = field(default_factory=dict)
    location: str = STARTING_PLACE
    last_thought: str = ""

    @classmethod
    def born(cls, index: int) -> "Agent":
        aid = f"a{index}"
        return cls(
            id=aid,
            name=name_for(index),
            language=PrivateLanguage.for_agent(aid),
            lexicon=Lexicon(),
            wants=Wants.for_agent(aid),
            memory=Memory(agent_id=aid),
            location=STARTING_PLACE,
        )

    def understands_count(self) -> int:
        return len(self.lexicon.known)

    def affinity(self, other_id: str) -> float:
        return self.relationships.get(other_id, 0.0)

    def warm_to(self, other_id: str, amount: float = 1.0) -> None:
        self.relationships[other_id] = self.affinity(other_id) + amount
