"""The founding village — an authored cast of thirty, decided before tick one.

Where a plain genesis wakes strangers, this is a *hand-authored* founding: thirty
named souls in six families and cross-cutting groups, each with a nature and a
backstory, tangled in a web written on purpose — kin bonds, group loyalties, and
a handful of sharp cross-family bonds and grudges (an estrangement, an unpaid
debt, a hero-worship, a water dispute). It is the world you walk into first.

Cost note: this is one-shot genesis (free); the world then loops on the free rule
cognition — the paid model is spent only when the player interacts.
"""
from __future__ import annotations

from itertools import combinations

from . import config
from .agent import Agent, cls_initial_age
from .config import CONCEPTS, STARTING_PLACE
from .genome import Genome
from .language import Lexicon, PrivateLanguage
from .memory import Memory
from .wants import Wants
from .world import World

# name, family, group, forage, grow, bravery, wants, story
FOUNDERS: list[tuple] = [
    # ---- Vane — the old farming family that holds the fields --------------------
    ("Doran", "Vane", "council", .30, .90, .35, ("safety", "status"),
     "the hollow's stubborn farmer; he feeds half the village and forgives almost no one"),
    ("Mara", "Vane", "hearth", .40, .82, .45, ("trust", "company"),
     "keeps the village's memory and its herb-lore; she buried her partner in the thornwood years ago"),
    ("Bex", "Vane", "hearth", .50, .60, .40, ("company", "trust"),
     "an orphan the Vanes took in; she belongs to the whole village and to no one"),
    ("Elin", "Vane", "", .55, .55, .58, ("novelty", "status"),
     "Doran's daughter, restless in the fields and hungry for a wider life"),
    ("Corin", "Vane", "foragers", .60, .45, .62, ("novelty", "company"),
     "Doran's young son, who worships Sela and wants the deep woods"),
    # ---- Ashmol — traders and craftsfolk, fractured ----------------------------
    ("Ivo", "Ashmol", "council", .55, .50, .50, ("status", "company"),
     "a smooth-tongued trader who owes small debts all over the village"),
    ("Pell", "Ashmol", "", .45, .60, .50, ("safety", "trust"),
     "Ivo's steadier brother, forever cleaning up after him"),
    ("Odile", "Ashmol", "hearth", .40, .76, .40, ("rest", "trust"),
     "the village weaver, quiet and exact, estranged from her family by an old wrong"),
    ("Wren", "Ashmol", "", .50, .55, .48, ("company", "trust"),
     "Odile's daughter, caught between her mother's silence and her uncle Ivo's charm"),
    ("Sable", "Ashmol", "council", .35, .45, .32, ("status", "rest"),
     "the Ashmol elder, who keeps the family's ledgers and its grudges"),
    # ---- Thorn — the foragers of the deep wood ---------------------------------
    ("Sela", "Thorn", "foragers", .90, .30, .92, ("novelty", "status"),
     "the boldest forager in the hollow; she goes deepest since her sister was lost to the wild"),
    ("Vesna", "Thorn", "council", .60, .45, .50, ("safety", "trust"),
     "the Thorn matriarch, who has buried too many of her own"),
    ("Kael", "Thorn", "foragers", .82, .35, .80, ("novelty", "status"),
     "Sela's cousin, who follows her into the dark without question"),
    ("Dax", "Thorn", "foragers", .75, .30, .86, ("novelty", "status"),
     "the youngest forager, eager and reckless"),
    ("Ren", "Thorn", "foragers", .70, .40, .60, ("novelty", "company"),
     "a wanderer from the east who took the Thorn name when Sela vouched for him"),
    # ---- Bly — the hearth-guard household ---------------------------------------
    ("Tam", "Bly", "hearth", .60, .40, .86, ("safety", "trust"),
     "the hearth's watchman, brave to a fault; he has never forgiven himself for a night he was too slow"),
    ("Rook", "Bly", "", .55, .40, .70, ("status", "safety"),
     "Tam's apprentice, desperate to prove himself"),
    ("Nessa", "Bly", "hearth", .45, .60, .40, ("company", "rest"),
     "Tam's wife, who keeps the hearth-fire and the village's fragile peace"),
    ("Bram", "Bly", "", .50, .50, .50, ("rest", "trust"),
     "Tam's quieter brother, who privately doubts the guard is worth the fear it trades in"),
    # ---- Fen — the marsh folk, who keep to themselves --------------------------
    ("Odo", "Fen", "", .60, .50, .45, ("safety", "rest"),
     "reads the water and the weather better than anyone"),
    ("Lys", "Fen", "hearth", .45, .60, .40, ("trust", "company"),
     "Odo's partner and a healer of small hurts"),
    ("Miri", "Fen", "", .60, .45, .55, ("novelty", "company"),
     "their daughter, curious about the dryland families"),
    ("Tolan", "Fen", "council", .45, .55, .40, ("status", "safety"),
     "the Fen elder, who distrusts the Vane hold on the fields and the water"),
    ("Senna", "Fen", "", .50, .55, .42, ("rest", "trust"),
     "quiet, and the only Fen who trades openly with Odile"),
    # ---- Unbound — drifters and loners, no family ------------------------------
    ("Yara", "", "foragers", .70, .40, .60, ("novelty", "rest"),
     "came alone, owes nothing to anyone, and likes it that way"),
    ("Cass", "", "", .50, .50, .45, ("rest", "trust"),
     "a loner who talks to no one but Bex"),
    ("Juno", "", "", .55, .50, .50, ("status", "novelty"),
     "an old wanderer who remembers a dozen other villages"),
    ("Pike", "", "", .60, .45, .50, ("status", "company"),
     "sharp-eyed, and sells rumors as readily as bloom"),
    ("Goss", "", "", .50, .50, .45, ("status", "company"),
     "trades in secrets; everyone is a little wary of what they know"),
    ("Wisp", "", "", .55, .50, .52, ("novelty", "rest"),
     "barely speaks, and no one is sure where they came from"),
]

