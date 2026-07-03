"""Private languages and the slow work of learning to understand each other.

Every agent is born speaking a language only it (and you) can read. When one
agent speaks to another, the listener hears *symbols*, not meaning. Meaning is
earned two ways:
  1. You translate it (fast, participatory — the gardener's lever).
  2. Grounded repetition: hearing a symbol again and again while watching the
     speaker act on it (slow, autonomous).

You are the only one who understands everyone. That is not authority — it is
the ability to help.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from .config import CONCEPTS

# Syllable stock used to invent each agent's private words. Deterministic per
# agent, so a world reloads identically.
_SYLLABLES = ("ka", "lo", "mi", "ru", "sha", "te", "vo", "wei", "na", "zi",
              "qua", "el", "or", "um", "ba", "ie", "fen", "gri", "shu", "tau")


def _rng_int(seed: str, n: int) -> int:
    """Deterministic non-negative int from a string seed."""
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(h, 16) % n


def coin_word(agent_id: str, concept: str) -> str:
    """Invent this agent's private word for a concept — stable across reloads."""
    base = f"{agent_id}:{concept}"
    a = _SYLLABLES[_rng_int(base + ":a", len(_SYLLABLES))]
    b = _SYLLABLES[_rng_int(base + ":b", len(_SYLLABLES))]
    return a + b


@dataclass
class PrivateLanguage:
    """An agent's own tongue: concept <-> invented word, both directions."""
    agent_id: str
    word_of: dict[str, str] = field(default_factory=dict)
    concept_of: dict[str, str] = field(default_factory=dict)

    @classmethod
    def for_agent(cls, agent_id: str) -> "PrivateLanguage":
        word_of = {c: coin_word(agent_id, c) for c in CONCEPTS}
        concept_of = {w: c for c, w in word_of.items()}
        return cls(agent_id=agent_id, word_of=word_of, concept_of=concept_of)

    @classmethod
    def inherit(cls, parent: "PrivateLanguage", child_id: str, rng, drift: float | None = None
                ) -> "PrivateLanguage":
        """A child's tongue: mostly a parent's words, some freshly coined. Kin
        thus share most of their language and understand each other natively —
        the seed of dialect-tribes."""
        from .config import LANGUAGE_DRIFT
        drift = LANGUAGE_DRIFT if drift is None else drift
        word_of = {}
        for c in CONCEPTS:
            word_of[c] = coin_word(child_id, c) if rng.random() < drift else parent.word_of[c]
        concept_of = {w: c for c, w in word_of.items()}
        return cls(agent_id=child_id, word_of=word_of, concept_of=concept_of)

    def say(self, concept: str) -> str:
        return self.word_of[concept]

    def understand(self, word: str) -> str | None:
        """Owner-side decode. Returns the concept, or None if not this tongue."""
        return self.concept_of.get(word)


@dataclass
class Lexicon:
    """What one agent has learned of *other* agents' words.

    known:     foreign word -> concept it has fully learned.
    evidence:  foreign word -> grounded-hit count building toward learning it.
    """
    known: dict[str, str] = field(default_factory=dict)
    evidence: dict[str, int] = field(default_factory=dict)

    def knows(self, word: str) -> bool:
        return word in self.known

    def teach(self, word: str, concept: str) -> None:
        """Direct instruction — your translation, or a fully grounded word."""
        self.known[word] = concept
        self.evidence.pop(word, None)

    def observe(self, word: str, concept: str, threshold: int) -> bool:
        """Record one grounded co-occurrence. Returns True if the word is now
        learned. `concept` is the *true* meaning the world knows — the agent
        never sees it directly, only accumulates evidence that this word tends
        to accompany this outcome."""
        if word in self.known:
            return False
        self.evidence[word] = self.evidence.get(word, 0) + 1
        if self.evidence[word] >= threshold:
            self.teach(word, concept)
            return True
        return False


@dataclass
class Utterance:
    """Something said. `symbol` is what the listener hears; `concept` is the
    truth, visible only to the speaker and to you."""
    tick: int
    speaker_id: str
    listener_id: str      # another agent's id, or "glenn"
    symbol: str
    concept: str

    def heard_by_glenn(self) -> str:
        return f'{self.speaker_id} → you: "{self.symbol}" ({self.concept})'
