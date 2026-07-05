# Loam

*A living world of AI beings you explore, tend, and build your own stories in — a
moddable engine where worlds and characters are files you can fork and share.*

Loam is a small, persistent world of AI beings who **survive, age, die, and
breed**, who speak **private languages they inherit and drift**, and who wake
already **tangled in one another** — kin, friends, debts, and grudges written
before the first tick. You walk into a village with a past, watch it live, and
step in where you like.

It is built as a **platform, not just a sim**. A world is a *file* you can mint,
fork into as many separate stories as you want, and hand to someone else. A
being you love is a *file* too — save it, and drop it into a different world as a
stranger to be woven in anew. The mind that drives it all is a swappable seam:
free rule cognition by default, any model behind a validated contract when you
want one. The graphical client — walk the village in pixels — is coming next;
the engine underneath it is done.

You are the one who understands every tongue — a translator each being can turn
to, individually and horizontally. No worship, no hierarchy. Understanding isn't
authority; it's the ability to help. See [docs/DESIGN.md](docs/DESIGN.md) for the
full design.

---

## Try it

Runs with **zero dependencies** — the default cognition is free and offline.

```bash
python -m loam.cli village hollow        # mint the authored founding village (30 souls with pasts)
python -m loam.cli play hollow --ticks 200   # fork a playthrough and let it live
python -m loam.cli chronicle             # births, deaths, families, tongue, the ties that bind
python -m loam.cli visit a3              # sit with one being — its story, gifts, kin, thoughts
python -m loam.cli serve                 # watch it live in a browser (map, vitals, the web)
```

### Worlds you fork, never overwrite

A world can be minted as an **immutable base** — a reusable template — and every
play **forks** a fresh copy from it. A run only ever writes the playthrough; the
base is *never* overwritten, so "it worked last time" can always begin again from
the same pristine ground — and one base can run as many side-by-side stories as
you like.

```bash
python -m loam.cli village hollow            # the authored village, with families and grudges
python -m loam.cli genesis eden --agents 8   # or a fresh procedural base → worlds/eden.base.json
python -m loam.cli play eden --ticks 50      # fork & live a playthrough (base stays pristine)
python -m loam.cli play eden --as north      # a second, separate story from the same base
python -m loam.cli worlds                    # the bases you can play
```

Bases live in `worlds/` (committed — shareable content); playthroughs live in
`runtime/` (local, disposable).

### Characters you carry between worlds

Save a being you love out of any world and drop it into another. A saved
character keeps its **self** — its genome and its private tongue — but *not* its
playthrough state, so it arrives a stranger and is woven into a fresh web: **same
soul, new entanglements.** Or **forge** one from a description.

```bash
python -m loam.cli save-char Sela --from hollow       # → chars/sela.char.json
python -m loam.cli forge rook "a wary loner, deadly in the wild"  # author one from words
python -m loam.cli genesis two --with sela --with rook --agents 8 # compose a base from them
python -m loam.cli chars                               # the characters you've saved
```

Forging: the rule forge derives a nature from the name; with `--real` a model
authors it from your description, behind a validated contract (never raw text),
falling back to the rule forge on any failure.

## The world

- **A founding village with a past** (`loam village`): thirty named souls in six
  families (Vane, Ashmol, Thorn, Bly, Fen, and the Unbound) and cross-cutting
  groups (the council, the foragers, the hearth). Kin bond their family,
  group-mates bond mildly, and a hand-written web of sharp cross-family ties —
  an estrangement, an unpaid debt, a water dispute, a hero-worship — overwrites
  that warmth. Every being carries a **story**. (A plain `genesis` instead wakes
  a procedural village, its web rule-woven or, with `--real`, model-authored.)
- **The web has teeth from tick one.** Cognition reads affinity, so a being
  feeds its friends, breeds with those it trusts, and preys on those it resents
  from the very start.
- **Bloom** is the resource beings must eat or their vitality decays to death.
  **Forage** it from the wild — rich but **dangerous**. **Grow** it on arable
  land — safe but **uncertain**. Both draw from the same finite, regrowing land,
  so crowding starves a place and the world finds a carrying capacity on its own.
