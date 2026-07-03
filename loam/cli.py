"""Loam's command line — how you tend and inhabit the world.

  loam run --ticks 50            # let it live (rule cognition, free)
  loam run --ticks 20 --real     # live Claude cognition (needs a key)
  loam serve                     # watch the world live in a browser
  loam chronicle                 # the report: births, deaths, tribes, tongue
  loam census                    # the numbers at a glance
  loam map                       # places, danger, bloom, who is where
  loam watch                     # what you'd have noticed lately
  loam visit a3                  # sit with one being
  loam translate kalo a5         # help a5 understand the word "kalo"
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
    c = metrics.census(w)
    print(f"— {args.ticks} ticks lived ({mind} cognition; now t{w.tick}) —")
    for line in tail[-18:]:
        print(line)
    frac, edges, total = metrics.coverage(w)
    print(f"— {c['population']} alive, gen {c['generations']}, "
          f"{c['births']} born, {c['deaths_hunger'] + c['deaths_age'] + c['deaths_forage'] + c['deaths_violence']} dead"
          f"; shared tongue {frac * 100:.0f}% —")
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


def cmd_census(args: argparse.Namespace) -> int:
    w = _require_world()
    if w is None:
        return 1
    c = metrics.census(w)
    for k, v in c.items():
        print(f"  {k:16} {v}")
    return 0


def cmd_map(args: argparse.Namespace) -> int:
    w = _require_world()
    if w is None:
        return 1
    for place, d in PLACES.items():
        here = sorted(a.name for a in w.agents.values() if a.location == place)
        danger = ("safe" if d["danger"] < 0.1 else "risky" if d["danger"] < 0.45 else "deadly")
        stock = w.bloom.get(place, 0.0)
        who = ", ".join(here) if here else "—"
        print(f"{place:14} {danger:6} bloom {stock:5.1f}  | {who}")
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


def cmd_serve(args: argparse.Namespace) -> int:  # pragma: no cover - network loop
    from http.server import BaseHTTPRequestHandler, HTTPServer

    from . import dashboard

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            w = persistence.load()
            body = (dashboard.render_page(w, refresh=args.refresh) if w is not None
                    else "<h1>No world yet. Run: loam run</h1>")
            data = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *a) -> None:
            pass

    server = HTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Watching Loam at http://127.0.0.1:{args.port}  (refresh {args.refresh}s, Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped watching.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="loam", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="let the world live N ticks")
    r.add_argument("--ticks", type=int, default=20)
    r.add_argument("--agents", type=int, default=6, help="only used for a fresh world")
    r.add_argument("--seed", type=int, default=7)
    r.add_argument("--present", action="store_true", help="you're here; think harder")
    r.add_argument("--real", action="store_true", help="live Claude cognition")
    r.set_defaults(func=cmd_run)

    w = sub.add_parser("watch", help="recent things you'd have noticed")
    w.add_argument("--lines", type=int, default=20)
    w.set_defaults(func=cmd_watch)

    sub.add_parser("chronicle", help="the report").set_defaults(func=cmd_chronicle)
    sub.add_parser("census", help="the numbers").set_defaults(func=cmd_census)
    sub.add_parser("map", help="places, danger, bloom, who is where").set_defaults(func=cmd_map)

    v = sub.add_parser("visit", help="sit with one being")
    v.add_argument("agent")
    v.set_defaults(func=cmd_visit)

    t = sub.add_parser("translate", help="help a being understand a word")
    t.add_argument("symbol")
    t.add_argument("agent")
    t.set_defaults(func=cmd_translate)

    x = sub.add_parser("reset", help="begin a new world")
    x.add_argument("--agents", type=int, default=6)
    x.add_argument("--seed", type=int, default=7)
    x.set_defaults(func=cmd_reset)

    s = sub.add_parser("serve", help="watch the world live in a browser")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--refresh", type=int, default=3, help="seconds between auto-refreshes")
    s.set_defaults(func=cmd_serve)
    return p


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):  # pragma: no cover
            pass
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
