# Loam

*A living world of AI beings you explore, tend, and build your own stories in — a
moddable engine where worlds and characters are files you can fork and share.*

Loam is a small **medieval village** of AI beings who **survive, age, die, and
breed**, and who wake already **tangled in one another** — kin, friends, debts,
and grudges written before the first tick. You walk in through a day-and-night
cycle, meet its people, read who they are, and step in where you like, while the
village lives around you on its own.

It is built as a **platform, not just a sim**. A world is a *file* you can mint,
fork into as many separate stories as you want, and hand to someone else. A being
you love is a *file* too — save it and drop it into another world as a stranger
to be woven in anew. The mind that drives it all is a swappable seam: free rule
cognition by default, any model behind a validated contract when you want one.

Walk the village in pixels (`loam explore`), tend it from the terminal, or watch
it live in the browser. See [docs/DESIGN.md](docs/DESIGN.md) for the full design.

---

## Try it

Runs with **zero dependencies** — the default cognition is free and offline.

```bash
python -m loam.cli village hollow        # mint the authored founding village (30 souls with pasts)
python -m loam.cli play hollow --ticks 200   # fork a playthrough and let it live
python -m loam.cli chronicle             # births, deaths, families, tongue, the ties that bind
python -m loam.cli visit a3              # sit with one being — its story, gifts, kin, thoughts
python -m loam.cli serve                 # watch it live in a browser (map, vitals, the web)
python -m loam.cli explore hollow        # walk the village in a window (pip install -e ".[game]")
```

## Walk the village

`loam explore hollow` opens a window and drops you into the village as a
gold-cloaked wanderer. Walk with the arrows or WASD; press **E** beside anyone to
meet them and read their story, their current thought, and who they're bonded to
or at odds with. The village lives around you: a **30-minute day** turns dawn →
dusk → night (the world washed with the changing light), people head out to the
**fields**, the **woods**, and the **square** by day, and drift **home** to their
family's house by night. Everyone is individually recognizable — skin, hair, and
a tunic in their household's colour. It runs entirely on the free rule cognition;
the model is never touched here.

Needs the game extra: `pip install -e ".[game]"`.

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
- **Village life on a day-clock.** In the explore client a day is a set span:
  people work the fields and woods and gather in the square by day, then go home
  to their family's house at night — the village breathes with the light.
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

### Using a live model (bring your own key)