- **Life & the beast**: beings age and die of hunger, the wild, violence, or old
  age; skills, appetites, lifespan, and **courage** are heritable. A predator
  prunes the reckless while hunger prunes the timid, and with no free refuge
  **courage evolves to a calibrated middle**.
- **Procreation**: two thriving, bonded beings conceive; a child inherits a blend
  of its parents and a **drifted copy of a parent's tongue**, so lineages become
  dialect-tribes and kin understand each other natively.
- **Free action**: beings move, forage, grow, eat, **give**, **seize**, speak,
  **mate**, rest, or turn to you. Whether a hungry being shares or takes is its
  own choice — so economy and violence *emerge* rather than being coded.

## Cost: the world loops free; the model is spent on you

The standing rule is **optimize for cost**. Genesis is one-shot and cheap. The
world then **loops on the free, deterministic rule cognition** — the paid model
is spent only where it earns its keep: when the **player interacts**, and at
pivotal moments. Model choice is a swappable seam (Rule vs a live model, behind a
contract with a rule fallback), single-sourced in `loam/config.py`:

| tier | model | when |
|------|-------|------|
| routine | `claude-haiku-4-5` | an ordinary tick (usually the free rule policy) |
| reflective | `claude-sonnet-5` | you're present / interacting |
| pivotal | `claude-opus-4-8` | a decisive moment, or a being is old or dying |

## Backlog & current state

**State:** the engine + content platform is complete and CI-green (143 tests).
The graphical explore client is in progress.

**Done**
- Genesis web — villages wake tangled, with mechanical teeth from tick one.
- Save-as-base — immutable base ↔ forked playthrough; a run can't clobber it.
- Character atoms — save/forge a being's *self*; genesis by composition (`--with`).
- Model-authored web & character — behind a validated contract, rule fallback.
- Named playthroughs — one base, many side-by-side stories (replay-throughs).
- Surface the web — the ties that bind, in the chronicle and the live dashboard.
- Authored founding village — 30 souls, families, groups, and pasts.
- Explore client scaffolding — pure spatial layout (`game/layout.py`).

**In progress**
- The **explore client** (`game/explore.py`, pygame): walk the village, meet its
  people, read their story/thought/bonds, watch it live around you. The world
  loops on free cognition; the model is touched only on interaction.

**Next**
- Farming, foraging, and the beast surfaced in the client; a player avatar.
- A bigger overarching story brought in as the drive, once exploring feels right.

**Later**
- Inhabit a being (first person); richer art; mod tooling so others can author
  and share their own worlds and characters.

## Architecture

The world owns *consequences*; cognition owns *choices*; the genome and the
tongue own what is *inherited*. The sim is headless and zero-dep; presentation
(dashboard, explore client) reads world state through a decoupled seam.

```
config.py      model tiers, the map, and every balance constant (one source of truth)
genome.py      the heritable core: appetites, skills, lifespan — genesis and inheritance
language.py    private + inherited tongues, learned lexicons, utterances
wants.py       heterogeneous, evolving desire (appetites come from the genome)
memory.py      per-being bounded memory
agent.py       a being: body, tongue, wants, kin, pregnancy, and an authored story
genesis.py     the web a village is born into — bonds/frictions (rule or model weaver)
character.py   a being's portable base self — saved, forged from a description, re-dropped
cast.py        the authored founding village — thirty souls, families, groups, pasts
cognition.py   Decision + RuleCognition (free/default/fallback) + ClaudeCognition (live)
llm.py         the only place that touches the network
world.py       the tick loop: ecology, life, death, birth, speech, and your levers
metrics.py     census, lineage tribes, the economy, the ties that bind — the chronicle
persistence.py JSON save/load; an immutable base forked into a mutable playthrough
dashboard.py   a browser window into the world (loam serve)
game/          the explore client: layout.py (pure) + explore.py (the pygame loop)
cli.py         village / genesis / play / save-char / forge / chronicle / serve / explore
```

## Develop

```bash
pip install -e ".[dev]"           # sim + tests; add ".[game]" for the explore client
pytest --cov=loam --cov-fail-under=90
```

Clean-room project. Proprietary; all rights reserved (see LICENSE).
