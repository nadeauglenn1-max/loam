"""Loam's command line — how you tend and inhabit the world.

  loam run --ticks 20            # let it live 20 ticks (rule cognition, free)
  loam run --ticks 5 --present   # you're here; pivotal moments think harder
  loam run --ticks 5 --real      # live Claude cognition (needs a key)
  loam watch                     # what you'd have noticed lately
  loam chronicle                 # the morning report: is a shared tongue forming?
  loam map                       # where everyone is right now
  loam visit a2                  # sit with one being
  loam translate kalo a3         # help a3 understand the word "kalo"
  loam reset --agents 6          # begin a new world
"""
from __future__ import annotations

import argparse
import sys

from . import metrics, persistence
from .cognition import ClaudeCognition, Cognition, RuleCognition
from .config import PLACES
from .world import World


def _make_cognition(real: bool) -> Cognition:
    if not real:
        return RuleCognition()
    from .llm import LiveLLM
    return ClaudeCognition(LiveLLM(), fallback=RuleCognition())


def _load_or_make(real: bool, agents: int, seed: int) -> World:
    cognition = _make_cognition(real)
    w = persistence.load()
    if w is None:
        w = World.seeded(n_agents=agents, seed=seed)
    w.cognition = cognition
    return w


def _require_world() -> World | None:
    w = persistence.load()
    if w is None:
        print("No world yet. Try: loam run")
    return w


def cmd_run(args: argparse.Namespace) -> int:
    w = _load_or_make(args.real, args.agents, args.seed)
    w.present = args.present
    before = len(w.feed)
    w.run(args.ticks)
    persistence.save(w)
    new = w.feed[before:]
    tail = new if new else w.feed[-12:]
    mind = "live Claude" if args.real else "rule"
    print(f"— {args.ticks} ticks lived ({mind} cognition; now t{w.tick}, {len(w.agents)} beings) —")
    for line in tail[-16:]:
        print(line)
    frac, edges, total = metrics.coverage(w)
    print(f"— shared tongue: {frac * 100:.0f}% ({edges}/{total} links) —")
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    w = _require_world()
    if w is None:
        return 1
    for line in w.feed[-args.lines:]:
        print(line)
    return 0


def cmd_chronicle(args: argparse.Namespace) -> int:
    w = _require_world()
    if w is None:
        return 1
    print(metrics.chronicle(w))
    return 0


def cmd_map(args: argparse.Namespace) -> int:
    w = _require_world()
    if w is None:
        return 1
    for place, affords in PLACES.items():
        here = [a.name for a in w.agents.values() if a.location == place]
        who = ", ".join(sorted(here)) if here else "—"
        print(f"{place:14} (for {', '.join(affords)}): {who}")
    return 0


def cmd_visit(args: argparse.Namespace) -> int:
    w = _require_world()
    if w is None:
        return 1
    print(w.visit(args.agent))
    return 0


def cmd_translate(args: argparse.Namespace) -> int:
    w = _require_world()
    if w is None:
        return 1
    print(w.translate(args.symbol, args.agent))
    persistence.save(w)
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    w = World.seeded(n_agents=args.agents, seed=args.seed)
    persistence.save(w)
    print(f"A new world of {args.agents} beings begins (seed {args.seed}).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="loam", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="let the world live N ticks")
    r.add_argument("--ticks", type=int, default=10)
    r.add_argument("--agents", type=int, default=5, help="only used for a fresh world")
    r.add_argument("--seed", type=int, default=7)
    r.add_argument("--present", action="store_true", help="you're here; think harder")
    r.add_argument("--real", action="store_true", help="live Claude cognition")
    r.set_defaults(func=cmd_run)

    w = sub.add_parser("watch", help="recent things you'd have noticed")
    w.add_argument("--lines", type=int, default=20)
    w.set_defaults(func=cmd_watch)

    c = sub.add_parser("chronicle", help="the morning report")
    c.set_defaults(func=cmd_chronicle)

    m = sub.add_parser("map", help="where everyone is right now")
    m.set_defaults(func=cmd_map)

    v = sub.add_parser("visit", help="sit with one being")
    v.add_argument("agent")
    v.set_defaults(func=cmd_visit)

    t = sub.add_parser("translate", help="help a being understand a word")
    t.add_argument("symbol")
    t.add_argument("agent")
    t.set_defaults(func=cmd_translate)

    x = sub.add_parser("reset", help="begin a new world")
    x.add_argument("--agents", type=int, default=5)
    x.add_argument("--seed", type=int, default=7)
    x.set_defaults(func=cmd_reset)
    return p


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):  # pragma: no cover - non-reconfigurable stream
            pass
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
