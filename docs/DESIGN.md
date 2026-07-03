# Loam — design & roadmap

Loam began as a study of emergent *language*. It is becoming a study of emergent
*culture*: what a small society of AI beings does when it must survive, ages and
dies, and can reproduce — with everything heritable, including its tongue.

The rule of the project: **we do not code culture. We build pressure, and watch
what precipitates.** Religion, money, violence, and factions are not modules.
They are what we hope to *observe* arising from need, risk, death, kinship, and a
free space of action.

## The layers

```
   culture        beliefs (notions), exchange, alliance, conflict, faction   ← emergent, observed
   ─────────────────────────────────────────────────────────────────────
   society        language, bonds, wants (company/status/trust/novelty)      ← v0.1–0.2
   ─────────────────────────────────────────────────────────────────────
   life           vitality, hunger, aging, death, procreation, gestation     ← v0.3
   ─────────────────────────────────────────────────────────────────────
   ecology        bloom (the resource): forage (risk) / grow (uncertainty)    ← v0.3
   ─────────────────────────────────────────────────────────────────────
   world          a large map of places, each with its own danger & bounty    ← v0.3
```

The social/language layer we already built is not sidelined — it becomes the
**carrier of culture**, because language is heritable.

## The load-bearing idea: heritable language

A child is born speaking a **drifted copy of a parent's tongue** — most of the
parent's words, some mutated. Consequences cascade:

- Lineages become **dialect-tribes**. Sharing a tongue = in-group; a foreign
  tongue = out-group.
- Trust and understanding flow along **bloodlines**, cheaply; across them, only
  through the slow work of grounding or your translation.
- That asymmetry is the seed of **factions, hoarding across group lines,
  violence with a "why," and belief that binds a group**.

## The resource: bloom

Beings must eat **bloom** or their vitality decays to death. Two ways to get it:

- **Forage** — gather wild bloom from a place. Rich, immediate, and **dangerous**:
  a chance of injury or death scaled by the place's danger and lowered by the
  being's `foraging` skill.
- **Grow** — plant and tend bloom. Safe, but **uncertain**: a crop fails
  sometimes, and the being is *not told why*. It must diagnose (try again, move,
  ask, or believe). Lowered failure with the being's `growing` skill.

Bloom can be **held**, **eaten**, **given**, and **seized**. What a being does
with a surplus — share it, hoard it, trade it, or take another's by force — is a
free choice its cognition makes under pressure. Economy and violence live here.

## Life & death

- **Vitality** decays each tick (metabolism); eating bloom restores it; zero = death.
- **Age & lifespan**: beings grow old and die even if fed. Lifespan is heritable
  with variation. As a being ages or weakens, its situation says so — and its
  thoughts will carry it. Mortality is what makes procreation necessary.

## Procreation, gestation, genetics

- Two healthy, willing, co-located beings can conceive.
- **Gestation**: a pregnancy timer; birth costs the carrier vitality.
- **Genetics** (`genome.py`): a child inherits a blend of parents' **appetites
  (wants), skills, lifespan, and language**, each with mutation — so a child
  *may or may not* follow a parent's needs, talents, or tongue. Divergence is a
  feature: it's how new kinds of being, and new tribes, arise.

## Free action space (so culture emerges, not scripts)

Cognition chooses among: **move, forage, grow, tend, eat, give, seize, speak,
mate, rest, seek-you**. The interesting behaviours — sharing vs seizing, fleeing
vs fighting, breeding vs hoarding — are choices under pressure, not rules.

## What we are watching for

- **Religion** — do beings form and spread *notions* (explanations, beliefs)
  around the unexplained: failed crops, death? Do beliefs bind groups?
- **Money** — does bloom become a medium of exchange (given for favour, mating,
  protection) rather than only consumed?
- **Violence** — do they kill over resource? Along tribe lines?
- **Factions** — do dialect-lineages cluster, split, and contest?
- **Argument** — do they disagree, contest claims, reject each other's notions?

We instrument for these (census, lineages, tallies of gifts/seizures/deaths,
faction clustering by tongue) and we *read the run* — we do not hardcode the
answers.

## Roadmap

- **v0.3 (in progress)** — ecology (bloom, forage-risk, grow-uncertainty, big
  map), life (vitality, aging, death), procreation (gestation, genetics,
  heritable language), free actions (give/seize/mate), instrumentation (census,
  lineage, factions). Balance-tuned on free mock runs, then a long real run.
- **v0.4** — the notion/belief layer made first-class (transmission, adoption,
  recurrence) so proto-religion and proto-value are legible; deeper cognition
  over relationships and history.
- **later** — you *inhabit* a being (first person), not only tend from above.

## Standing principles

One source of truth (`config.py`). Complete, tested subsystems — never
half-finished. Docs ship with code. Free mock cognition is the default and the
safe fallback; live Claude cognition (`--real`) is where culture is watched.
