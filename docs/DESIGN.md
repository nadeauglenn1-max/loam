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

## The beast, and the evolution of courage (v0.4)

A predator roams the food-bearing places, deadly to a lone forager, survivable
by a group. Courage is a heritable gene. The point is not death — it is a
*selective pressure with a twin*: the beast prunes the reckless, hunger prunes
the timid. If there is a free safe refuge, timidity is never punished and
courage collapses to cowardice (the population huddles and dwindles). Remove the
free refuge, and the two pressures balance: **courage evolves to a calibrated
middle and holds its variance** — brave enough to eat, wary enough to live. This
was run and confirmed; see the README.

## The web a village is born into (v0.5)

A world does not begin as a crowd of strangers. Before the first tick, its
founders are already **tangled** — bonds and frictions with a founding memory of
each: old friends and kin, a debt of kindness owed, a rivalry unsettled, a wrong
unforgiven. This is not decoration: cognition already reads affinity (who to
feed, breed with, seize from, speak to), so the web has **mechanical teeth from
tick one** — a being feeds its friends and preys on its rivals immediately.

The weave (`genesis.py`) is **deterministic in the world's seed**, so a base
world is reproducible — a prerequisite for treating a saved world as a *reusable
base*. A web is a property of a *village*: below `WEB_MIN_VILLAGE` founders (a
pair or trio, used to isolate mechanics in tests) none is woven. Density and the
warmth/friction balance are single-sourced constants in `config.py`.

This is the first step toward **genesis as composition** — a village assembled
from saved characters plus fresh founders, with the connective web (the part
that makes a roster a society) generated over them; today rule-woven, later a
model can author richer tensions behind the same seam.

## Roadmap

- **v0.3–v0.4 (done)** — ecology (bloom, forage-risk, grow-uncertainty, big
  map), life (vitality, aging, death), procreation (gestation, genetics,
  heritable language), free actions (give/seize/mate), instrumentation (census,
  lineage, factions), and the beast (evolution of calibrated courage).
- **v0.5 (done)** — the genesis web: villages wake already bonded and in
  friction, deterministic in the seed.
- **v0.6 (done)** — the **save file as a reusable base**: `genesis` mints an
  immutable base template (`worlds/<name>.base.json`); `play` *forks* it into a
  mutable playthrough (`runtime/<name>.play.json`); a run only ever writes the
  playthrough, so the base is never overwritten — replay always begins from the
  same pristine ground. Bases are shareable content; playthroughs are disposable.
- **v0.7 (done)** — **characters as portable atoms**: `save-char` writes a
  being's *self* (genome + private tongue, not its playthrough state) to
  `chars/<name>.char.json`; `genesis --with <char>` composes a base from saved
  favourites + fresh founders, all woven into one fresh web. Same soul, new
  entanglements.
- **v0.8 (done)** — a **model-authored genesis web**: `genesis --real` lets a
  model author the ties behind the same `Weaver` seam the rule weaver fills; the
  engine consumes a *validated contract* (not raw text) and falls back to the
  rule weave on any failure — model-agnostic by construction.
- **v0.9 (done)** — multiple named playthroughs of one base (`play <base> --as
  <story>`): one base forks into many side-by-side stories, each its own file,
  the base untouched — replay-throughs by construction.
- **v0.10 (done)** — a **model-authored character**: `forge <name> "<desc>"`
  turns a prose description into a being's nature behind the same `Forge` seam
  (RuleForge default/fallback, ClaudeForge with `--real`) — a *validated genome*,
  never raw text.
- **v0.11 (done)** — **surface the web**: `metrics.ties()` powers a "ties that
  bind" section in the chronicle and a panel on the live dashboard (one helper,
  two surfaces — strongest bonds and sharpest frictions).
- **v0.12 (done)** — an **authored founding village** (`loam village`): eight
  named souls with backstories and a hand-written web of bonds and grudges, plus
  a `story` on every being — the place you walk into first, with a past.
- **v0.14 (done)** — the **explore client** (`loam explore`, pygame, in-process):
  walk the village with a player avatar, meet its people, read their story /
  thought / bonds, and watch it live around you. Code-drawn graphics; the world
  loops on free cognition, the model is untouched here (spent only on interaction).
