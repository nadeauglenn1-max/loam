"""Instrumentation — how we see and learn from the world.

We do not detect "religion" or "money" directly; we measure the substrate they
would grow from — population and lineage, the toll of death, the economy of
sharing versus taking, and the clustering of beings into dialect-tribes — and we
read the run.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .config import CONCEPTS

if TYPE_CHECKING:  # pragma: no cover
    from .agent import Agent
    from .world import World

FACTION_SIMILARITY = 0.6   # share this fraction of words -> the same tongue


def owners(world: "World") -> dict[str, tuple[str, str]]:
    out: dict[str, tuple[str, str]] = {}
    for a in world.agents.values():
        for concept, word in a.language.word_of.items():
            out[word] = (a.id, concept)
    return out


def coverage(world: "World") -> tuple[float, int, int]:
    """Directed understanding-links between living beings / all possible pairs."""
    agents = list(world.agents.values())
    n = len(agents)
    total = n * (n - 1)
    if total == 0:
        return (0.0, 0, 0)
    edges = 0
    for listener in agents:
        reaches = {o.id for o in agents if o.id != listener.id
                   and any(listener.comprehends(o.language.word_of[c]) is not None for c in CONCEPTS)}
        edges += len(reaches)
    return (edges / total, edges, total)


def player_summary(world: "World") -> dict:
    """Who you have become — the shape of your journey so far."""
    from . import bonds, rifts
    p = world.player
    frac, done, total = rifts.progress(world)
    close = sorted(((b, lvl) for b, lvl in p.bonds.items() if lvl > 0), key=lambda kv: -kv[1])
    return {
        "name": p.name, "gender": p.gender,
        "understood": done, "families": total, "understanding": frac,
        "words_earned": sum(len(v) for v in p.words.values()),
        "trades": sorted(((t, lvl) for t, lvl in p.skills.items() if lvl > 0),
                         key=lambda kv: -kv[1]),
        "spouse": world.agents[p.spouse].name if p.spouse in world.agents else "",
        "children": [world.agents[c].name for c in p.children if c in world.agents],
        "closest": [(world.agents[b].name, bonds.tier(lvl, wed=(b == p.spouse)))
                    for b, lvl in close[:5] if b in world.agents],
    }


def tongue_trend(world: "World", window: int = 5) -> tuple[float, float, str]:
    """How the shared tongue has moved lately — it is a living thing, rising as
    beings learn each other and fraying as elders (and their words) are lost and
    newborns arrive speaking a drifted tongue. Returns (now, change, word)."""
    frac, _edges, _total = coverage(world)
    hist = [h["coverage"] for h in world.history if "coverage" in h]
    if len(hist) < 2:
        return (frac, 0.0, "still forming")
    earlier = hist[max(0, len(hist) - 1 - window)]
    d = frac - earlier
    word = "holding steady" if abs(d) < 0.02 else ("growing" if d > 0 else "fraying")
    return (frac, d, word)


def family_cohesion(world: "World", family: str) -> tuple[float, int]:
    """How well a family's own living members understand each other."""
    from .rifts import family_of
    members = [a for a in world.agents.values() if a.alive and family_of(a) == family]
    n = len(members)
    total = n * (n - 1)
    if total == 0:
        return (0.0, n)
    edges = sum(1 for listener in members for o in members if o.id != listener.id
                and any(listener.comprehends(o.language.word_of[c]) is not None for c in CONCEPTS))
    return (edges / total, n)


def word_spread(world: "World") -> list[tuple[str, str, str, int]]:
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


def _tongue_similarity(a: "Agent", b: "Agent") -> float:
    matches = sum(1 for c in CONCEPTS if a.language.word_of[c] == b.language.word_of[c])
    return matches / len(CONCEPTS)


