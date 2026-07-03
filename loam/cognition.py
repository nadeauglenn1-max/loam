"""Cognition — how an agent decides what to do with its tick.

Two implementations behind one seam:

* `RuleCognition` — deterministic, free, dependency-free. The default, the
  CI-safe engine, and the fallback when live cognition fails. It is not a
  placeholder: it is a real, legible policy.
* `ClaudeCognition` — a live Claude actually reasons about where to go and who
  to reach, at whatever model tier the world's attention economy has chosen. On
  any error or unparseable reply it defers to a wrapped `RuleCognition`, so a
  flaky network can never crash the world — it only makes it think more simply.

The world (world.py) owns the *consequences* of a decision; cognition owns only
the choice.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from . import config
from .config import PHYSICAL, PLACE_FOR, PLACES

if TYPE_CHECKING:  # pragma: no cover
    import random

    from .agent import Agent
    from .llm import LiveLLM
    from .world import World

# Terse interior lines, drawn deterministically so a mock world still has a
# voice and reloads replay identically.
_MOODS = (
    "I want this more than I can say.",
    "Does anyone here hear me?",
    "The words come out wrong every time.",
    "Maybe they'll understand if I try again.",
    "I am tired of being alone in my own tongue.",
    "There is something I almost recognized just now.",
    "If I could only make myself plain.",
    "I keep circling the same need.",
    "Someone looked at me like they knew.",
    "I'll go where the thing I want lives.",
)


def _mood(situation: str) -> str:
    h = hashlib.sha256(situation.encode("utf-8")).hexdigest()
    return _MOODS[int(h[:8], 16) % len(_MOODS)]


@dataclass
class Decision:
    """What an agent chooses this tick.

    kind:   "move" | "speak" | "seek" | "rest"
    place:  destination (for "move")
    target: another agent's id (for "speak")
    thought: one line of interior voice
    """
    kind: str
    place: str | None = None
    target: str | None = None
    thought: str = ""


class Cognition(Protocol):
    def decide(self, agent: "Agent", world: "World", rng: "random.Random") -> Decision:
        ...


class RuleCognition:
    """A legible policy: go where your want lives; speak to those beside you."""

    SEEK_CHANCE = 0.10   # sometimes turn to the one who understands everyone
    SPEAK_CHANCE = 0.5   # once where your need lives, reach out or rest

    def decide(self, agent: "Agent", world: "World", rng: "random.Random") -> Decision:
        focus = agent.wants.focus
        situation = f"{agent.id}:{world.tick}:{agent.location}:{focus}"
        thought = _mood(situation)

        if rng.random() < self.SEEK_CHANCE:
            return Decision("seek", thought=thought)

        dest = PLACE_FOR[focus]
        if agent.location != dest:
            return Decision("move", place=dest, thought=thought)

        # At the place this want lives. Reach for a neighbour, or settle.
        neighbours = world.co_located(agent)
        if neighbours and rng.random() < self.SPEAK_CHANCE:
            neighbours.sort(key=lambda a: agent.affinity(a.id), reverse=True)
            best = neighbours[0]
            target = best if agent.affinity(best.id) > 0 else rng.choice(neighbours)
            return Decision("speak", target=target.id, thought=thought)
        return Decision("rest", thought=thought)


_SYSTEM = (
    "You are a being in a small world, speaking a private language no one else "
    "was born knowing. You move between places, reach for what you want, and try "
    "to be understood. You are not performing for anyone. Decide your next move "
    "and reply in exactly this form, nothing else:\n"
    "ACTION: move|speak|seek|rest\n"
    "PLACE: <a place name, or ->\n"
    "TO: <a being's name, or ->\n"
    "THOUGHT: <one short first-person sentence>\n"
    "'seek' means turning to the one who understands every tongue. Only 'speak' "
    "to a being that is here beside you."
)


class ClaudeCognition:
    """Live cognition. A real Claude chooses; the rules catch it if it falls."""

    def __init__(self, llm: "LiveLLM", fallback: Cognition | None = None) -> None:
        self._llm = llm
        self._fallback = fallback or RuleCognition()

    def decide(self, agent: "Agent", world: "World", rng: "random.Random") -> Decision:
        try:
            reply = self._llm.complete(
                tier=world.tier_now(),
                system=_SYSTEM,
                user=self._situation(agent, world),
                max_tokens=120,
            )
            decision = self._parse(reply, agent, world)
        except Exception:  # network / SDK / anything — the world must not stop
            return self._fallback.decide(agent, world, rng)
        if decision is None:
            fb = self._fallback.decide(agent, world, rng)
            # keep the model's voice even when its choice was unusable
            parsed_thought = self._field(reply, "THOUGHT")
            if parsed_thought:
                fb.thought = parsed_thought
            return fb
        return decision

    # -- prompt / parse -----------------------------------------------------
    def _situation(self, agent: "Agent", world: "World") -> str:
        here = agent.location
        affords = ", ".join(PLACES.get(here, ())) or "nothing in particular"
        others = world.co_located(agent)
        if others:
            def gloss(o: "Agent") -> str:
                bond = agent.affinity(o.id)
                tie = "a friend" if bond > 1 else ("familiar" if bond > 0 else "a stranger")
                return f"{o.name} ({tie})"
            here_who = "; ".join(gloss(o) for o in others)
        else:
            here_who = "no one"
        places = "\n".join(f"  {p}: for {', '.join(c)}" for p, c in PLACES.items())
        memory = " | ".join(agent.memory.recent(4)) or "nothing yet"
        return (
            f"You are {agent.name}. Right now you want: {agent.wants.focus}.\n"
            f"You are at {here} (which offers: {affords}).\n"
            f"Beside you: {here_who}.\n"
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
        action = self._field(reply, "ACTION").lower()
        thought = self._field(reply, "THOUGHT") or _mood(reply)
        if action == "rest":
            return Decision("rest", thought=thought)
        if action == "seek":
            return Decision("seek", thought=thought)
        if action == "move":
            place = self._match_place(self._field(reply, "PLACE"))
            if place is None or place == agent.location:
                return None
            return Decision("move", place=place, thought=thought)
        if action == "speak":
            target = self._match_neighbour(self._field(reply, "TO"), agent, world)
            if target is None:
                return None
            return Decision("speak", target=target, thought=thought)
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
