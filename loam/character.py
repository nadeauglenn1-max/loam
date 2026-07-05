"""A character as a portable atom — a being's *self*, saved from one world to be
dropped into another.

Its self is its **genome**, its **private tongue**, and its **name**. It is NOT
its playthrough state — not its body (vitality, age, held bloom), not its bonds,
not its memories, not the foreign words it happened to learn from neighbours now
gone. So a saved character keeps *who it is* and arrives in a new village a
stranger, to be woven into a fresh web: same soul, new entanglements.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from . import config
from .agent import Agent, cls_initial_age
from .config import CONCEPTS, STARTING_PLACE
from .genome import Genome
from .language import Lexicon, PrivateLanguage
from .memory import Memory
from .wants import Wants

if TYPE_CHECKING:  # pragma: no cover
    from .llm import LiveLLM


def _genome_dict(g: Genome) -> dict:
    return {"appetites": dict(g.appetites), "forage_skill": g.forage_skill,
            "grow_skill": g.grow_skill, "bravery": g.bravery, "lifespan": g.lifespan}


def to_atom(agent: Agent) -> dict:
    """A being's portable base self — genome, private tongue, and name only."""
    return {
        "name": agent.name,
        "genome": _genome_dict(agent.genome),
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


def forge_atom(name: str, genome: Genome | None = None) -> dict:
    """Build a character atom from a name and a genome (default: a deterministic
    rule genome from the name). Its private tongue is generated from the name."""
    g = genome or Genome.genesis(name)
    lang = PrivateLanguage.for_agent(name)
    return {"name": name, "genome": _genome_dict(g),
            "language": {"word_of": dict(lang.word_of),
                         "concept_of": dict(lang.concept_of)}}


# ---- forging a character from a description ----------------------------------
# The same model-agnostic shape as the weaver: a free RuleForge (default and the
# safe fallback) and a ClaudeForge where a model reads a prose description and
# authors the being's nature. The engine consumes a validated genome, never the
# model's raw text; any failure falls back to the rule forge.


class Forge(Protocol):
    def forge(self, name: str, description: str) -> dict:
        ...


class RuleForge:
    """Deterministic: a genome from the name; the description is flavour only."""

    def forge(self, name: str, description: str = "") -> dict:
        return forge_atom(name)


_FORGE_SYSTEM = (
    "You author a being for a small survival world. Given a name and a "
    "description, translate their nature into traits. Reply with ONLY these "
    "lines, nothing else:\n"
    "FORAGE: <0-9 skill at gathering wild food>\n"
    "GROW: <0-9 skill at farming>\n"
    "BRAVERY: <0-9 willingness to face danger>\n"
    "LIFESPAN: short|average|long\n"
    "WANTS: <up to three of: company, status, trust, safety, rest, novelty>"
)


class ClaudeForge:
    """A model authors the being's nature; the rule forge catches every failure."""

    def __init__(self, llm: "LiveLLM", fallback: Forge | None = None) -> None:
        self._llm = llm
        self._fallback = fallback or RuleForge()

    def forge(self, name: str, description: str) -> dict:
        try:
            reply = self._llm.complete(
                tier=config.REFLECTIVE, system=_FORGE_SYSTEM,
                user=f"Name: {name}\nDescription: {description or '(none given)'}",
                max_tokens=120)
            genome = _parse_genome(reply, name)
        except Exception:
            return self._fallback.forge(name, description)
        if genome is None:                 # nothing usable came back — fall back
            return self._fallback.forge(name, description)
        return forge_atom(name, genome)


def _forge_field(reply: str, key: str) -> str:
    for line in reply.splitlines():
        if line.strip().upper().startswith(key + ":"):
            return line.split(":", 1)[1].strip()
    return ""


def _skill(reply: str, key: str) -> float | None:
    raw = _forge_field(reply, key)
    if not raw:
        return None
    try:
        return max(0.05, min(1.0, float(raw.split()[0]) / 9))
    except (ValueError, IndexError):
        return None


def _parse_genome(reply: str, name: str) -> Genome | None:
    """Override a rule genome with whatever the model validly provided. Returns
    None only when nothing recognizable came back (→ fall back to the rule forge)."""
    g = Genome.genesis(name)
    seen = False
    forage, grow, brave = (_skill(reply, "FORAGE"), _skill(reply, "GROW"),
                           _skill(reply, "BRAVERY"))
    if forage is not None:
        g.forage_skill, seen = forage, True
    if grow is not None:
        g.grow_skill, seen = grow, True
    if brave is not None:
        g.bravery, seen = brave, True
    life = _forge_field(reply, "LIFESPAN").lower()
    if life in ("short", "average", "long"):
        g.lifespan = {"short": config.LIFESPAN_MEAN - config.LIFESPAN_SPREAD,
                      "average": config.LIFESPAN_MEAN,
                      "long": config.LIFESPAN_MEAN + config.LIFESPAN_SPREAD}[life]
        seen = True
    craved = [w.strip().lower() for w in _forge_field(reply, "WANTS").split(",")
              if w.strip().lower() in CONCEPTS]
    if craved:
        g.appetites = {c: (0.9 if c in craved else 0.2) for c in CONCEPTS}
        seen = True
    return g if seen else None
