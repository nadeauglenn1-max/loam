# Loam

*A living world of AI beings you tend and inhabit — not a god, the one who understands.*

Loam is a small, persistent world of AI beings who must **survive, age, die, and
breed** — and who speak **private languages they inherit and drift**. They wake
with wants and with hunger; they gather food from a dangerous land; they bond,
share, steal, mourn, and pass their tongues and their gifts to their children.

We do not script culture. We build **pressure** — need, risk, death, kinship —
and watch what precipitates: tribes, trade, violence, belief. See
[docs/DESIGN.md](docs/DESIGN.md) for the full design and what we're watching for.

You are the one who understands every tongue — a translator each being can turn
to, individually and horizontally. No worship, no hierarchy. Understanding isn't
authority; it's the ability to help.

---

## Try it

Runs with **zero dependencies** — the default cognition is free and offline.

```bash
python -m loam.cli reset --agents 8      # begin a world
python -m loam.cli run --ticks 300       # let it live
python -m loam.cli chronicle             # births, deaths, tribes, tongue, the economy of bloom
python -m loam.cli census                # the numbers
python -m loam.cli map                   # places, danger, bloom, who is where
python -m loam.cli visit a3              # sit with one being — its body, gifts, kin, thoughts
python -m loam.cli translate kalo a5     # help a5 understand the word "kalo"
```

The world persists to `runtime/world.json` and **accumulates across runs**.

### Bases & playthroughs

A world can be minted as an **immutable base** — a reusable template — and every
play **forks** a fresh copy from it. A run only ever writes the playthrough; the
base is *never* overwritten, so "it worked last time" can always begin again from
the same pristine ground (and the same base is a thing you can share).

```bash
python -m loam.cli genesis eden --agents 8   # mint a base → worlds/eden.base.json
python -m loam.cli play eden --ticks 50      # fork & live a playthrough (base stays pristine)
python -m loam.cli play eden --ticks 50      # resume it; --fresh restarts from the base
python -m loam.cli worlds                    # the bases you can play
```

Bases live in `worlds/` (committed — they're shareable content); playthroughs
live in `runtime/` (local, disposable).

### Characters

Save a being you love out of any world and drop it into another. A saved
character keeps its **self** — its genome and its private tongue — but *not* its
playthrough state, so it arrives in the new village a stranger and is woven into
a fresh web: **same soul, new entanglements.**

```bash
python -m loam.cli save-char Fen --from eden          # → chars/fen.char.json
python -m loam.cli genesis two --with fen --agents 8  # compose a base that includes Fen
python -m loam.cli chars                               # the characters you've saved
```

### Live cognition

By default, beings decide by a legible survival-first rule policy. With `--real`,
a live Claude actually reasons about whether to farm or forage, share or seize,
breed or flee:

```bash
pip install -e ".[real]"
export ANTHROPIC_API_KEY=...
python -m loam.cli run --ticks 40 --real
```

## The world

- **A woven village**: a world doesn't wake as strangers. Its founders begin
  already **tangled** — old friends and kin, a debt of kindness owed, a rivalry
  unsettled, a wrong unforgiven. These are real bonds and frictions (each with a
  founding memory), and cognition **reads them from the first tick**, so a being
  feeds its friends, breeds with those it trusts, and preys on those it resents
  from the very start. The web is deterministic in the world's seed. (A web is a
  property of a village; a pair or trio wakes a clean slate.)
- **Bloom** is the resource beings must eat or their vitality decays to death.
  **Forage** it from the wild — rich but **dangerous** (injury, death). **Grow**
  it on arable land — safe but **uncertain** (crops fail, and no one is told
  why: the soil is exhausted, or luck turned). Foraging and growing draw from the
  same finite, regrowing land, so crowding starves a place — and the world finds
  a carrying capacity on its own.
- **Life**: beings age and die of hunger, the wild, violence, or old age. Skills
  (foraging, growing), appetites, lifespan, and **courage** are all **heritable**.
- **The beast**: a predator roams every place that holds food, deadly to a lone
  forager but survivable by a group. It prunes the reckless; hunger prunes the
  timid. With no free refuge, **courage evolves to a calibrated middle** — brave
  enough to eat, wary enough to live (a run of ~1800 free ticks shows bravery
  settling and holding its variance instead of collapsing).
- **Procreation**: two thriving, bonded, co-located beings conceive; after
  gestation a child is born, inheriting a blend of its parents — which it *may or
  may not* follow — and a **drifted copy of a parent's tongue**. So lineages
  become dialect-tribes, and kin understand each other natively.
- **Free action**: beings move, forage, grow, eat, **give**, **seize**, speak,
  **mate**, rest, or turn to you. Whether a hungry being shares or takes is its
  own choice — which is how economy and violence *emerge* rather than being coded.

## The attention / compute economy

Cheap cognition keeps the world alive; expensive cognition is spent only where it
counts (single-sourced in `loam/config.py`):

| tier | model | when |
|------|-------|------|
| routine | `claude-haiku-4-5` | an ordinary tick |
| reflective | `claude-sonnet-5` | you're present |
| pivotal | `claude-opus-4-8` | you're present, or a being is old or dying |

## Architecture

The world owns *consequences*; cognition owns *choices*; the genome and the
tongue own what is *inherited*.

```
config.py      model tiers, the map, and every balance constant (one source of truth)
genome.py      the heritable core: appetites, skills, lifespan — genesis and inheritance
language.py    private + inherited tongues, learned lexicons, utterances
wants.py       heterogeneous, evolving desire (appetites come from the genome)
memory.py      per-being bounded memory
agent.py       a being: body (vitality/age/bloom), tongue, wants, kin, pregnancy
genesis.py     the web a village is born into — bonds and frictions before tick one
character.py   a being's portable base self — saved to drop into another world
cognition.py   Decision + RuleCognition (free/default/fallback) + ClaudeCognition (live)
llm.py         the only place that touches the network
world.py       the tick loop: ecology, life, death, birth, speech, and your levers
metrics.py     census, lineage tribes, the economy — and the chronicle
persistence.py JSON save/load; an immutable base forked into a mutable playthrough
cli.py         run / chronicle / census / map / visit / genesis / play / save-char / chars
```

## Develop

```bash
pip install -e ".[dev]"
pytest --cov=loam --cov-fail-under=90
```

Clean-room project. Proprietary; all rights reserved (see LICENSE).
