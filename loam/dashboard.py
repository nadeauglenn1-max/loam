"""A window into the world — a self-contained HTML view you can leave open and
watch while the world lives.

Renders the map with every being placed where it stands, coloured by its tongue
(so you can see tribes cluster and move), the vital signs, the economy of bloom,
and the recent feed. `loam serve` serves this and lets the page refresh itself.
"""
from __future__ import annotations

import html
from typing import TYPE_CHECKING

from . import metrics
from .config import PLACES

if TYPE_CHECKING:  # pragma: no cover
    from .world import World

# A palette for tongue-tribes. Lone tongues fall back to a neutral gray.
_TRIBE_COLORS = ("#1D9E75", "#378ADD", "#D85A30", "#7F77DD", "#BA7517",
                 "#D4537E", "#639922", "#0F6E56", "#185FA5", "#993C1D")
_LONE = "#5F5E5A"

_BG = "#14140f"
_CARD = "#20201a"
_INK = "#efece2"
_MUTE = "#a8a496"
_LINE = "#34342b"


def _tribe_colors(world: "World") -> dict[str, str]:
    """name -> colour, so members of the same tongue share a colour."""
    out: dict[str, str] = {}
    ci = 0
    for tribe in metrics.factions(world):
        if len(tribe) == 1:
            out[tribe[0]] = _LONE
        else:
            color = _TRIBE_COLORS[ci % len(_TRIBE_COLORS)]
            ci += 1
            for name in tribe:
                out[name] = color
    return out


def _danger_word(d: float) -> str:
    return "safe" if d < 0.1 else "risky" if d < 0.45 else "deadly"


def _e(s: str) -> str:
    return html.escape(str(s))


