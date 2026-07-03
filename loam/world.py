"""The world — a small society moving through a small geography, whether or not
you are watching.

Each tick, every being decides (via its cognition) to move toward what it wants,
speak to someone beside it, turn to you, or rest. Speaking happens in a private
tongue, so being understood is never free. A listener learns a word only when it
hears it *where that word's meaning is visible* — food-words at the spring,
trust-words at the commons. Abstract meanings are the hardest to ground alone,
which is where your translation matters most.

Out of that friction — wants, movement, misunderstanding, the occasional
breakthrough — a history accumulates that no one scripted.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import config
from .agent import Agent
from .cognition import Cognition, Decision, RuleCognition
from .config import PHYSICAL, PLACES, SOCIAL
from .language import Utterance


@dataclass
class World:
    seed: int = 7
    tick: int = 0
    agents: dict[str, Agent] = field(default_factory=dict)
    feed: list[str] = field(default_factory=list)          # things you'd notice
    utterances: list[Utterance] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)      # the common tongue over time
    present: bool = False                                  # are you here right now?
    cognition: Cognition = field(default_factory=RuleCognition, repr=False)

    # ---- construction -----------------------------------------------------
    @classmethod
    def seeded(cls, n_agents: int = 5, seed: int = 7) -> "World":
        w = cls(seed=seed)
        for i in range(n_agents):
            a = Agent.born(i)
            w.agents[a.id] = a
        w._log(f"A world wakes with {n_agents} beings at {config.STARTING_PLACE}, "
               "each speaking alone.")
        return w

    # ---- queries used by cognition ----------------------------------------
    def co_located(self, agent: Agent) -> list[Agent]:
        return [a for a in self.agents.values()
                if a.id != agent.id and a.location == agent.location]

    def tier_now(self, pivotal: bool = False) -> str:
        if self.present:
            return config.PIVOTAL if pivotal else config.REFLECTIVE
        return config.ROUTINE

    # ---- the loop ---------------------------------------------------------
    def _rng(self) -> random.Random:
        return random.Random(f"{self.seed}:{self.tick}")

    def step(self) -> None:
        self.tick += 1
        rng = self._rng()
        order = sorted(self.agents.values(), key=lambda a: a.id)
        rng.shuffle(order)
        for agent in order:
            decision = self.cognition.decide(agent, self, rng)
            self._apply(agent, decision, rng)
        self._settle()   # being somewhere quietly meets a physical need
        if self.tick == 1 or self.tick % 10 == 0:
            from . import metrics  # lazy: metrics reads the world we're building
            self.history.append(metrics.snapshot(self))

    def run(self, ticks: int) -> None:
        for _ in range(ticks):
            self.step()

    def _apply(self, agent: Agent, d: Decision, rng: random.Random) -> None:
        agent.last_thought = d.thought
        if d.kind == "move" and d.place and d.place != agent.location:
            agent.location = d.place
            agent.memory.remember(self.tick, f"went to {d.place} for {agent.wants.focus}")
        elif d.kind == "seek":
            self._speak_to_you(agent)
        elif d.kind == "speak" and d.target in self.agents:
            self._speak(agent, self.agents[d.target])
        else:  # rest, or a decision that no longer applies
            agent.memory.remember(self.tick, "rested")

    # ---- consequences -----------------------------------------------------
    def _speak(self, speaker: Agent, listener: Agent) -> None:
        if listener.location != speaker.location:
            return  # they wandered apart before the word landed
        concept = speaker.wants.focus
        word = speaker.language.say(concept)
        self.utterances.append(Utterance(self.tick, speaker.id, listener.id, word, concept))
        speaker.memory.remember(self.tick, f'said "{word}" ({concept}) to {listener.name}')

        if listener.lexicon.knows(word):
            self._understood(speaker, listener, concept, word)
            return

        legible = concept in PLACES.get(listener.location, ())
        if legible:
            learned = listener.lexicon.observe(word, concept, config.GROUNDING_THRESHOLD)
            if learned:
                self._breakthrough(speaker, listener, concept, word)
                return
            listener.memory.remember(
                self.tick, f'heard "{word}" from {speaker.name} at {listener.location} — a guess forms')
        else:
            listener.memory.remember(
                self.tick, f'heard "{word}" from {speaker.name} — meaning unclear')

    def _understood(self, speaker: Agent, listener: Agent, concept: str, word: str) -> None:
        speaker.warm_to(listener.id)
        listener.warm_to(speaker.id)
        if concept in SOCIAL:
            speaker.wants.satisfy()
            listener.wants.satisfy(0.25)
        listener.memory.remember(self.tick, f'understood {speaker.name}: {concept}')
        self._log(f'{listener.name} understood {speaker.name} — "{word}" means {concept}.')

    def _breakthrough(self, speaker: Agent, listener: Agent, concept: str, word: str) -> None:
        speaker.warm_to(listener.id, 1.5)
        listener.warm_to(speaker.id, 1.5)
        listener.memory.remember(self.tick, f'LEARNED "{word}" = {concept} (from {speaker.name})')
        self._log(f'{listener.name} finally learned that {speaker.name}\'s "{word}" means {concept}.')

    def _speak_to_you(self, speaker: Agent) -> None:
        concept = speaker.wants.focus
        word = speaker.language.say(concept)
        self.utterances.append(Utterance(self.tick, speaker.id, "glenn", word, concept))
        speaker.wants.satisfy(0.25)   # being understood by you eases the want a little
        speaker.memory.remember(self.tick, f'turned to you, said "{word}" ({concept})')
        self._log(Utterance(self.tick, speaker.id, "glenn", word, concept).heard_by_glenn())

    def _settle(self) -> None:
        """Being where a physical need lives quietly meets it."""
        for a in self.agents.values():
            focus = a.wants.focus
            if focus in PHYSICAL and focus in PLACES.get(a.location, ()):
                a.wants.satisfy(0.34)
                a.memory.remember(self.tick, f"found {focus} at {a.location}")

    def _log(self, text: str) -> None:
        self.feed.append(f"[t{self.tick}] {text}")

    # ---- your levers (the gardener, not the god) --------------------------
    def translate(self, symbol: str, for_agent_id: str) -> str:
        """Grant one being the meaning of a word it has heard. Your main way of
        helping them reach each other — worth most for the abstract words that
        are hardest to learn by watching."""
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
        """Sit with one being."""
        a = self.agents.get(agent_id)
        if a is None:
            return f"No such being: {agent_id}"
        learned = ", ".join(f'"{w}"={c}' for w, c in a.lexicon.known.items()) or "nothing yet"
        recent = "\n    ".join(a.memory.recent()) or "(no memories)"
        friends = sorted(a.relationships.items(), key=lambda kv: kv[1], reverse=True)
        bonds = ", ".join(f"{self.agents[i].name}({v:.1f})"
                          for i, v in friends[:3] if i in self.agents) or "no one yet"
        return (
            f"{a.name} ({a.id}) — at {a.location}\n"
            f"  wants: {a.wants.describe()}\n"
            f"  thought: {a.last_thought or '(quiet)'}\n"
            f"  closest to: {bonds}\n"
            f"  understands: {learned}\n"
            f"  lately:\n    {recent}"
        )
