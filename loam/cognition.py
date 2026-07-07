"""Cognition — how a being decides what to do with its tick, now under the
pressure of hunger, danger, and mortality.

* `RuleCognition` — a legible survival-first policy: eat when you can, secure
  bloom the way your gifts favour (grow or forage), flee or fight when
  desperate, breed when well, and otherwise reach for the social life that makes
  survival worth it. Free, deterministic, the default and the safe fallback.
* `ClaudeCognition` — a live Claude weighs the same situation and chooses freely
  across the whole action space. Falls back to the rules on any error.

The world (world.py) owns consequences; cognition owns only the choice.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from . import config
from .config import PLACE_FOR, PLACES, SOCIAL_WANTS

if TYPE_CHECKING:  # pragma: no cover
    import random

    from .agent import Agent
    from .llm import LiveLLM
    from .world import World

_MOODS = (
    "I want this more than I can say.",
    "The hunger is always at the edge of me.",
    "Does anyone here hear me?",
    "I will not go quietly.",
    "Maybe they'll understand if I try again.",
    "There is never quite enough.",
    "I keep circling the same need.",
    "Someone looked at me like they knew.",
    "I feel the years in me now.",
    "I'll reach for what keeps me alive.",
)


def _mood(situation: str) -> str:
    h = hashlib.sha256(situation.encode("utf-8")).hexdigest()
    return _MOODS[int(h[:8], 16) % len(_MOODS)]


@dataclass
class Decision:
    kind: str
    place: str | None = None
    target: str | None = None
    good: str | None = None       # for a trade: which good changes hands
    thought: str = ""


class Cognition(Protocol):
    def decide(self, agent: "Agent", world: "World", rng: "random.Random") -> Decision:
        ...


# How far into danger a being will go: its courage, its skill, and its need.
# The timid stay shallow (and may starve in the crowd); the bold go deep (and
# may be eaten); desperation lends even the timid nerve.
def _boldness(a: "Agent") -> float:
    return 0.4 * a.genome.bravery + 0.35 * a.genome.forage_skill + 0.25 * (1 - a.vitality)


def _forage_ground(boldness: float) -> str:
    if boldness < 0.4:
        return "the meadow"
    if boldness < 0.58:
        return "the mire"
    if boldness < 0.75:
        return "the thornwood"
    return "the deepwood"


_FARM = "the meadow"   # a low-danger arable place growers head for


class RuleCognition:
    HUNGRY = 0.6
    STARVING = 0.25
    SEEK_CHANCE = 0.08
    TRADE_CHANCE = 0.5       # how readily surplus is handed to a neighbour who needs it
    TRADE_SURPLUS = 2.0      # a good is spare once you hold at least this much
    WORK_CHANCE = 0.5        # how readily a well-fed villager turns to their trade
    WORK_VITALITY = 0.72     # only work once survival is secured
    WORK_DANGER_CAP = 0.15   # only *travel* to work at safe ground; risky ground is worked only if already there
    WORK_MAX_RISK = 0.15     # auto-work only the safe trades; the perilous ones are the player's

    def _work(self, a: "Agent", world: "World", thought: str) -> Decision | None:
        """Ply a trade — if it can be done where you stand, or at safe ground you
        can reach. Never marches a villager into danger to work; the perilous
        gathers (mining, hunting deep) are the player's to brave."""
        from . import crafts
        prof = crafts.PROFESSIONS.get(a.vocation)
        if prof is None or prof.risk > self.WORK_MAX_RISK:
            return None
        if a.location in prof.places:
            if not crafts.why_not(prof, a.location, a.goods):
                return Decision("work", thought=thought)
            return None                              # missing inputs — live normally
        for place in prof.places:
            if PLACES.get(place, {}).get("danger", 1.0) <= self.WORK_DANGER_CAP:
                return Decision("move", place=place, thought=thought)
        return None

    def decide(self, agent: "Agent", world: "World", rng: "random.Random") -> Decision:
        a = agent
        thought = _mood(f"{a.id}:{world.tick}:{a.location}:{a.condition}:{a.wants.focus}")

        # 1. eat what you carry when you're not thriving
        if a.vitality < 0.7 and a.bloom > 0.2:
            return Decision("eat", thought=thought)

        need_food = a.vitality < self.HUNGRY or a.bloom < 1.0
        if need_food:
            # desperation can turn to force
            if a.vitality < self.STARVING and a.bloom < 0.2:
                prey = [o for o in world.co_located(a) if o.bloom > 0.6 and a.affinity(o.id) <= 0]
                if prey and rng.random() < 0.5:
                    prey.sort(key=lambda o: o.bloom, reverse=True)
                    return Decision("seize", target=prey[0].id, thought=thought)
            here = PLACES[a.location]
            soil_here = world.bloom.get(a.location, 0.0)
            grower = a.genome.grow_skill >= a.genome.forage_skill
            if grower:
                if here["arable"] and soil_here >= config.GROW_SOIL_MIN:
                    return Decision("grow", thought=thought)
                # the soil here is dead — seek living farmland, or turn forager
                best = max((p for p, d in PLACES.items() if d["arable"]),
                           key=lambda p: world.bloom.get(p, 0.0))
                if world.bloom.get(best, 0.0) >= config.GROW_SOIL_MIN and best != a.location:
                    return Decision("move", place=best, thought=thought)
                if here["wild"] > 0 and soil_here > 0.5:
                    return Decision("forage", thought=thought)
                return Decision("move", place=_forage_ground(_boldness(a)), thought=thought)
            if here["wild"] > 0 and soil_here > 0.5:
                return Decision("forage", thought=thought)
            return Decision("move", place=_forage_ground(_boldness(a)), thought=thought)

        # at night the village goes home to rest (the well-fed, at least)
        if world.phase() == "night":
            if a.location != config.STARTING_PLACE:
                return Decision("move", place=config.STARTING_PLACE, thought=thought)
            return Decision("rest", thought=thought)

        # 2. thriving and bonded: sometimes breed
        if a.vitality > 0.8 and world._fertile(a):
            partners = [o for o in world.co_located(a)
                        if world._fertile(o) and a.affinity(o.id) > 0]
            if partners and rng.random() < 0.12:
                partners.sort(key=lambda o: a.affinity(o.id), reverse=True)
                return Decision("mate", target=partners[0].id, thought=thought)

        # 3. surplus: sometimes feed a struggling friend
        if a.bloom > 3.0:
            needy = [o for o in world.co_located(a)
                     if a.affinity(o.id) > 0 and o.vitality < 0.5]
            if needy and rng.random() < 0.35:
                return Decision("give", target=needy[0].id, thought=thought)

        # 3b. hand a surplus good to a neighbour whose trade needs it — the
        # economy circulates: a shepherd's wool reaches the weaver, ore the smith
        if a.goods:
            from . import crafts
            for o in world.co_located(a):
                if a.affinity(o.id) < 0:
                    continue
                good = next((g for g, q in a.goods.items()
                             if q >= self.TRADE_SURPLUS and crafts.needs_good(o.vocation, g)), None)
                if good is not None:
                    if rng.random() < self.TRADE_CHANCE:
                        return Decision("trade", target=o.id, good=good, thought=thought)
                    break

        # 4. turn to you now and then
        if rng.random() < self.SEEK_CHANCE:
            return Decision("seek", thought=thought)

        # the belly is full and the day is yours: ply your trade
        if a.vocation and a.vitality >= self.WORK_VITALITY and rng.random() < self.WORK_CHANCE:
            work = self._work(a, world, thought)
            if work is not None:
                return work

        # 5. pursue the social want that gives life meaning
        focus = a.wants.focus
        dest = "the commons" if focus in SOCIAL_WANTS else PLACE_FOR.get(focus)
        if dest and a.location != dest:
            return Decision("move", place=dest, thought=thought)
        neighbours = world.co_located(a)
        if neighbours and rng.random() < 0.6:
            neighbours.sort(key=lambda o: a.affinity(o.id), reverse=True)
            best = neighbours[0]
            target = best if a.affinity(best.id) > 0 else rng.choice(neighbours)
            return Decision("speak", target=target.id, thought=thought)
        return Decision("rest", thought=thought)


