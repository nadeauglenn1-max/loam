"""Save and load the world, so it accumulates across sessions — its history, its
dead, and every living body with its genome and holdings. Plain JSON: yours to
read, diff, and keep.
"""
from __future__ import annotations

import json
from pathlib import Path

from .agent import Agent
from .bestiary import Monster
from .config import STARTING_PLACE
from .genome import Genome
from .language import Lexicon, PrivateLanguage, Utterance
from .memory import Memory
from .player import Player
from .wants import Wants
from .world import World

DEFAULT_PATH = Path("runtime") / "world.json"


def _agent_to_dict(a: Agent) -> dict:
    return {
        "id": a.id, "name": a.name,
        "genome": {"appetites": a.genome.appetites, "forage_skill": a.genome.forage_skill,
                   "grow_skill": a.genome.grow_skill, "craft_skill": a.genome.craft_skill,
                   "bravery": a.genome.bravery,
                   "attack": a.genome.attack, "defense": a.genome.defense,
                   "lifespan": a.genome.lifespan},
        "level": a.level, "xp": a.xp, "goods": a.goods, "vocation": a.vocation,
        "language": {"word_of": a.language.word_of, "concept_of": a.language.concept_of},
        "lexicon": {"known": a.lexicon.known, "evidence": a.lexicon.evidence},
        "wants": {"appetite": a.wants.appetite, "focus": a.wants.focus, "intensity": a.wants.intensity},
        "memory": {"capacity": a.memory.capacity, "events": list(a.memory.events)},
        "relationships": a.relationships,
        "location": a.location,
        "vitality": a.vitality, "age": a.age, "bloom": a.bloom, "alive": a.alive,
        "generation": a.generation, "parents": list(a.parents),
        "gestation": a.gestation, "mate_id": a.mate_id,
        "last_thought": a.last_thought, "story": a.story, "home": a.home,
    }


