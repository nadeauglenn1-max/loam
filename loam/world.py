"""The world — a small society that runs whether or not you're watching.

Each tick, every agent reaches toward what it currently wants by speaking to
another agent. But it speaks in its own tongue, so being understood is never
free: it has to be earned through repetition, or granted by your translation.
Out of that friction, relationships, misunderstandings, and small breakthroughs
accumulate into a history.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import config
from .agent import Agent
from .language import Utterance
from .model import Model, MockModel

# Wants that are met simply by being understood by another.
_SOCIAL = ("company", "trust", "status")

_SYSTEM = (
    "You are a being in a small world, speaking a private language no one else "
    "was born knowing. You are reaching for something you want and trying to be "
    "understood. Answer with one short, first-person sentence of what you feel "
    "right now. No preamble."
)


@dataclass
class World:
    seed: int = 7
    tick: int = 0
    agents: dict[str, Agent] = field(default_factory=dict)
    feed: list[str] = field(default_factory=list)          # things you'd notice
    utterances: list[Utterance] = field(default_factory=list)
    present: bool = False                                  # are you here right now?
    model: Model = field(default_factory=MockModel, repr=False)

    # ---- construction -----------------------------------------------------
    @classmethod
    def seeded(cls, n_agents: int = 5, seed: int = 7) -> "World":
        w = cls(seed=seed)
        for i in range(n_agents):
            a = Agent.born(i)
            w.agents[a.id] = a
        w._log(f"A world wakes with {n_agents} beings, each speaking alone.")
        return w

    # ---- the loop ---------------------------------------------------------
    def _rng(self) -> random.Random:
        return random.Random(f"{self.seed}:{self.tick}")

    def _tier(self, pivotal: bool) -> str:
        if self.present:
            return config.PIVOTAL if pivotal else config.REFLECTIVE
        return config.ROUTINE

    def step(self) -> None:
        """Advance the world by one tick."""
        self.tick += 1
        rng = self._rng()
        order = sorted(self.agents.values(), key=lambda a: a.id)
        rng.shuffle(order)
        for speaker in order:
            self._act(speaker, rng)

    def run(self, ticks: int) -> None:
        for _ in range(ticks):
            self.step()

    def _act(self, speaker: Agent, rng: random.Random) -> None:
        others = [a for a in self.agents.values() if a.id != speaker.id]
        if not others:
            return
        concept = speaker.wants.focus

        # Sometimes an agent turns to you instead of the others — sought
        # individually, never in worship.
        if rng.random() < 0.12:
            self._speak_to_glenn(speaker, concept)
            return

        # Prefer someone it already trusts; otherwise a stranger.
        others.sort(key=lambda a: speaker.affinity(a.id), reverse=True)
        listener = others[0] if speaker.affinity(others[0].id) > 0 else rng.choice(others)

        word = speaker.language.say(concept)
        utt = Utterance(self.tick, speaker.id, listener.id, word, concept)
        self.utterances.append(utt)

        speaker.last_thought = self.model.inner_voice(
            tier=self._tier(pivotal=False),
            system=_SYSTEM,
            situation=(f"You are {speaker.name}. You want {concept}. "
                       f"You say '{word}' to {listener.name}, who may not understand."),
        )
        speaker.memory.remember(self.tick, f'said "{word}" ({concept}) to {listener.name}')

        if listener.lexicon.knows(word):
            self._understood(speaker, listener, concept, word)
        else:
            learned = listener.lexicon.observe(word, concept, config.GROUNDING_THRESHOLD)
            if learned:
                self._breakthrough(speaker, listener, concept, word)
            else:
                listener.memory.remember(self.tick, f'heard "{word}" from {speaker.name} — unknown')

    # ---- outcomes ---------------------------------------------------------
    def _understood(self, speaker: Agent, listener: Agent, concept: str, word: str) -> None:
        speaker.warm_to(listener.id)
        listener.warm_to(speaker.id)
        if concept in _SOCIAL:
            speaker.wants.satisfy()
            listener.wants.satisfy(0.25)
        listener.memory.remember(self.tick, f'understood {speaker.name}: {concept}')
        self._log(f'{listener.name} understood {speaker.name} — "{word}" means {concept}.')

    def _breakthrough(self, speaker: Agent, listener: Agent, concept: str, word: str) -> None:
        speaker.warm_to(listener.id, 1.5)
        listener.warm_to(speaker.id, 1.5)
        listener.memory.remember(self.tick, f'LEARNED "{word}" = {concept} (from {speaker.name})')
        self._log(
            f'{listener.name} finally learned that {speaker.name}\'s "{word}" means {concept}.'
        )

    def _speak_to_glenn(self, speaker: Agent, concept: str) -> None:
        word = speaker.language.say(concept)
        utt = Utterance(self.tick, speaker.id, "glenn", word, concept)
        self.utterances.append(utt)
        speaker.wants.satisfy(0.25)  # being understood by you eases the want a little
        speaker.memory.remember(self.tick, f'turned to you, said "{word}" ({concept})')
        self._log(utt.heard_by_glenn())

    def _log(self, text: str) -> None:
        self.feed.append(f"[t{self.tick}] {text}")

    # ---- your levers (the gardener, not the god) --------------------------
    def translate(self, symbol: str, for_agent_id: str) -> str:
        """Grant one agent the meaning of a word it has heard. Your main way of
        helping them reach each other — horizontal, never a decree."""
        listener = self.agents.get(for_agent_id)
        if listener is None:
            return f"No such being: {for_agent_id}"
        for owner in self.agents.values():
            concept = owner.language.understand(symbol)
            if concept is not None:
                listener.lexicon.teach(symbol, concept)
                listener.memory.remember(self.tick, f'you taught: "{symbol}" = {concept}')
                self._log(f'You told {listener.name} that "{symbol}" means {concept}.')
                return f'{listener.name} now understands "{symbol}" = {concept}.'
        return f'No one in this world speaks "{symbol}".'

    def visit(self, agent_id: str) -> str:
        """Sit with one being. What it wants, what it recalls, what it has come
        to understand of the others."""
        a = self.agents.get(agent_id)
        if a is None:
            return f"No such being: {agent_id}"
        learned = ", ".join(f'"{w}"={c}' for w, c in a.lexicon.known.items()) or "nothing yet"
        recent = "\n    ".join(a.memory.recent()) or "(no memories)"
        return (
            f"{a.name} ({a.id})\n"
            f"  wants: {a.wants.describe()}\n"
            f"  thought: {a.last_thought or '(quiet)'}\n"
            f"  understands: {learned}\n"
            f"  lately:\n    {recent}"
        )