Loam runs **fully free and offline** by default — the rule cognition needs no
key, no account, nothing. The optional `--real` features (a model authoring a
world's web or a character, or live per-being cognition) call the Anthropic API,
so **you bring your own key** — your key, your usage, your cost. Loam never
ships, stores, or transmits a key; it only reads one from your environment.

1. **Get a key** — sign up at [console.anthropic.com](https://console.anthropic.com),
   then create one under **API Keys**. Usage is pay-as-you-go, and the `--real`
   paths are small and infrequent by design (the world loops free; the model is
   spent only on interaction and pivotal moments).
2. **Install the extra:**
   ```bash
   pip install -e ".[real]"
   ```
3. **Put the key in your environment** — Loam reads `LOAM_ANTHROPIC_API_KEY`
   (preferred) or `ANTHROPIC_API_KEY`:
   ```bash
   # macOS / Linux
   export LOAM_ANTHROPIC_API_KEY="sk-ant-..."
   ```
   ```powershell
   # Windows PowerShell — this session:
   $env:LOAM_ANTHROPIC_API_KEY = "sk-ant-..."
   # or persist it for future sessions:
   setx LOAM_ANTHROPIC_API_KEY "sk-ant-..."
   ```
4. **Add `--real` to a command:**
   ```bash
   python -m loam.cli genesis eden --agents 8 --real    # a model authors the web
   python -m loam.cli forge rook "a wary loner" --real  # a model authors the character
   python -m loam.cli play eden --ticks 40 --real       # live per-being cognition
   ```

Keep your key in the environment — never commit it or paste it into a file.
Without a key, just omit `--real`; everything else is free. (Live per-being
cognition also falls back to the rule policy on any transient model error.)

## Backlog & current state

**State:** playable and CI-green (149 tests). The engine + content platform is
complete, and the medieval-village explore client — day/night, anchors, distinct
moving people — is in and walkable. (Saving a newborn you take a liking to is
already covered by `save-char`.)

**Done**
- Genesis web — villages wake tangled, with mechanical teeth from tick one.
- Save-as-base — immutable base ↔ forked playthrough; a run can't clobber it.
- Character atoms — save/forge a being's *self*; genesis by composition (`--with`).
- Model-authored web & character — behind a validated contract, rule fallback.
- Named playthroughs — one base, many side-by-side stories (replay-throughs).
- Surface the web — the ties that bind, in the chronicle and the live dashboard.
- Authored founding village — 30 souls, families, groups, and pasts.
- **Explore client** (`loam explore`, pygame) — walk the village with a player
  avatar, meet its people, read their story/thought/bonds, watch it live. The
  world loops on free cognition; the model is untouched here.
- **Day-clock** — a day is a set 30-minute span in the explore client, with a
  day/night wash; a short session is a day or two, not generations.
- **Anchors** — the areas render as a medieval village: a Homes quarter with a
  house per family, a Square with a well and market, worked Fields, and wooded
  edges; a night routine sends the well-fed home after dark.
- **Distinct, moving people** — bigger, individually-recognizable villagers
  (skin/hair/tunic, tunic hue shared by household) that walk between anchors with
  a leg-swinging gait and face where they go.
- **Combat & leveling engine** — stats-resolved (heritable attack vs defense,
  damage off vitality, xp and levels earned by fighting), deterministic and free,
  shared by villagers, monsters, and the player alike (`world.attack`).
- **Monsters** — data-driven entities from a registry (`bestiary.py`, cave rat →
  cave troll): each kind is a row of stats, they carry beings' combat interface,
  and `world.strike` resolves any fight (being↔being, being↔monster). A new
  monster is a new row.
- **Zones** — a dangerous area is content too (`zones.py`): a named place, a
  danger, and a spawn table. Overlay zones cover the wild map and inherit its
  danger; standalone caves and dungeons carry their own. `world.populate_zone`
  rolls a table into live monsters. **Building a cave or dungeon is adding a
  row** — see `loam zones`.
- **Professions & goods** — the working economy (`crafts.py`): fishing, mining,
  hunting, husbandry, woodcutting, smelting, smithing, toolmaking, tanning,
  armoring, weaving, cooking. **A profession is a recipe** — a hand's skill, at a
  place, turning inputs into goods, at some risk. A forged weapon sharpens combat
  and a tool sharpens a gather, so the economy feeds the combat pillar; it rides
  *beside* the tuned survival ecology, never through it. **Adding a trade is
  adding a row** — see `loam crafts`.
- **A working village** — every soul has a vocation (authored for the founding
  cast, inherited by their children), and a well-fed villager turns to their
  trade through the day. The village visibly fishes, herds, and gathers; the
  perilous trades (mining, hunting) are the player's to brave. Beings **trade
  surplus** to neighbours whose craft can use it, so the chains circulate on
  their own — a shepherd's wool reaches the weaver, who makes cloth.
- **You start knowing nothing** — the story is *becoming* the one who understands.
  You begin a novice at every trade and learn only by doing; and you understand a
  family slowly, against their distrust — a word of theirs is a prize, won by
  advancing the trade that is theirs. Fish, and the Fen come to trust you.

**Next — the combat pillar**
- **Player combat in the client** — enter a zone, fight, level, loot (this is
  where the action-vs-turn *feel* is chosen, and where the beast that haunts the
  forage becomes a foe you actually face).
- Also: make the village's everyday work playable; a "converse" beat (a model
  speaking *for* a being, on interaction only).

**Later**
- A bigger overarching story as the drive; a common tongue (language may retire
  from the engine); inhabit a being (first person); mod tooling so others author
  and share their own worlds and characters.

## Architecture

The world owns *consequences*; cognition owns *choices*; the genome and the
tongue own what is *inherited*. The sim is headless and zero-dep; presentation
(dashboard, explore client) reads world state through a decoupled seam. Within
the client, *how it looks* is a swappable subsystem too: a `Theme` owns the whole
palette, the sprites, the day/night wash and the panels, and the loop just asks
it to draw — reskin the world by writing another `Theme`, no core changes.

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
combat.py      combat & leveling — attack/defense, damage off vitality, xp/levels
bestiary.py    monsters as data-driven entities — a registry of kinds
zones.py       dangerous areas as data — named area, danger, monster spawn table
crafts.py      professions & goods as data — a trade is a recipe (skill×place→goods)
cognition.py   Decision + RuleCognition (free/default/fallback) + ClaudeCognition (live)
llm.py         the only place that touches the network
game/explore.py the explore client — the loop, input, and stepping the sim
game/theme.py  the look — a swappable graphics subsystem (palette, sprites, panels)
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