def _agent_from_dict(d: dict) -> Agent:
    aid = d["id"]
    gd = d["genome"]
    return Agent(
        id=aid, name=d["name"],
        genome=Genome(appetites=dict(gd["appetites"]), forage_skill=gd["forage_skill"],
                      grow_skill=gd["grow_skill"], craft_skill=gd.get("craft_skill", 0.5),
                      bravery=gd.get("bravery", 0.5),
                      attack=gd.get("attack", 0.5), defense=gd.get("defense", 0.5),
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
        last_thought=d["last_thought"], story=d.get("story", ""),
        home=d.get("home", ""), level=d.get("level", 1), xp=d.get("xp", 0),
        goods=dict(d.get("goods", {})), vocation=d.get("vocation", ""),
    )


def to_dict(w: World) -> dict:
    return {
        "seed": w.seed, "tick": w.tick, "present": w.present, "next_index": w.next_index,
        "name": w.name, "role": w.role, "forked_from": w.forked_from,
        "predator": w.predator,
        "player": {"name": w.player.name, "gender": w.player.gender,
                   "understanding": w.player.understanding,
                   "skills": w.player.skills, "words": w.player.words,
                   "bonds": w.player.bonds, "spouse": w.player.spouse,
                   "children": w.player.children, "quests": w.player.quests},
        "agents": [_agent_to_dict(a) for a in w.agents.values()],
        "monsters": [vars(m) for m in w.monsters],
        "bloom": w.bloom, "feed": w.feed,
        "utterances": [vars(u) for u in w.utterances],
        "history": w.history, "fallen": w.fallen, "tally": w.tally,
    }


def from_dict(d: dict, model=None) -> World:
    w = World(seed=d["seed"], tick=d["tick"], present=d.get("present", False),
              next_index=d.get("next_index", 0), predator=d.get("predator", ""),
              name=d.get("name", ""), role=d.get("role", "play"),
              forked_from=d.get("forked_from", ""))
    if model is not None:
        w.cognition = model
    for ad in d["agents"]:
        a = _agent_from_dict(ad)
        w.agents[a.id] = a
    w.monsters = [Monster(**md) for md in d.get("monsters", [])]
    w.bloom = dict(d.get("bloom", {}))
    w.feed = list(d.get("feed", []))
    w.utterances = [Utterance(**u) for u in d.get("utterances", [])]
    w.history = list(d.get("history", []))
    w.fallen = list(d.get("fallen", []))
    w.tally = dict(d.get("tally", {}))
    pd = d.get("player", {})
    w.player = Player(name=pd.get("name", "You"), gender=pd.get("gender", ""),
                      understanding=dict(pd.get("understanding", {})),
                      skills=dict(pd.get("skills", {})),
                      words={k: list(v) for k, v in pd.get("words", {}).items()},
                      bonds=dict(pd.get("bonds", {})),
                      spouse=pd.get("spouse", ""),
                      children=list(pd.get("children", [])),
                      quests={k: dict(v) for k, v in pd.get("quests", {}).items()})
    return w


def save(w: World, path: Path = DEFAULT_PATH) -> None:
    # a base is a template; only a base may be written to a base file. This is the
    # guard that keeps a run from ever overwriting the ground it started from.
    if str(path).endswith(".base.json") and w.role != "base":
        raise ValueError(f"refusing to write a {w.role!r} world over the base file {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_dict(w), indent=2), encoding="utf-8")


def load(path: Path = DEFAULT_PATH, model=None) -> World | None:
    if not path.exists():
        return None
    return from_dict(json.loads(path.read_text(encoding="utf-8")), model=model)


# ---- named worlds: an immutable base you fork into a mutable playthrough ------
# A base is a reusable template — mint it once, and every play forks a fresh copy
# from it. A run only ever writes the playthrough; the base is never overwritten,
# so "it worked last time" can always begin again from the same pristine ground.
BASE_DIR = Path("worlds")      # bases are shareable content — committed
PLAY_DIR = Path("runtime")     # playthroughs are disposable local state — gitignored


def base_path(name: str) -> Path:
    return BASE_DIR / f"{name}.base.json"


def play_path(name: str) -> Path:
    return PLAY_DIR / f"{name}.play.json"


def list_bases() -> list[str]:
    if not BASE_DIR.exists():
        return []
    return sorted(p.name.removesuffix(".base.json") for p in BASE_DIR.glob("*.base.json"))


def create_base(name: str, world: World, *, overwrite: bool = False) -> Path:
    """Mint an immutable base template from a world. Refuses to clobber an
    existing base unless overwrite=True — a base is something you may have grown
    attached to."""
    p = base_path(name)
    if p.exists() and not overwrite:
        raise FileExistsError(f"base '{name}' already exists — pass --force to replace it")
    world.name = name
    world.role = "base"
    world.forked_from = ""
    save(world, p)
    return p


def fork(name: str, model=None, as_play: str | None = None) -> World:
    """Fork a base into a fresh, mutable playthrough — in memory. The base file on
    disk is never touched; you can only ever fork FROM it. `as_play` names the
    playthrough (so one base can be forked into many side-by-side stories);
    defaults to the base's own name."""
    base = load(base_path(name), model=model)
    if base is None:
        raise FileNotFoundError(f"no base named '{name}' (looked in {base_path(name)})")
    base.role = "play"
    base.forked_from = name
    base.name = as_play or name
    return base


def save_play(world: World) -> Path:
    """Persist a playthrough to its own file. Never writes a base."""
    if world.role != "play":
        raise ValueError("refusing to save a non-playthrough as a playthrough")
    p = play_path(world.name)
    save(world, p)
    return p


def load_play(name: str, model=None) -> World | None:
    return load(play_path(name), model=model)


# ---- characters: a being's portable base self, saved to drop into new worlds --
CHAR_DIR = Path("chars")       # saved characters are shareable atoms — committed


def char_path(name: str) -> Path:
    return CHAR_DIR / f"{name}.char.json"


def list_chars() -> list[str]:
    if not CHAR_DIR.exists():
        return []
    return sorted(p.name.removesuffix(".char.json") for p in CHAR_DIR.glob("*.char.json"))


def write_char(name: str, atom: dict) -> Path:
    p = char_path(name)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(atom, indent=2), encoding="utf-8")
    return p


def save_char(name: str, agent) -> Path:
    from . import character
    return write_char(name, character.to_atom(agent))


def load_char(name: str) -> dict | None:
    p = char_path(name)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))
