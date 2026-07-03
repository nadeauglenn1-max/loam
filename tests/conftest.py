"""Shared test helpers."""
from __future__ import annotations


class ScriptedRandom:
    """A deterministic stand-in for random.Random with scripted draws, so a
    cognition policy can be walked down an exact branch."""

    def __init__(self, randoms=(), choice_index: int = 0):
        self._randoms = list(randoms)
        self._i = 0
        self._choice_index = choice_index

    def random(self) -> float:
        v = self._randoms[self._i] if self._i < len(self._randoms) else 0.5
        self._i += 1
        return v

    def choice(self, seq):
        return seq[self._choice_index]

    def shuffle(self, seq) -> None:  # pragma: no cover - order irrelevant in tests
        pass


class FakeLLM:
    """Returns a canned reply and records the calls it received."""

    def __init__(self, reply: str):
        self.reply = reply
        self.calls: list[dict] = []

    def complete(self, **kwargs) -> str:
        self.calls.append(kwargs)
        return self.reply


class RaisingLLM:
    def complete(self, **kwargs) -> str:
        raise RuntimeError("network is down")
