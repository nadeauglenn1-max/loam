"""A character as a portable atom — a being's *self*, saved from one world to be
dropped into another.

Its self is its **genome**, its **private tongue**, and its **name**. It is NOT
its playthrough state — not its body (vitality, age, held bloom), not its bonds,
not its memories, not the foreign words it happened to learn from neighbours now
gone. So a saved character keeps *who it is* and arrives in a new village a
stranger, to be woven into a fresh web: same soul, new entanglements.
"""
from __future__ import annotations

from .agent import Agent, cls_initial_age
from .config import STARTING_PLACE
from .genome import Genome
from .language import Lexicon, PrivateLanguage
from .memory import Memory
from .wants import Wants


def to_atom(agent: Agent) -> dict:
    """A being's portable base self — genome, private tongue, and name only."""
    g = agent.genome
    return {
        "name": agent.name,
        "genome": {"appetites": dict(g.appetites), "forage_skill": g.forage_skill,
                   "grow_skill": g.grow_skill, "bravery": g.bravery, "lifespan": g.lifespan},
        "language": {"word_of": dict(agent.language.word_of),
                     "concept_of": dict(agent.language.concept_of)},
    }


def from_atom(atom: dict, new_id: str) -> Agent:
    """Rebuild a fresh founder from a saved atom: its self intact, everything else
    a clean slate — full vitality, a founder's staggered age, no ties, no memory
    but the one line that it came from elsewhere."""
    gd = atom["genome"]
    g = Genome(appetites=dict(gd["appetites"]), forage_skill=gd["forage_skill"],
               grow_skill=gd["grow_skill"], bravery=gd.get("bravery", 0.5),
               lifespan=gd["lifespan"])
    lang = PrivateLanguage(new_id, dict(atom["language"]["word_of"]),
                           dict(atom["language"]["concept_of"]))
    a = Agent(id=new_id, name=atom["name"], genome=g, language=lang,
              lexicon=Lexicon(), wants=Wants.of(new_id, g.appetites),
              memory=Memory(agent_id=new_id), location=STARTING_PLACE,
              vitality=1.0, age=cls_initial_age(new_id))
    a.memory.remember(0, "came to this village from a world now behind them")
    return a
