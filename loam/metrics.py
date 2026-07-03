"""Measuring the thing worth watching: is a shared tongue forming?

A world of private languages could stay forever mutually unintelligible. What
makes it a *civilization* is the slow spread of understanding — words that
escape their inventor and become common ground. These functions measure that,
and render the chronicle you read in the morning.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .world import World


def owners(world: "World") -> dict[str, tuple[str, str]]:
    """Every private word in the world -> (owner_id, concept)."""
    out: dict[str, tuple[str, str]] = {}
    for a in world.agents.values():
        for concept, word in a.language.word_of.items():
            out[word] = (a.id, concept)
    return out


def coverage(world: "World") -> tuple[float, int, int]:
    """How connected the world is by understanding.

    Returns (fraction, comprehension_edges, total_directed_pairs), where an edge
    (listener -> speaker) exists when the listener knows at least one of the
    speaker's words.
    """
    agents = list(world.agents.values())
    n = len(agents)
    total = n * (n - 1)
    if total == 0:
        return (0.0, 0, 0)
    own = owners(world)
    edges = 0
    for listener in agents:
        reaches: set[str] = set()
        for word in listener.lexicon.known:
            owner = own.get(word)
            if owner and owner[0] != listener.id:
                reaches.add(owner[0])
        edges += len(reaches)
    return (edges / total, edges, total)


def word_spread(world: "World") -> list[tuple[str, str, str, int]]:
    """Words that have escaped their inventor, most-spread first.

    Each entry: (word, concept, owner_name, number_of_other_beings_who_know_it).
    """
    own = owners(world)
    names = {a.id: a.name for a in world.agents.values()}
    counts: dict[str, int] = {}
    for a in world.agents.values():
        for word in a.lexicon.known:
            o = own.get(word)
            if o and o[0] != a.id:
                counts[word] = counts.get(word, 0) + 1
    rows = []
    for word, count in counts.items():
        owner_id, concept = own[word]
        rows.append((word, concept, names.get(owner_id, owner_id), count))
    rows.sort(key=lambda r: (-r[3], r[0]))
    return rows


def snapshot(world: "World") -> dict:
    """A point-in-time record for the world's growth curve."""
    frac, edges, total = coverage(world)
    total_known = sum(len(a.lexicon.known) for a in world.agents.values())
    return {"tick": world.tick, "coverage": round(frac, 4),
            "edges": edges, "total_pairs": total, "words_learned": total_known}


def _notable(world: "World", limit: int = 12) -> list[str]:
    keys = ("learned", "understood", "told", "means")
    hits = [line for line in world.feed if any(k in line for k in keys)]
    return hits[-limit:]


def chronicle(world: "World") -> str:
    """The morning report — what the night made of the world."""
    frac, edges, total = coverage(world)
    lines: list[str] = []
    lines.append(f"═══ Loam — the world at tick {world.tick} ═══")
    lines.append(f"{len(world.agents)} beings, {len(world.utterances)} things said.")
    lines.append("")

    # growth of the common tongue
    lines.append(f"A shared tongue is {frac * 100:.0f}% formed "
                 f"({edges} of {total} understanding-links live).")
    if world.history:
        first = world.history[0]
        lines.append(f"  (began at {first['coverage'] * 100:.0f}% on tick {first['tick']}.)")
    lines.append("")

    # words that escaped their inventor
    spread = word_spread(world)
    if spread:
        lines.append("Words that have spread:")
        for word, concept, owner, count in spread[:6]:
            others = "being" if count == 1 else "beings"
            lines.append(f'  "{word}" (= {concept}, first {owner}\'s) — known by {count} other {others}')
    else:
        lines.append("No word has yet escaped its inventor. They are still alone in their tongues.")
    lines.append("")

    # who reaches whom
    lines.append("Each being now understands:")
    for a in sorted(world.agents.values(), key=lambda x: x.id):
        lines.append(f"  {a.name}: {a.understands_count()} foreign words — at {a.location}, wanting {a.wants.focus}")
    lines.append("")

    # moments
    moments = _notable(world)
    if moments:
        lines.append("Moments worth remembering:")
        lines.extend(f"  {m}" for m in moments)
        lines.append("")

    lines.append("The world is still turning. Come tend it.")
    return "\n".join(lines)
