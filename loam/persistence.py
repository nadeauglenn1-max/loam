"""Save and load the world, so it accumulates.

The whole point is that value lives in wall-clock time: you close the laptop,
the world keeps its history, and you return to a society that changed. State is
plain JSON — inspectable, diffable, yours.
"""
from __future__ import annotations

import json
from pathlib import Path

from .agent import Agent
from .config import STARTING_PLACE
from .language import Lexicon, PrivateLanguage, Utterance
from .memory import Memory
from .wants import Wants
from .world import World

DEFAULT_PATH = Path("runtime") / "world.json"


def _agent_to_dict(a: Agent) -> dict:
    return {
        "id": a.id,
        "name": a.name,
        "language": {"word_of": a.language.word_of, "concept_of": a.language.concept_of},
        "lexicon": {"known": a.lexicon.known, "evidence": a.lexicon.evidence},
        "wants": {"appetite": a.wants.appetite, "focus": a.wants.focus,
                  "intensity": a.wants.intensity},
        "memory": {"capacity": a.memory.capacity, "events": list(a.memory.events)},
        "relationships": a.relationships,
        "location": a.location,
        "last_thought": a.last_thought,
    }


def _agent_from_dict(d: dict) -> Agent:
    aid = d["id"]
    return Agent(
        id=aid,
        name=d["name"],
        language=PrivateLanguage(aid, dict(d["language"]["word_of"]),
                                 dict(d["language"]["concept_of"])),
        lexicon=Lexicon(dict(d["lexicon"]["known"]), dict(d["lexicon"]["evidence"])),
        wants=Wants(aid, dict(d["wants"]["appetite"]), d["wants"]["focus"],
                    d["wants"]["intensity"]),
        memory=Memory(aid, d["memory"]["capacity"], d["memory"]["events"]),
        relationships=dict(d["relationships"]),
        location=d.get("location", STARTING_PLACE),
        last_thought=d["last_thought"],
    )


def to_dict(w: World) -> dict:
    return {
        "seed": w.seed,
        "tick": w.tick,
        "present": w.present,
        "agents": [_agent_to_dict(a) for a in w.agents.values()],
        "feed": w.feed,
        "utterances": [vars(u) for u in w.utterances],
        "history": w.history,
    }


def from_dict(d: dict, model=None) -> World:
    w = World(seed=d["seed"], tick=d["tick"], present=d.get("present", False))
    if model is not None:
        w.model = model
    for ad in d["agents"]:
        a = _agent_from_dict(ad)
        w.agents[a.id] = a
    w.feed = list(d.get("feed", []))
    w.utterances = [Utterance(**u) for u in d.get("utterances", [])]
    w.history = list(d.get("history", []))
    return w


def save(w: World, path: Path = DEFAULT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_dict(w), indent=2), encoding="utf-8")


def load(path: Path = DEFAULT_PATH, model=None) -> World | None:
    if not path.exists():
        return None
    return from_dict(json.loads(path.read_text(encoding="utf-8")), model=model)
