"""Quests — a family's trouble, and the task that earns their trust.

You do not come to understand a family by sitting with them and nodding (that is
easy, and cheap). You understand them by *doing something for them*: their crops
are plagued, their woods run thick with wolves — go and see to it. Each family
has a trouble tied to what they are (farmers fear the fields, foragers the deep
wood), and clearing it is a real task — a fight, out in the world — that earns a
real measure of their understanding.

The quest is content: a family, a foe, a place, a count. Adding one — or changing
whose trouble is what — is a data row.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import rifts

# family -> (foe kind, the place it troubles, how many to cull)
FAMILY_TROUBLE: dict[str, tuple] = {
    "Vane":   ("gopher", "the meadow", 3),
    "Thorn":  ("wolf", "the thornwood", 3),
    "Fen":    ("bog serpent", "the mire", 3),
    "Bly":    ("goblin", "the thornwood", 3),
    "Ashmol": ("boar", "the deepwood", 2),
    "Unbound": ("cave rat", "the mire", 3),
}

_TELLING = {
    "gopher": "gophers are at the crops again",
    "wolf": "wolves run thick and bold",
    "bog serpent": "serpents trouble the water",
    "goblin": "goblins creep down from the rocks",
    "boar": "a boar has gone rank and dangerous",
    "cave rat": "vermin have overrun the place",
}
_WHERE = {"the meadow": "the fields", "the mire": "the marsh",
          "the thornwood": "the thornwood", "the deepwood": "the deep wood"}


@dataclass
class Quest:
    family: str
    target: str
    place: str
    need: int
    done: int = 0

    @property
    def complete(self) -> bool:
        return self.done >= self.need


def for_family(family: str) -> Quest | None:
    row = FAMILY_TROUBLE.get(family)
    return Quest(family, *row) if row else None


def telling(q: Quest) -> str:
    """How a villager describes their trouble."""
    where = _WHERE.get(q.place, q.place)
    return f"{_TELLING.get(q.target, q.target + 's plague us')} in {where} — cull {q.need}"


def offered_by(world, being) -> Quest | None:
    """The quest a being would give you: their family's trouble, unless you've
    already taken it on or already understand them."""
    fam = rifts.family_of(being)
    if fam in world.player.quests or world.player.understands(fam):
        return None
    return for_family(fam)