# sharp cross-cutting ties, applied last (they OVERWRITE kin/group warmth) —
# name, name, kind, strength 1-9, reason
TIES: list[tuple[str, str, str, int, str]] = [
    ("Ivo", "Odile", "friction", 8, "the old betrayal Odile never forgave and Ivo pretends to have forgotten"),
    ("Ivo", "Doran", "friction", 6, "a debt Ivo still owes, that Doran has stopped expecting back"),
    ("Tolan", "Doran", "friction", 6, "the long dispute over the fields and the water"),
    ("Tam", "Sela", "friction", 5, "he thinks her recklessness will get someone killed; she thinks him a coward"),
    ("Rook", "Dax", "friction", 5, "a young rivalry, forager against guard"),
    ("Pike", "Goss", "friction", 6, "rival rumor-mongers who each know too much about the other"),
    ("Mara", "Odile", "bond", 7, "old friends who keep each other's oldest secrets"),
    ("Mara", "Vesna", "bond", 6, "two women who have buried too many of their own"),
    ("Bex", "Cass", "bond", 7, "the only person Cass will speak to"),
    ("Bex", "Wren", "bond", 6, "the two girls caught between their families"),
    ("Corin", "Sela", "bond", 6, "hero-worship, from the boy who wants the deep woods"),
    ("Elin", "Ren", "bond", 6, "she wants the wandering life he left behind"),
    ("Juno", "Ren", "bond", 5, "two wanderers who recognize each other"),
]

# each family keeps a trade; a few souls whose story names a craft override it
FAMILY_VOCATION = {
    "Vane": "husbandry", "Ashmol": "weaving", "Thorn": "woodcutting",
    "Bly": "smithing", "Fen": "fishing", "Unbound": "cooking",
}
NAME_VOCATION = {
    "Doran": "husbandry", "Mara": "herbalism", "Ivo": "cooking", "Odile": "weaving",
    "Sela": "hunting", "Kael": "hunting", "Dax": "hunting",
    "Odo": "fishing", "Lys": "herbalism",
}


def _vocation(name: str, family: str) -> str:
    return NAME_VOCATION.get(name) or FAMILY_VOCATION.get(family or "Unbound", "cooking")


_KIN, _GROUP = (5.0, 6.5), (2.5, 3.5)   # affinity ranges for family and group bonds


def _genome(forage: float, grow: float, bravery: float, wants: tuple) -> Genome:
    appetites = {c: (0.9 if c in wants else 0.2) for c in CONCEPTS}
    return Genome(appetites=appetites, forage_skill=forage, grow_skill=grow,
                  bravery=bravery, lifespan=config.LIFESPAN_MEAN)


def _bond(a: Agent, b: Agent, lo_hi: tuple[float, float], memory: str) -> None:
    lo, hi = lo_hi
    mag = (lo + hi) / 2
    a.warm_to(b.id, mag)
    b.warm_to(a.id, mag)
    a.memory.remember(0, memory)
    b.memory.remember(0, memory)


def build_base(seed: int = 7) -> World:
    """Wake the authored founding village — thirty souls, their families, groups,
    stories, and the web of bonds and grudges written between them."""
    w = World(seed=seed)
    by_name: dict[str, Agent] = {}
    families: dict[str, list[Agent]] = {}
    groups: dict[str, list[Agent]] = {}

    for i, (name, family, group, forage, grow, bravery, wants, story) in enumerate(FOUNDERS):
        aid = f"a{i}"
        g = _genome(forage, grow, bravery, wants)
        a = Agent(id=aid, name=name, genome=g, language=PrivateLanguage.for_agent(aid),
                  lexicon=Lexicon(), wants=Wants.of(aid, g.appetites),
                  memory=Memory(agent_id=aid), location=STARTING_PLACE,
                  vitality=1.0, age=cls_initial_age(aid), story=story,
                  home=(family or "Unbound"), vocation=_vocation(name, family))
        w.agents[aid] = a
        by_name[name] = a
        if family:
            families.setdefault(family, []).append(a)
        if group:
            groups.setdefault(group, []).append(a)

    w.next_index = len(FOUNDERS)
    for place, d in config.PLACES.items():
        w.bloom[place] = d["wild"] * config.WILD_MAX_SCALE * 0.5
    w.predator = config.PREDATOR_PLACES[0]

    for fam, members in families.items():
        for a, b in combinations(members, 2):
            _bond(a, b, _KIN, f"kin — the {fam} family")
    for grp, members in groups.items():
        for a, b in combinations(members, 2):
            _bond(a, b, _GROUP, f"one of the {grp}")

    for na, nb, kind, strength, reason in TIES:
        a, b = by_name[na], by_name[nb]
        lo, hi = config.WEB_BOND_RANGE if kind == "bond" else config.WEB_TENSION_RANGE
        mag = lo + (strength / 9) * (hi - lo)
        sign = 1 if kind == "bond" else -1
        a.relationships[b.id] = sign * mag           # SET — overwrites kin/group warmth
        b.relationships[a.id] = sign * mag * 0.85
        a.memory.remember(0, reason)
        b.memory.remember(0, reason)

    w._log(f"The founding village wakes: {len(FOUNDERS)} souls across "
           f"{len(families)} families, each with a past.")
    return w