def render_page(world: "World", *, refresh: int = 0) -> str:
    c = metrics.census(world)
    frac, _, _ = metrics.coverage(world)
    colors = _tribe_colors(world)
    meta = f'<meta http-equiv="refresh" content="{refresh}">' if refresh else ""

    vitals = [
        ("tick", world.tick), ("alive", c["population"]), ("generations", c["generations"]),
        ("avg vitality", c["avg_vitality"]), ("shared tongue", f"{frac * 100:.0f}%"),
        ("born", c["births"]),
        ("died", c["deaths_hunger"] + c["deaths_age"] + c["deaths_forage"] + c["deaths_violence"]),
    ]
    vital_html = "".join(
        f'<div class="vital"><div class="v">{_e(v)}</div><div class="k">{_e(k)}</div></div>'
        for k, v in vitals)

    cards = []
    for place, d in PLACES.items():
        here = [a for a in world.agents.values() if a.location == place]
        here.sort(key=lambda a: a.name)
        stock = world.bloom.get(place, 0.0)
        ceil = max(1.0, d["wild"] * 9.0)
        bar = min(100, int(stock / ceil * 100))
        chips = "".join(
            f'<span class="chip" style="background:{colors.get(a.name, _LONE)}" '
            f'title="{_e(a.condition)}, vit {a.vitality:.2f}, age {a.age}, holds {a.bloom:.0f} bloom">'
            f'{_e(a.name)}<i style="opacity:{max(0.25, min(1.0, a.vitality)):.2f}"></i></span>'
            for a in here) or '<span class="empty">—</span>'
        cards.append(
            f'<div class="place"><div class="phead"><span class="pname">{_e(place)}</span>'
            f'<span class="danger d-{_danger_word(d["danger"])}">{_danger_word(d["danger"])}</span></div>'
            f'<div class="bloom"><div class="bloomfill" style="width:{bar}%"></div></div>'
            f'<div class="bloomn">bloom {stock:.1f}</div>'
            f'<div class="chips">{chips}</div></div>')
    map_html = "".join(cards)

    give, take = c["gifts"], c["seizures"]
    tot = max(1, give + take)
    econ = (f'<div class="econ"><div class="ebar">'
            f'<div class="give" style="width:{give / tot * 100:.0f}%"></div>'
            f'<div class="take" style="width:{take / tot * 100:.0f}%"></div></div>'
            f'<div class="econk">{give} gifts · {take} seizures · '
            f'{c["matings"]} matings · {c["deaths_violence"]} killed</div></div>')

    tied = metrics.ties(world, 8)
    tie_rows = "".join(
        f'<div class="tie"><span>{_e(na)} <i>&amp;</i> {_e(nb)}</span>'
        f'<span class="{"bond" if s > 0 else "fric"}">{s:+.0f}</span></div>'
        for na, nb, s in tied) or '<span class="empty">no ties yet</span>'
    ties_html = (f'<div class="ties"><div class="tieshead">the ties that bind</div>'
                 f'{tie_rows}</div>')

    feed = "".join(f'<div class="line">{_e(line)}</div>' for line in world.feed[-16:])

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">{meta}
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Loam · tick {world.tick}</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:{_BG};color:{_INK};font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif}}
.wrap{{max-width:1100px;margin:0 auto;padding:22px}}
h1{{font-size:20px;font-weight:500;margin:0 0 14px}}
.dot{{color:{_MUTE};font-weight:400}}
.vitals{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px}}
.vital{{background:{_CARD};border:1px solid {_LINE};border-radius:10px;padding:10px 14px;min-width:92px}}
.vital .v{{font-size:20px;font-weight:500}}
.vital .k{{font-size:12px;color:{_MUTE}}}
.map{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}}
.place{{background:{_CARD};border:1px solid {_LINE};border-radius:12px;padding:12px;min-height:120px}}
.phead{{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}}
.pname{{font-weight:500}}
.danger{{font-size:11px;padding:2px 8px;border-radius:20px}}
.d-safe{{background:#12352a;color:#5DCAA5}} .d-risky{{background:#3a2a08;color:#EF9F27}} .d-deadly{{background:#3a170c;color:#F0997B}}
.bloom{{height:6px;background:{_LINE};border-radius:6px;overflow:hidden}}
.bloomfill{{height:100%;background:#5DCAA5}}
.bloomn{{font-size:11px;color:{_MUTE};margin:3px 0 8px}}
.chips{{display:flex;flex-wrap:wrap;gap:5px}}
.chip{{font-size:12px;color:#0d0d0a;padding:2px 7px;border-radius:20px;display:inline-flex;align-items:center;gap:4px}}
.chip i{{width:6px;height:6px;border-radius:50%;background:#0d0d0a;display:inline-block}}
.empty{{color:{_MUTE}}}
.econ{{margin-bottom:18px}}
.ebar{{display:flex;height:10px;border-radius:6px;overflow:hidden;background:{_LINE}}}
.give{{background:#1D9E75}} .take{{background:#D85A30}}
.econk{{font-size:12px;color:{_MUTE};margin-top:5px}}
.ties{{background:{_CARD};border:1px solid {_LINE};border-radius:12px;padding:12px;margin-bottom:18px}}
.tieshead{{font-size:12px;color:{_MUTE};margin-bottom:8px}}
.tie{{display:flex;justify-content:space-between;font-size:13px;padding:2px 0}}
.tie i{{color:{_MUTE};font-style:normal}}
.bond{{color:#5DCAA5}} .fric{{color:#F0997B}}
.feed{{background:{_CARD};border:1px solid {_LINE};border-radius:12px;padding:12px;font:13px/1.6 ui-monospace,Menlo,Consolas,monospace}}
.feed .line{{color:{_MUTE};white-space:pre-wrap}}
</style></head><body><div class="wrap">
<h1>Loam <span class="dot">· tick {world.tick} · the one who understands is watching</span></h1>
<div class="vitals">{vital_html}</div>
<div class="map">{map_html}</div>
{econ}
{ties_html}
<div class="feed">{feed}</div>
</div></body></html>"""