def factions(world: "World") -> list[list[str]]:
    """Cluster living beings into tribes that share a tongue (union-find)."""
    agents = list(world.agents.values())
    parent = {a.id: a.id for a in agents}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, a in enumerate(agents):
        for b in agents[i + 1:]:
            if _tongue_similarity(a, b) >= FACTION_SIMILARITY:
                parent[find(a.id)] = find(b.id)

    groups: dict[str, list[str]] = {}
    names = {a.id: a.name for a in agents}
    for a in agents:
        groups.setdefault(find(a.id), []).append(names[a.id])
    return sorted((sorted(g) for g in groups.values()), key=len, reverse=True)


def ties(world: "World", limit: int = 8) -> list[tuple[str, str, float]]:
    """The strongest ties in the world — (nameA, nameB, strength), each pair once,
    bonds positive and frictions negative, sharpest by magnitude first. The
    strength is the average of the two sides, so a one-sided tie reads weaker."""
    names = {a.id: a.name for a in world.agents.values()}
    seen: set[frozenset[str]] = set()
    out: list[tuple[str, str, float]] = []
    for a in world.agents.values():
        for oid, v in a.relationships.items():
            if oid not in world.agents:
                continue
            key = frozenset((a.id, oid))
            if key in seen:
                continue
            seen.add(key)
            strength = (v + world.agents[oid].affinity(a.id)) / 2
            if strength != 0:
                out.append((names[a.id], names[oid], strength))
    out.sort(key=lambda t: abs(t[2]), reverse=True)
    return out[:limit]


def census(world: "World") -> dict:
    living = world.agents
    n = len(living)
    gens = [a.generation for a in living.values()]
    t = world.tally
    return {
        "population": n,
        "generations": (max(gens) + 1) if gens else 0,
        "avg_age": round(sum(a.age for a in living.values()) / n, 1) if n else 0,
        "avg_vitality": round(sum(a.vitality for a in living.values()) / n, 2) if n else 0,
        "avg_bravery": round(sum(a.genome.bravery for a in living.values()) / n, 3) if n else 0,
        "births": t.get("births", 0),
        "deaths_hunger": t.get("deaths_hunger", 0),
        "deaths_age": t.get("deaths_age", 0),
        "deaths_forage": t.get("deaths_forage", 0),
        "deaths_predator": t.get("deaths_predator", 0),
        "deaths_violence": t.get("deaths_violence", 0),
        "gifts": t.get("gifts", 0),
        "seizures": t.get("seizures", 0),
        "matings": t.get("matings", 0),
        "harvests": t.get("harvests", 0),
        "crop_failures": t.get("crop_failures", 0),
    }


def _total_deaths(c: dict) -> int:
    return (c["deaths_hunger"] + c["deaths_age"] + c["deaths_forage"]
            + c["deaths_predator"] + c["deaths_violence"])


def snapshot(world: "World") -> dict:
    frac, edges, total = coverage(world)
    c = census(world)
    return {"tick": world.tick, "coverage": round(frac, 4),
            "population": c["population"], "generations": c["generations"],
            "avg_bravery": c["avg_bravery"], "births": c["births"],
            "deaths": _total_deaths(c)}


def _notable(world: "World", limit: int = 14) -> list[str]:
    keys = ("born", "died", "was lost", "was killed", "the beast", "learned",
            "seized", "gave bloom", "expecting", "driven off")
    hits = [line for line in world.feed if any(k in line for k in keys)]
    return hits[-limit:]