- **v0.15 (done)** — a **day-clock**: a day is a set 30-minute span paced in the
  explore client, with a day/night wash; a short session is a day or two, not
  generations. (Pure pacing/clock — the tuned survival balance is untouched.)
- **v0.16 (done)** — **anchors**: the areas render as a medieval village — a
  Homes quarter with a house per family, a Square (well + market), worked Fields,
  and wooded edges — with a `home` on every being and a night routine that sends
  the well-fed home after dark (so the village breathes with the day-clock).
- **v0.17 (done)** — **distinct, moving people**: bigger, individually-recognizable
  villagers (deterministic skin/hair/tunic, tunic hue shared by household) that
  walk between anchors with a leg-swinging gait and face where they go.
- **v0.18 (done)** — the **combat & leveling engine**: health is vitality (one
  bar); attack/defense are heritable genome aptitudes; level and earned xp raise
  effective power; `world.attack` resolves a blow (deterministic, free) and a
  slain foe dies and levels its slayer. Shared by villagers, monsters, and the
  player alike.
- **v0.19 (done)** — **monsters** as data-driven entities (`bestiary.py`): a
  registry of kinds (cave rat → cave troll), each carrying beings' combat
  interface; `world.strike` resolves any fight and `world.spawn_monster` places
  them. A new monster is a data row.
- **v0.20 (done)** — **data-driven zones** (`zones.py`): a zone is a named area, a
  danger, and a spawn table. Overlay zones cover the wild map and inherit its
  danger (one source of truth); standalone caves and dungeons carry their own.
  `world.populate_zone` rolls a table into live monsters; the moddable contract
  is that a zone may only spawn kinds the bestiary knows. "Build a cave or a
  dungeon" is adding a data row — see `loam zones`. (Note: the ecology predator in
  `_forage` — the tuned pressure that evolves courage — is left intact; "the
  beast" appears in the deepwood zone's spawn table as the same creature seen as a
  combat entity. The two are unified when the player can *enter* a zone and the
  abstract forage-roll is replaced by a real fight — the next brick.)
- **v0.21 (done)** — **professions & goods** (`crafts.py`): the working economy as
  data. A profession is a recipe — a hand's `craft_skill`, at a place, turning
  inputs into goods, at some risk (`world.do_craft`). Fishing/mining/hunting/
  husbandry/woodcutting gather; smelting/smithing/toolmaking/tanning/armoring/
  weaving/cooking refine. Goods equip: a wielded weapon raises `combat_attack`,
  armor raises `combat_defense`, a tool sharpens a gather — so the economy feeds
  the combat pillar. It rides *beside* the survival ecology (bloom/hunger), never
  through it, so the tuned balance is untouched. Adding a trade is a data row —
  see `loam crafts`.
- **v0.22 (done)** — the trades given a place in the *living* village. Every
  soul has a `vocation` (authored for the founding cast, honouring their stories;
  a gather trade for the plain-born; inherited by children — a heritable working
  culture). A well-fed villager, once survival is secured, turns to their trade
  (a new `work` decision → `world.do_craft`). Balance-guarded: a villager only
  *travels* to safe ground to work, and only the safe trades auto-fire — the
  perilous gathers (mining, hunting) are the player's to brave, and crafting is
  immune to the forage-predator. Verified across seeds: the equilibrium holds
  within normal variance while the village visibly fishes, herds, and gathers.
- **next** — player combat in the client (enter a zone, fight, level, loot; where
  the action-vs-turn feel is chosen, and where the ecology beast and the combat
  beast finally merge); trade/sharing of goods between beings (so the craft
  chains flow without the player); a "converse" beat. (Saving a newborn you like
  is already covered by `save-char`.)
- **later** — a bigger overarching story as the drive; language may retire from
  the engine (a common tongue); you *inhabit* a being (first person).

## Standing principles

One source of truth (`config.py`). Complete, tested subsystems — never
half-finished. Docs ship with code. Free mock cognition is the default and the
safe fallback; live Claude cognition (`--real`) is where culture is watched.
