# Loam

*A living world of AI agents you tend and inhabit — not a god, the one who understands.*

Loam is a small, persistent society of AI beings. Each is born speaking a
**private language** only it (and you) can read. They wake with **wants** that
shift over time, move through a small **geography** to meet those wants, and try
to reach each other across the barrier of their separate tongues.

Understanding is never free. A being learns another's word only by **hearing it
where its meaning is visible** — food-words at the spring, trust-words at the
commons — or when **you translate it for them**. Out of that friction, a history
accumulates that no one scripted: friendships, misunderstandings, dialects, and
the slow formation of a shared tongue.

You are not above them. You are the one who understands every language — a
translator and confidant each being can turn to, individually and horizontally.
No worship, no hierarchy. Understanding isn't authority; it's the ability to
help.

---

## Try it

Runs with **zero dependencies** — the default cognition is free and offline.

```bash
python -m loam.cli reset --agents 5      # begin a world
python -m loam.cli run --ticks 100       # let it live
python -m loam.cli chronicle             # is a shared tongue forming?
python -m loam.cli map                   # where is everyone?
python -m loam.cli visit a2              # sit with one being
python -m loam.cli translate kalo a3     # help a3 understand the word "kalo"
```

The world persists to `runtime/world.json` and **accumulates across runs** — you
can close the laptop and come back to a changed society.

### Live cognition

By default, beings decide by a legible rule policy. With `--real`, a live Claude
actually reasons about where to go and who to reach:

```bash
pip install -e ".[real]"
export ANTHROPIC_API_KEY=...             # or LOAM_ANTHROPIC_API_KEY
python -m loam.cli run --ticks 50 --real
python -m loam.cli run --ticks 5 --real --present   # you're here → higher tiers
```

## The two things that make it work

- **Wants are the engine.** Heterogeneous and evolving — satisfy one and a new
  one rises. Freedom without pressure is a chatroom; wants are the pressure.
- **Language is the scarce resource.** Because meaning must be *earned*, every
  alliance and betrayal has to pass through the work of being understood. The
  abstract words (trust, company) are hardest to ground alone — which is exactly
  where your help matters most.

## The attention / compute economy

Cheap cognition keeps the world alive 24/7; expensive cognition is spent only
where it counts (single-sourced in `loam/config.py`):

| tier | model | when |
|------|-------|------|
| routine | `claude-haiku-4-5` | an ordinary tick, no one watching |
| reflective | `claude-sonnet-5` | you're present |
| pivotal | `claude-opus-4-8` | you're present and the moment is rare |

## Architecture

One seam per concern; the world owns *consequences*, cognition owns *choices*.

```
config.py      model tiers, geography, constants (single source of truth)
language.py    private languages, learned lexicons, utterances
wants.py       heterogeneous, evolving desire
memory.py      per-being bounded memory
agent.py       a being: tongue, want, memory, location, relationships
cognition.py   Decision + RuleCognition (free/default/fallback) + ClaudeCognition (live)
llm.py         the only place that touches the network
world.py       the tick loop, grounded learning, and your levers (translate/visit)
metrics.py     is a common tongue forming? + the chronicle
persistence.py JSON save/load — the world that accumulates
cli.py         run / watch / chronicle / map / visit / translate / reset
```

## Develop

```bash
pip install -e ".[dev]"
pytest --cov=loam --cov-fail-under=90
```

Clean-room project. Proprietary; all rights reserved.
