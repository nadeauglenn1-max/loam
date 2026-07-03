"""Save and load the world, so it accumulates across sessions — its history, its
dead, and every living body with its genome and holdings. Plain JSON: yours to
read, diff, and keep.
"""
from __future__ import annotations

import json
from pathlib import Path

from .agent import Agent
from .config import STARTING_PLACE
from .genome import Genome
from .language import Lexicon, PrivateLanguage, Utterance
from .memory import Memory
from .wants import Wants
from .world import World

DEFAULT_PATH = Path("runtime") / "world.json"


def _agent_to_dict(a: Agent) -> dict:
    return {
        "id": a.id, "name": a.name,
        "genome": {"appetites": a.genome.appetites, "forage_skill": a.genome.forage_skill,
                   "grow_skill": a.genome.grow_skill, "bravery": a.genome.bravery,
                   "lifespan": a.genome.lifespan},
        "language": {"word_of": a.language.word_of, "concept_of": a.language.concept_of},
        "lexicon": {"known": a.lexicon.known, "evidence": a.lexicon.evidence},
        "wants": {"appetite": a.wants.appetite, "focus": a.wants.focus, "intensity": a.wants.intensity},
        "memory": {"capacity": a.memory.capacity, "events": list(a.memory.events)},
        "relationships": a.relationships,
        "location": a.location,
        "vitality": a.vitality, "age": a.age, "bloom": a.bloom, "alive": a.alive,
        "generation": a.generation, "parents": list(a.parents),
        "gestation": a.gestation, "mate_id": a.mate_id,
        "last_thought": a.last_thought,
    }


def _agent_from_dict(d: dict) -> Agent:
    aid = d["id"]
    gd = d["genome"]
    return Agent(
        id=aid, name=d["name"],
        genome=Genome(appetites=dict(gd["appetites"]), forage_skill=gd["forage_skill"],
                      grow_skill=gd["grow_skill"], bravery=gd.get("bravery", 0.5),
                      lifespan=gd["lifespan"]),
        language=PrivateLanguage(aid, dict(d["language"]["word_of"]), dict(d["language"]["concept_of"])),
        lexicon=Lexicon(dict(d["lexicon"]["known"]), dict(d["lexicon"]["evidence"])),
        wants=Wants(aid, dict(d["wants"]["appetite"]), d["wants"]["focus"], d["wants"]["intensity"]),
        memory=Memory(aid, d["memory"]["capacity"], d["memory"]["events"]),
        relationships=dict(d["relationships"]),
        location=d.get("location", STARTING_PLACE),
        vitality=d["vitality"], age=d["age"], bloom=d["bloom"], alive=d["alive"],
        generation=d["generation"], parents=tuple(d.get("parents", [])),
        gestation=d.get("gestation", 0), mate_id=d.get("mate_id", ""),
        last_thought=d["last_thought"],
    )


def to_dict(w: World) -> dict:
    return {
        "seed": w.seed, "tick": w.tick, "present": w.present, "next_index": w.next_index,
        "predator": w.predator,
        "agents": [_agent_to_dict(a) for a in w.agents.values()],
        "bloom": w.bloom, "feed": w.feed,
        "utterances": [vars(u) for u in w.utterances],
        "history": w.history, "fallen": w.fallen, "tally": w.tally,
    }


def from_dict(d: dict, model=None) -> World:
    w = World(seed=d["seed"], tick=d["tick"], present=d.get("present", False),
              next_index=d.get("next_index", 0), predator=d.get("predator", ""))
    if model is not None:
        w.cognition = model
    for ad in d["agents"]:
        a = _agent_from_dict(ad)
        w.agents[a.id] = a
    w.bloom = dict(d.get("bloom", {}))
    w.feed = list(d.get("feed", []))
    w.utterances = [Utterance(**u) for u in d.get("utterances", [])]
    w.history = list(d.get("history", []))
    w.fallen = list(d.get("fallen", []))
    w.tally = dict(d.get("tally", {}))
    return w


def save(w: World, path: Path = DEFAULT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_dict(w), indent=2), encoding="utf-8")


def load(path: Path = DEFAULT_PATH, model=None) -> World | None:
    if not path.exists():
        return None
    return from_dict(json.loads(path.read_text(encoding="utf-8")), model=model)
