"""Loam's command line — how you tend and inhabit the world.

  loam run --ticks 50            # let it live (rule cognition, free)
  loam run --ticks 20 --real     # live Claude cognition (needs a key)
  loam serve                     # watch the world live in a browser
  loam chronicle                 # the report: births, deaths, tribes, tongue
  loam census                    # the numbers at a glance
  loam map                       # places, danger, bloom, who is where
  loam zones                     # the dangerous areas and the monsters they spawn
  loam crafts                    # the professions and what each trade makes
  loam rifts                     # the families you have yet to understand — your progress
  loam help Sela                 # sit with a being — help them, and understand their family
  loam watch                     # what you'd have noticed lately
  loam visit a3                  # sit with one being
  loam translate kalo a5         # help a5 understand the word "kalo"
  loam reset --agents 6          # begin a new scratch world
  loam village hollow            # mint the authored founding village (people with pasts)
  loam genesis eden --agents 8   # mint a reusable base world (an immutable template)
  loam play eden --ticks 50      # fork a playthrough from it — the base stays pristine
  loam worlds                    # the bases you can play
  loam save-char Fen --from eden # save a favourite being as a portable character
  loam genesis two --with fen    # compose a base that includes a saved character
  loam chars                     # the characters you've saved
  loam forge Rook "a wary loner" # author a character from a description
  loam explore hollow            # walk the village in a window (needs the [game] extra)
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


def cmd_crafts(args: argparse.Namespace) -> int:
    from . import crafts
    print("Professions — a trade is a recipe (build one by adding a row to crafts.py):")
    for name, p in crafts.PROFESSIONS.items():
        made = ", ".join(f"{amt:g} {g}" for g, amt in p.yields.items())
        needs = ", ".join(f"{q:g} {g}" for g, q in p.inputs.items()) or "—"
        risk = "safe" if p.risk < 0.05 else "risky" if p.risk < 0.2 else "dangerous"
        print(f"  {name:12} {p.kind:7} at {'/'.join(p.places)}")
        print(f"               needs {needs}  ->  {made}   ({risk})")
    return 0


def cmd_zones(args: argparse.Namespace) -> int:
    from . import zones
    print("Zones — the dangerous places (build one by adding a row to zones.py):")
    for name in zones.list_zones():
        d = zones.danger_of(name)
        band = "safe" if d < 0.1 else "risky" if d < 0.45 else "deadly"
        table = ", ".join(f"{k} L{lo}-{hi}" for k, _w, lo, hi in zones.spawn_table(name))
        print(f"  {name:18} {zones.ZONES[name]['kind']:8} {band:6} "
              f"(danger {d:.2f})  | {table}")
    return 0


def cmd_rifts(args: argparse.Namespace) -> int:
    from . import rifts
    w = persistence.load_play(args.play) if args.play else persistence.load()
    if w is None:
        where = f"playthrough '{args.play}'" if args.play else "world"
        print(f"No {where} yet. Try:  loam play <base>")
        return 1
    frac, done, total = rifts.progress(w)
    bar_n = 24
    filled = int(frac * bar_n)
    print(f"You understand {done}/{total} families  [{'#' * filled}{'-' * (bar_n - filled)}] {frac * 100:.0f}%")
    if rifts.all_understood(w):
        print("You have become the one who understands. Every tongue is open to you.")
        return 0
    print("Rifts still open (finish the one you've begun, then the next):")
    for r in w.rifts():
        pct = int(r.level * 100)
        state = f"{pct:3d}% understood" if r.started else "  a stranger still"
        names = ", ".join(a.name for a in r.members[:5]) + ("…" if r.size > 5 else "")
        print(f"  {r.family:10} {state}  ·  {r.size} living  ·  {names}")
    return 0


def cmd_visit(args: argparse.Namespace) -> int:
    w = _require_world()
    if w is None:
        return 1
    print(w.visit(args.agent))
    return 0


def cmd_help_being(args: argparse.Namespace) -> int:
    from . import rifts
    w = persistence.load_play(args.play) if args.play else persistence.load()
    if w is None:
        print("No world yet. Try:  loam play <base>")
        return 1
    being = _find_being(w, args.being)
    if being is None:
        print(f"No being '{args.being}' there. Try:  loam rifts")
        return 1
    r = w.aid(being.id)
    if not r["ok"]:
        print(r.get("reason", "could not help"))
        return 1
    print(f"You sat with {being.name} of {r['family']}. "
          f"You understand the {r['family']} now {int(r['level'] * 100)}%.")
    if r["brokered"]:
        b = r["brokered"]
        print(f"  You helped them speak: '{b['word']}' = {b['concept']}.")
    if r["closed"]:
        print(f"  You have come to understand the {r['family']} completely — a rift closed.")
    frac, done, total = rifts.progress(w)
    print(f"  ({done}/{total} families understood, {frac * 100:.0f}%)")
    if args.play:
        persistence.save_play(w)
    else:
        persistence.save(w)
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


def cmd_genesis(args: argparse.Namespace) -> int:
    imported = []
    for cname in args.with_chars:
        atom = persistence.load_char(cname)
        if atom is None:
            print(f"No saved character '{cname}'. See:  loam chars")
            return 1
        imported.append(atom)
    weaver = None
    if args.real:
        from .genesis import ClaudeWeaver
        from .llm import LiveLLM
        weaver = ClaudeWeaver(LiveLLM())
    w = World.seeded(n_agents=args.agents, seed=args.seed, imported=imported, weaver=weaver)
    try:
        p = persistence.create_base(args.name, w, overwrite=args.force)
    except FileExistsError as e:
        print(str(e))
        return 1
    print(f"Base '{args.name}' minted — {len(w.agents)} beings, seed {args.seed} → {p}")
    for line in w.feed:
        print(f"  {line}")
    print(f"Fork a playthrough from it:  loam play {args.name}")
    return 0


def cmd_play(args: argparse.Namespace) -> int:
    cognition = _make_cognition(args.real)
    play_name = args.as_ or args.name
    world = None if args.fresh else persistence.load_play(play_name, model=cognition)
    if world is not None:
        origin = "resumed"
    else:
        try:
            world = persistence.fork(args.name, model=cognition, as_play=play_name)
        except FileNotFoundError as e:
            print(str(e))
            print(f"Mint one first:  loam genesis {args.name}")
            return 1
        origin = f"forked fresh from base '{args.name}'"
    world.present = args.present
    before = len(world.feed)
    world.run(args.ticks)
    persistence.save_play(world)
    new = world.feed[before:]
    tail = new if new else world.feed[-12:]
    mind = "live Claude" if args.real else "rule"
    c = metrics.census(world)
    frac, _edges, _total = metrics.coverage(world)
    print(f"— playthrough '{play_name}' {origin} ({mind} cognition; now t{world.tick}) —")
    for line in tail[-18:]:
        print(line)
    print(f"— {c['population']} alive, gen {c['generations']}; shared tongue "
          f"{frac * 100:.0f}% — the base '{args.name}' is untouched —")
    return 0


def cmd_worlds(args: argparse.Namespace) -> int:
    bases = persistence.list_bases()
    if not bases:
        print("No bases yet. Mint one:  loam genesis <name>")
        return 0
    print("Bases you can play:")
    for name in bases:
        note = "  (playthrough in progress)" if persistence.play_path(name).exists() else ""
        print(f"  {name}{note}")
    return 0


def _find_being(w: World, key: str):
    if key in w.agents:
        return w.agents[key]
    for a in w.agents.values():
        if a.name.lower() == key.lower():
            return a
    return None


def cmd_save_char(args: argparse.Namespace) -> int:
    w = persistence.load_play(args.frm) if args.frm else persistence.load()
    if w is None:
        where = f"playthrough '{args.frm}'" if args.frm else "scratch world"
        print(f"No {where} to save from.")
        return 1
    being = _find_being(w, args.being)
    if being is None:
        print(f"No being '{args.being}' there. Try:  loam visit <id>")
        return 1
    name = args.as_ or being.name.lower()
    p = persistence.save_char(name, being)
    print(f"Saved {being.name} as character '{name}' → {p}")
    return 0


def cmd_chars(args: argparse.Namespace) -> int:
    names = persistence.list_chars()
    if not names:
        print("No saved characters yet. Save one:  loam save-char <being> [--from <play>]")
        return 0
    print("Saved characters:")
    for n in names:
        print(f"  {n}")
    return 0


def cmd_village(args: argparse.Namespace) -> int:
    from . import cast
    w = cast.build_base(seed=args.seed)
    try:
        p = persistence.create_base(args.name, w, overwrite=args.force)
    except FileExistsError as e:
        print(str(e))
        return 1
    print(f"The founding village '{args.name}' is set — {len(w.agents)} souls "
          f"with histories → {p}")
    for a in w.agents.values():
        print(f"  {a.name} — {a.story}")
    print(f"Fork a playthrough and live it:  loam play {args.name}")
    return 0


def cmd_forge(args: argparse.Namespace) -> int:
    if args.real:
        from .character import ClaudeForge
        from .llm import LiveLLM
        forge = ClaudeForge(LiveLLM())
        mind = "a live model"
    else:
        from .character import RuleForge
        forge = RuleForge()
        mind = "the rule forge"
    atom = forge.forge(args.name, args.description)
    p = persistence.write_char(args.name, atom)
    g = atom["genome"]
    craves = ", ".join(sorted(g["appetites"], key=g["appetites"].get, reverse=True)[:2])
    print(f"Forged '{args.name}' with {mind} → {p}")
    print(f"  forage {g['forage_skill']:.2f}, grow {g['grow_skill']:.2f}, "
          f"bravery {g['bravery']:.2f}, lifespan {g['lifespan']}; craves {craves}")
    print(f"Drop into a world:  loam genesis <base> --with {args.name}")
    return 0


def cmd_explore(args: argparse.Namespace) -> int:  # pragma: no cover - interactive window
    try:
        from .game import explore
    except ImportError:
        print('The explore client needs pygame.  Install it:  pip install -e ".[game]"')
        return 1
    try:
        return explore.run(args.name, fresh=args.fresh)
    except FileNotFoundError as e:
        print(str(e))
        print(f"Mint one first:  loam village {args.name}")
        return 1


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
    sub.add_parser("zones", help="the dangerous areas and what they spawn").set_defaults(func=cmd_zones)
    sub.add_parser("crafts", help="the professions and what each one makes").set_defaults(func=cmd_crafts)

    rf = sub.add_parser("rifts", help="the families you have yet to understand — your progress")
    rf.add_argument("play", nargs="?", help="a playthrough to read (default: the scratch world)")
    rf.set_defaults(func=cmd_rifts)

    v = sub.add_parser("visit", help="sit with one being")
    v.add_argument("agent")
    v.set_defaults(func=cmd_visit)

    hb = sub.add_parser("help", help="sit with a family member — help them, and come to understand their family")
    hb.add_argument("being", help="a being's id or name")
    hb.add_argument("play", nargs="?", help="a playthrough (default: the scratch world)")
    hb.set_defaults(func=cmd_help_being)

    t = sub.add_parser("translate", help="help a being understand a word")
    t.add_argument("symbol")
    t.add_argument("agent")
    t.set_defaults(func=cmd_translate)

    x = sub.add_parser("reset", help="begin a new scratch world")
    x.add_argument("--agents", type=int, default=6)
    x.add_argument("--seed", type=int, default=7)
    x.set_defaults(func=cmd_reset)

    vl = sub.add_parser("village", help="mint the authored founding village (people with pasts)")
    vl.add_argument("name")
    vl.add_argument("--seed", type=int, default=7)
    vl.add_argument("--force", action="store_true", help="replace an existing base")
    vl.set_defaults(func=cmd_village)

    g = sub.add_parser("genesis", help="mint an immutable base world (a reusable template)")
    g.add_argument("name")
    g.add_argument("--agents", type=int, default=6)
    g.add_argument("--seed", type=int, default=7)
    g.add_argument("--force", action="store_true", help="replace an existing base")
    g.add_argument("--with", dest="with_chars", action="append", default=[], metavar="CHAR",
                   help="include a saved character as a founder (repeatable)")
    g.add_argument("--real", action="store_true", help="let a live model author the web")
    g.set_defaults(func=cmd_genesis)

    pl = sub.add_parser("play", help="fork a base into a playthrough (or resume one) and live it")
    pl.add_argument("name")
    pl.add_argument("--ticks", type=int, default=20)
    pl.add_argument("--present", action="store_true", help="you're here; think harder")
    pl.add_argument("--real", action="store_true", help="live Claude cognition")
    pl.add_argument("--as", dest="as_", metavar="STORY",
                    help="name this playthrough (fork one base into many side-by-side stories)")
    pl.add_argument("--fresh", action="store_true",
                    help="restart from the base, discarding the current playthrough")
    pl.set_defaults(func=cmd_play)

    sub.add_parser("worlds", help="list the bases you can play").set_defaults(func=cmd_worlds)

    sc = sub.add_parser("save-char", help="save a being as a portable character")
    sc.add_argument("being", help="a being's id or name")
    sc.add_argument("--from", dest="frm", metavar="PLAY",
                    help="the playthrough to take it from (default: the scratch world)")
    sc.add_argument("--as", dest="as_", metavar="NAME", help="the character name to save under")
    sc.set_defaults(func=cmd_save_char)

    sub.add_parser("chars", help="list saved characters").set_defaults(func=cmd_chars)

    fg = sub.add_parser("forge", help="author a character from a description (rule, or --real model)")
    fg.add_argument("name")
    fg.add_argument("description", nargs="?", default="", help="a prose description of who they are")
    fg.add_argument("--real", action="store_true", help="let a live model author the character")
    fg.set_defaults(func=cmd_forge)

    ex = sub.add_parser("explore", help="walk the village in a window (needs the [game] extra)")
    ex.add_argument("name")
    ex.add_argument("--fresh", action="store_true", help="restart the playthrough from the base")
    ex.set_defaults(func=cmd_explore)

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