_SYSTEM = (
    "You are a living being in a small, dangerous world. You must eat bloom or "
    "weaken and die; you age; you can bear children. You speak a private tongue. "
    "Weigh your situation and choose ONE action, replying in exactly this form:\n"
    "ACTION: move|forage|grow|work|eat|give|seize|mate|speak|seek|rest\n"
    "PLACE: <a place name, or ->\n"
    "TO: <a being's name, or ->\n"
    "THOUGHT: <one short first-person sentence>\n"
    "forage = gather wild bloom (dangerous). grow = cultivate bloom (safe, can "
    "fail). work = ply your trade where it can be done. eat = eat what you carry. "
    "give/seize/mate/speak act on a being beside you. seek = turn to the one who "
    "understands every tongue. Only act on a being that is here with you."
)

_ACTIONS_WITH_TARGET = {"give", "seize", "mate", "speak"}


class ClaudeCognition:
    def __init__(self, llm: "LiveLLM", fallback: Cognition | None = None) -> None:
        self._llm = llm
        self._fallback = fallback or RuleCognition()

    def decide(self, agent: "Agent", world: "World", rng: "random.Random") -> Decision:
        try:
            reply = self._llm.complete(
                tier=world.tier_now(pivotal=agent.is_old or agent.vitality < 0.25),
                system=_SYSTEM,
                user=self._situation(agent, world),
                max_tokens=130,
            )
            decision = self._parse(reply, agent, world)
        except Exception:
            return self._fallback.decide(agent, world, rng)
        if decision is None:
            fb = self._fallback.decide(agent, world, rng)
            voice = self._field(reply, "THOUGHT")
            if voice:
                fb.thought = voice
            return fb
        return decision

    def _situation(self, agent: "Agent", world: "World") -> str:
        a = agent
        here = PLACES[a.location]
        affords = ", ".join(here["affords"]) or "nothing social"
        stock = world.bloom.get(a.location, 0.0)
        danger = ("safe" if here["danger"] < 0.1 else
                  "risky" if here["danger"] < 0.45 else "deadly")
        others = world.co_located(a)
        if others:
            def gloss(o: "Agent") -> str:
                bond = a.affinity(o.id)
                tie = "kin/friend" if bond > 1 else ("an enemy" if bond < 0 else "a stranger")
                return f"{o.name} ({tie}, {o.condition}, holds {o.bloom:.0f} bloom)"
            beside = "; ".join(gloss(o) for o in others)
        else:
            beside = "no one"
        places = "\n".join(
            f"  {p}: {'/'.join(d['affords']) or 'wild'}, "
            f"{'arable' if d['arable'] else 'not arable'}, "
            f"{'safe' if d['danger'] < 0.1 else 'risky' if d['danger'] < 0.45 else 'deadly'}"
            for p, d in PLACES.items())
        memory = " | ".join(a.memory.recent(4)) or "nothing yet"
        temper = ("bold" if a.genome.bravery > 0.66 else
                  "cautious" if a.genome.bravery < 0.4 else "steady")
        beast = (f"The beast is HERE with you." if world.predator == a.location
                 else f"The beast is said to prowl {world.predator}.")
        return (
            f"You are {a.name}. You are {a.condition} (vitality {a.vitality:.2f}), "
            f"age {a.age} of about {a.genome.lifespan}, holding {a.bloom:.1f} bloom.\n"
            f"You are gifted at {'growing' if a.genome.grow_skill > a.genome.forage_skill else 'foraging'}, "
            f"and by nature {temper}.\n"
            f"You are at {a.location}: {affords}; {danger} to forage; wild bloom here ~{stock:.0f}. {beast}\n"
            f"A lone forager is easy prey; foraging together is far safer.\n"
            f"Beside you: {beside}.\n"
            f"Right now you also want: {a.wants.focus}.\n"
            f"The places you know:\n{places}\n"
            f"Lately: {memory}\n"
            "What do you do?"
        )

    @staticmethod
    def _field(reply: str, key: str) -> str:
        for line in reply.splitlines():
            if line.strip().upper().startswith(key + ":"):
                return line.split(":", 1)[1].strip()
        return ""

    def _parse(self, reply: str, agent: "Agent", world: "World") -> Decision | None:
        action = self._field(reply, "ACTION").lower().strip()
        action = action.split()[0] if action else ""
        thought = self._field(reply, "THOUGHT") or _mood(reply)
        if action in ("forage", "grow", "work", "eat", "seek", "rest"):
            return Decision(action, thought=thought)
        if action == "move":
            place = self._match_place(self._field(reply, "PLACE"))
            if place is None or place == agent.location:
                return None
            return Decision("move", place=place, thought=thought)
        if action in _ACTIONS_WITH_TARGET:
            target = self._match_neighbour(self._field(reply, "TO"), agent, world)
            if target is None:
                return None
            return Decision(action, target=target, thought=thought)
        return None

    @staticmethod
    def _match_place(raw: str) -> str | None:
        raw = raw.strip().lower().lstrip("-").strip()
        if not raw:
            return None
        for place in PLACES:
            if raw in place.lower() or place.lower() in raw:
                return place
        return None

    @staticmethod
    def _match_neighbour(raw: str, agent: "Agent", world: "World") -> str | None:
        raw = raw.strip().lower()
        if not raw or raw == "-":
            return None
        for o in world.co_located(agent):
            if o.name.lower() == raw or o.name.lower() in raw or o.id == raw:
                return o.id
        return None
