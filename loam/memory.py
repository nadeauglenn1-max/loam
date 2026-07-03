"""Per-agent memory — the thing that makes an agent someone rather than a
process. A bounded log of what happened to it, kept across reloads so the world
accumulates a history no one scripted.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class Memory:
    agent_id: str
    capacity: int = 24
    events: deque[str] = field(default_factory=deque)

    def __post_init__(self) -> None:
        # deque default_factory can't take maxlen; enforce it here.
        self.events = deque(self.events, maxlen=self.capacity)

    def remember(self, tick: int, text: str) -> None:
        self.events.append(f"[t{tick}] {text}")

    def recent(self, n: int = 6) -> list[str]:
        return list(self.events)[-n:]
