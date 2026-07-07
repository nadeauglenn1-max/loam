"""Converse — when you meet a being, they speak.

A being speaks in its own private tongue, and whether you can read it depends on
the words you have earned from its family. This is the founding conceit made
tangible: a stranger is *opaque*, their speech a sound you cannot parse, and only
as you help their family and earn their words does what they say come clear. It
is the reward for understanding, felt in the moment you stand before someone.

The line itself comes from a model-agnostic ``Voice`` — a free ``RuleVoice`` by
default (and the safe fallback), a ``ClaudeVoice`` when you want a living line.
Legibility is the mechanic; the voice only colours it.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from . import config, rifts

if TYPE_CHECKING:  # pragma: no cover
    from .llm import LiveLLM


def overheard(player, being) -> dict:
    """What a being says, and whether you can understand it. `concept` is what
    they reach for; `word` is their own word for it; `legible` is whether you've
    earned that word from their family (or come to understand the family whole)."""
    concept = being.wants.focus
    word = being.language.say(concept)
    fam = rifts.family_of(being)
    legible = player.understands(fam) or concept in player.words.get(fam, [])
    return {"concept": concept, "word": word, "family": fam, "legible": legible}


# what body language shows when you cannot read the words — never the meaning
_BEARING = {
    "company": "reaching toward you", "status": "standing a little straighter",
    "trust": "watching your eyes", "safety": "glancing toward shelter",
    "rest": "weary to the bone", "novelty": "restless, looking past you",
}


class Voice(Protocol):
    def speak(self, being, concept: str, legible: bool) -> str:
        ...


class RuleVoice:
    """Free and deterministic: their word, and its meaning only if you can read it."""

    def speak(self, being, concept: str, legible: bool) -> str:
        word = being.language.say(concept)
        bearing = _BEARING.get(concept, "speaking")
        if legible:
            return f'"{word}" — {being.name}, {bearing}. You understand: {concept}.'
        return f'"{word}" — {being.name} speaks, {bearing}; the word is still strange to you.'


_SYSTEM = (
    "You are a being in a small village, speaking to the one person who might come "
    "to understand you. Say ONE short, in-character line (first person, under 16 "
    "words) about what you want right now. Only the line, nothing else."
)


class ClaudeVoice:
    """A living line from a model when you can understand them; the rule voice
    catches every failure and always speaks for a stranger you can't yet read."""

    def __init__(self, llm: "LiveLLM", fallback: Voice | None = None) -> None:
        self._llm = llm
        self._fallback = fallback or RuleVoice()

    def speak(self, being, concept: str, legible: bool) -> str:
        if not legible:
            return self._fallback.speak(being, concept, legible)
        try:
            reply = self._llm.complete(
                tier=config.REFLECTIVE, system=_SYSTEM,
                user=f"You are {being.name}. You are {being.condition}. "
                     f"Right now you want: {concept}.",
                max_tokens=60)
            line = reply.strip().splitlines()[0].strip().strip('"')[:160]
            if not line:
                return self._fallback.speak(being, concept, legible)
            word = being.language.say(concept)
            return f'"{word}" — {being.name}: "{line}" ({concept})'
        except Exception:
            return self._fallback.speak(being, concept, legible)