def chronicle(world: "World") -> str:
    c = census(world)
    frac, edges, total = coverage(world)
    lines: list[str] = []
    lines.append(f"═══ Loam — day {world.day}, {world.phase()} (tick {world.tick}) ═══")
    if c["population"] == 0:
        lines.append("The world is empty. Every being has died.")
        return "\n".join(lines)

    lines.append(f"{c['population']} beings alive across {c['generations']} generation(s); "
                 f"average age {c['avg_age']}, average vitality {c['avg_vitality']}.")

    # the courage of the people, and how it has moved
    born_brave = world.history[0]["avg_bravery"] if world.history and "avg_bravery" in world.history[0] else None
    drift = ""
    if born_brave is not None:
        d = c["avg_bravery"] - born_brave
        way = "steadied" if abs(d) < 0.02 else ("grown bolder" if d > 0 else "grown warier")
        drift = f" — {way} from {born_brave:.2f} at the start"
    lines.append(f"The courage of the people is {c['avg_bravery']:.2f}{drift}. The beast prowls {world.predator}.")
    lines.append("")

    lines.append("The toll so far:")
    lines.append(f"  born: {c['births']}   |   died — hunger {c['deaths_hunger']}, age {c['deaths_age']}, "
                 f"the wild {c['deaths_forage']}, the beast {c['deaths_predator']}, violence {c['deaths_violence']}")
    lines.append(f"  matings {c['matings']}, harvests {c['harvests']}, "
                 f"crop failures {c['crop_failures']}")
    lines.append("")

    give, take = c["gifts"], c["seizures"]
    if give or take:
        temper = ("mostly giving" if give > take * 2 else
                  "mostly taking" if take > give * 2 else "torn between giving and taking")
        lines.append(f"The economy of bloom is {temper} — {give} gifts, {take} seizures.")
        lines.append("")

    tied = ties(world, 6)
    if tied:
        lines.append("The ties that bind:")
        for na, nb, s in tied:
            lines.append(f"  {na} & {nb}: {s:+.0f} ({'bond' if s > 0 else 'friction'})")
        lines.append("")

    tribes = factions(world)
    if len(tribes) == 1:
        lines.append(f"They are one people by tongue ({len(tribes[0])} share a language).")
    else:
        sizes = ", ".join(str(len(t)) for t in tribes)
        lines.append(f"They have split into {len(tribes)} tongues (sizes: {sizes}).")
        for t in tribes[:4]:
            lines.append(f"  · {', '.join(t)}")
    lines.append("")

    _now, change, way = tongue_trend(world)
    move = "" if way in ("still forming", "holding steady") else f", and {way} ({change * 100:+.0f}% lately)"
    lines.append(f"A shared tongue is {frac * 100:.0f}% formed "
                 f"({edges} of {total} understanding-links live){move or ', ' + way}.")
    from .rifts import families
    cohesion = [(f, *family_cohesion(world, f)) for f in families(world)]
    cohesion = [(f, coh, n) for f, coh, n in cohesion if n > 1]
    if cohesion:
        cohesion.sort(key=lambda r: -r[1])
        best, worst = cohesion[0], cohesion[-1]
        lines.append(f"  within families: the {best[0]} understand each other best "
                     f"({best[1] * 100:.0f}%); the {worst[0]} least ({worst[1] * 100:.0f}%).")
    spread = word_spread(world)
    if spread:
        lines.append("Words that have spread:")
        for word, concept, owner, count in spread[:5]:
            lines.append(f'  "{word}" (= {concept}, first {owner}\'s) — known by {count} other(s)')
    lines.append("")

    moments = _notable(world)
    if moments:
        lines.append("Moments worth remembering:")
        lines.extend(f"  {m}" for m in moments)
        lines.append("")

    s = player_summary(world)
    if s["understood"] or s["trades"] or s["closest"]:
        lines.append("Your story so far:")
        lines.append(f"  you understand {s['understood']}/{s['families']} families "
                     f"({s['words_earned']} words earned)"
                     + (f"; you ply " + ", ".join(f"{t} ({int(v * 100)}%)" for t, v in s["trades"][:3])
                        if s["trades"] else ""))
        if s["closest"]:
            lines.append("  closest to: " + ", ".join(f"{n} ({tier})" for n, tier in s["closest"]))
        if s["spouse"]:
            kids = f", raising {', '.join(s['children'])}" if s["children"] else ""
            lines.append(f"  wed to {s['spouse']}{kids}")
        lines.append("")

    lines.append("The world is still turning. Come tend it.")
    return "\n".join(lines)
