"""Shared test helpers."""
from __future__ import annotations


class ScriptedRandom:
    """A deterministic stand-in for random.Random with scripted draws, so a
    stochastic path can be walked exactly. Unscripted draws return a default."""

    def __init__(self, randoms=(), choice_index: int = 0, default: float = 0.5):
        self._randoms = list(randoms)
        self._i = 0
        self._choice_index = choice_index
        self._default = default

    def random(self) -> float:
        v = self._randoms[self._i] if self._i < len(self._randoms) else self._default
        self._i += 1
        return v

    def uniform(self, a: float, b: float) -> float:
        return (a + b) / 2

    def gauss(self, mu: float, sigma: float) -> float:
        return mu

    def choice(self, seq):
        return seq[self._choice_index % len(seq)]

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
