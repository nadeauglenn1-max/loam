"""The look of the world — a swappable graphics subsystem.

Everything about how Loam *looks* lives here: the palette, the fonts, how a place
reads as a village anchor, how a person is drawn, the day/night wash, the panels.
The explore client owns none of this — it owns the loop, the input, and the sim,
and asks a ``Theme`` to draw. So the graphics are a subsystem you can tweak, fork,
or replace wholesale (write another ``Theme``, pass it to ``explore.run``) without
touching the core. Not a deep component — a skin.

Pure pygame rendering, so — like the render loop — it's smoke-tested through the
client, not unit-tested, and omitted from coverage.
"""
from __future__ import annotations

import math
import random

import pygame

from ..config import PLACES
from . import layout

# ---- palette (edit here to reskin, or subclass Theme) ------------------------
GROUND = (21, 27, 18)
GRASS = ((31, 48, 29), (35, 54, 32), (27, 43, 26), (39, 58, 35))
TUFT = (24, 40, 23)
FLOWERS = ((198, 182, 96), (186, 126, 156), (150, 172, 212), (214, 152, 112))
SHADOW = (12, 15, 10)
INK = (240, 237, 227)
MUTE = (170, 166, 152)
PANEL = (26, 27, 21)
LINE = (58, 58, 48)
PLAYER = (245, 232, 180)

SKIN = [(242, 203, 165), (226, 182, 143), (198, 152, 112), (158, 114, 82), (120, 84, 60)]
HAIR = [(38, 30, 26), (92, 62, 38), (150, 110, 62), (206, 172, 96), (184, 186, 190), (122, 44, 32)]
TUNIC = [(70, 110, 150), (156, 82, 70), (90, 142, 92), (162, 132, 60),
         (120, 92, 150), (80, 140, 148), (172, 110, 140), (110, 122, 72)]
OUTLINE = (12, 13, 9)

# how each sim place reads as a village anchor: (display name, motif)
VILLAGE = {
    "the hearth":    ("Homes", "home"),
    "the commons":   ("The Square", "square"),
    "the meadow":    ("The Fields", "field"),
    "the mire":      ("The Marsh", "marsh"),
    "the thornwood": ("The Thornwood", "wood"),
    "the deepwood":  ("The Deep Wood", "wood"),
}


def _pick(palette, seed):
    return palette[int(layout._unit(seed) * len(palette)) % len(palette)]


def appearance(agent) -> tuple:
    """A distinct look, deterministic from id — tunic hue shared by household so
    families read as kin while individuals stay recognizable. Font-free, so it's
    testable headless without a display."""
    skin = _pick(SKIN, agent.id + ":skin")
    hair = _pick(HAIR, agent.id + ":hair")
    tunic = _pick(TUNIC, (agent.home or agent.id) + ":fam")
    style = int(layout._unit(agent.id + ":style") * 3) % 3
    return skin, hair, tunic, style


class Theme:
    """The default Loam look. Swap it by writing another with the same methods."""
    name = "loam-default"

    # fonts are lazy so a Theme can be constructed before pygame is initialized
    # (a caller builds one and hands it to run(); run() inits the display first)
    _FONTS = {"small": ("consolas,menlo,monospace", 12, False),
              "font":  ("consolas,menlo,monospace", 14, False),
              "big":   ("segoeui,arial,sans-serif", 22, True)}

    def __init__(self) -> None:
        self._font_cache: dict = {}
        self._vignette: pygame.Surface | None = None

    def _f(self, key: str):
        if key not in self._font_cache:
            name, size, bold = self._FONTS[key]
            self._font_cache[key] = pygame.font.SysFont(name, size, bold=bold)
        return self._font_cache[key]

    @property
    def small(self):
        return self._f("small")

    @property
    def font(self):
        return self._f("font")

    @property
    def big(self):
        return self._f("big")

    # ---- pure visual decisions -------------------------------------------
    def room_tint(self, place: str) -> tuple[int, int, int]:
        d = PLACES[place]["danger"]
        if place == "the hearth":
            return (48, 40, 30)
        if VILLAGE.get(place, ("", ""))[1] == "marsh":
            return (26, 40, 42)
        if d < 0.1:
            return (30, 44, 34)
        if d < 0.45:
            return (46, 38, 22)
        return (46, 26, 20)

    def danger_word(self, place: str) -> str:
        d = PLACES[place]["danger"]
        return "safe" if d < 0.1 else "risky" if d < 0.45 else "deadly"

    def sky(self, t: float) -> tuple[int, int, int, int]:
        """A translucent day/night tint for the fraction-of-day t."""
        if t < 0.18:
            return (28, 38, 82, 95)      # deep night
        if t < 0.28:
            return (70, 60, 85, 45)      # dawn
        if t < 0.68:
            return (0, 0, 0, 0)          # day — clear
        if t < 0.82:
            return (150, 80, 30, 55)     # dusk
        return (20, 24, 58, 110)         # night

    def appearance(self, agent) -> tuple:
        return appearance(agent)

    # ---- the static village ----------------------------------------------
    def build_background(self, W, H, rects, houses) -> pygame.Surface:
        bg = pygame.Surface((W, H))
        bg.fill(GROUND)
        # a soft, dithered meadow — tiles blended, then strewn with tufts and flowers
        tile = 24
        for ty in range(0, H, tile):
            for tx in range(0, W, tile):
                shade = GRASS[int(layout._unit(f"{tx}:{ty}:g") * len(GRASS))]
                bg.fill(shade, (tx, ty, tile, tile))
        rng = random.Random("meadow")
        for _ in range(520):                                   # grass tufts
            gx, gy = rng.randint(0, W), rng.randint(80, H)
            pygame.draw.line(bg, TUFT, (gx, gy), (gx, gy - rng.randint(2, 4)), 1)
        for _ in range(70):                                    # wildflowers
            fx, fy = rng.randint(0, W), rng.randint(80, H)
            pygame.draw.circle(bg, rng.choice(FLOWERS), (fx, fy), 1)
        for place, rect in rects.items():
            x, y, rw, rh = rect
            name, kind = VILLAGE.get(place, (place, "square"))
            self._round(bg, (x + 3, y + 4, rw, rh), SHADOW, 16)   # a soft drop shadow
            self._round(bg, rect, self.room_tint(place), 16)
            self._round(bg, (x + 2, y + 2, rw - 4, rh - 4), self._lift(self.room_tint(place)), 14, width=1)
            self._round(bg, rect, LINE, 16, width=2)
            if kind == "home":
                for fam, (hx, hy) in houses.items():
                    self._house(bg, hx, hy, fam)
            elif kind == "square":
                self._square(bg, rect)
            elif kind == "field":
                self._field(bg, rect)
            elif kind == "marsh":
                self._marsh(bg, rect)
            elif kind == "wood":
                self._wood(bg, rect, PLACES[place]["danger"])
            label = self.font.render(name, True, INK)
            bg.blit(label, (x + 13, y + 9))
            bg.blit(self.small.render(self.danger_word(place), True, MUTE), (x + 13, y + 29))
        return bg

    @staticmethod
    def _lift(color, by=14):
        return tuple(min(255, c + by) for c in color)

    def _house(self, surf, x, y, label):
        x, y = int(x), int(y)
        pygame.draw.rect(surf, SHADOW, (x - 18, y - 2, 38, 24), border_radius=3)   # ground shadow
        pygame.draw.rect(surf, (104, 82, 58), (x - 17, y - 4, 34, 22), border_radius=3)  # wall
        pygame.draw.rect(surf, (86, 66, 46), (x - 17, y + 8, 34, 10), border_radius=3)   # wall shade
        pygame.draw.polygon(surf, (138, 72, 52), [(x - 22, y - 3), (x + 22, y - 3), (x, y - 23)])  # roof
        pygame.draw.polygon(surf, (158, 88, 66), [(x - 22, y - 3), (x, y - 3), (x, y - 23)])       # roof lit side
        pygame.draw.polygon(surf, OUTLINE, [(x - 22, y - 3), (x + 22, y - 3), (x, y - 23)], 1)
        pygame.draw.rect(surf, (150, 40, 30), (x + 11, y - 20, 4, 8))            # chimney
        pygame.draw.rect(surf, (46, 32, 22), (x - 4, y + 6, 9, 12), border_radius=2)  # door
        pygame.draw.rect(surf, (214, 176, 96), (x + 7, y + 1, 6, 6))             # lit window
        pygame.draw.rect(surf, OUTLINE, (x + 7, y + 1, 6, 6), 1)
        tag = self.small.render(label, True, MUTE)
        surf.blit(tag, (x - tag.get_width() // 2, y + 21))

    def _square(self, surf, rect):
        x, y, w, h = rect
        cx, cy = int(x + w * 0.34), int(y + h * 0.60)
        pygame.draw.ellipse(surf, SHADOW, (cx - 16, cy + 8, 32, 10))
        pygame.draw.circle(surf, (96, 98, 104), (cx, cy), 16)          # well stones
        pygame.draw.circle(surf, (60, 62, 68), (cx, cy), 16, 2)
        pygame.draw.circle(surf, (20, 30, 46), (cx, cy), 9)            # water
        pygame.draw.circle(surf, (44, 66, 92), (cx - 2, cy - 2), 4)    # a glint
        pygame.draw.rect(surf, (86, 60, 40), (cx - 15, cy - 26, 3, 22))   # roof posts
        pygame.draw.rect(surf, (86, 60, 40), (cx + 12, cy - 26, 3, 22))
        pygame.draw.polygon(surf, (140, 74, 52), [(cx - 20, cy - 24), (cx + 20, cy - 24), (cx, cy - 34)])
        sx, sy = int(x + w * 0.70), int(y + h * 0.46)                  # market stall
        pygame.draw.rect(surf, SHADOW, (sx - 24, sy + 20, 50, 8))
        pygame.draw.rect(surf, (116, 90, 62), (sx - 24, sy, 48, 20), border_radius=2)
        for i in range(4):                                            # striped awning
            col = (168, 82, 66) if i % 2 == 0 else (206, 190, 160)
            pygame.draw.rect(surf, col, (sx - 28 + i * 14, sy - 9, 14, 9))
        pygame.draw.circle(surf, (196, 160, 70), (sx - 12, sy + 8), 3)  # goods
        pygame.draw.circle(surf, (150, 80, 70), (sx + 4, sy + 8), 3)

    def _field(self, surf, rect):
        x, y, w, h = rect
        rows = list(range(int(y + 48), int(y + h - 16), 16))
        for ry in rows:
            pygame.draw.line(surf, (54, 44, 30), (x + 18, ry + 5), (x + w - 14, ry + 5), 3)  # furrow
        for i, ry in enumerate(rows):
            for rx in range(int(x + 22), int(x + w - 14), 15):
                pygame.draw.line(surf, (70, 104, 44), (rx, ry + 4), (rx, ry - 5), 2)   # stalk
                top = (150, 176, 74) if (i + rx) % 3 else (196, 168, 84)              # leaf / ripe
                pygame.draw.circle(surf, top, (rx, ry - 6), 3)

    def _marsh(self, surf, rect):
        x, y, w, h = rect
        rng = random.Random(f"{x}:{y}:marsh")
        for _ in range(6):                                             # still pools, layered
            px = rng.randint(int(x + 20), int(x + w - 46))
            py = rng.randint(int(y + 46), int(y + h - 26))
            pw, ph = rng.randint(30, 54), rng.randint(14, 22)
            pygame.draw.ellipse(surf, (28, 54, 64), (px, py, pw, ph))
            pygame.draw.ellipse(surf, (40, 74, 86), (px + 2, py + 2, pw - 4, ph - 4))
            pygame.draw.ellipse(surf, (70, 112, 120), (px + 5, py + 3, pw - 16, 3))   # sheen
            if rng.random() < 0.6:                                     # a lily pad
                lx, ly = px + pw // 2, py + ph // 2
                pygame.draw.circle(surf, (58, 104, 66), (lx, ly), 4)
                pygame.draw.circle(surf, (210, 160, 180), (lx, ly), 1)
        for _ in range(18):                                            # reeds
            tx = rng.randint(int(x + 16), int(x + w - 16))
            ty = rng.randint(int(y + 44), int(y + h - 12))
            pygame.draw.line(surf, (86, 108, 62), (tx, ty), (tx - 1, ty - rng.randint(8, 13)), 1)
            pygame.draw.line(surf, (86, 108, 62), (tx + 3, ty), (tx + 4, ty - rng.randint(6, 11)), 1)

    def _wood(self, surf, rect, danger):
        x, y, w, h = rect
        rng = random.Random(f"{x}:{y}:wood")
        trees = [(rng.randint(int(x + 18), int(x + w - 18)),
                  rng.randint(int(y + 46), int(y + h - 16))) for _ in range(int(10 + danger * 16))]
        for tx, ty in sorted(trees, key=lambda t: t[1]):              # painter's order
            r = rng.randint(8, 12)
            g = max(34, 78 - int(danger * 32))
            pygame.draw.ellipse(surf, SHADOW, (tx - r, ty - 2, r * 2, 6))
            pygame.draw.rect(surf, (60, 44, 30), (tx - 2, ty - 6, 4, 8))         # trunk
            pygame.draw.circle(surf, (20, g - 12, 26), (tx, ty - r - 4), r)      # canopy base
            pygame.draw.circle(surf, (26, g, 34), (tx - 2, ty - r - 6), r - 2)   # mid
            pygame.draw.circle(surf, (34, g + 16, 44), (tx - 4, ty - r - 8), r - 5)  # highlight

    # ---- people -----------------------------------------------------------
    def _legs(self, surf, x, y, step, moving, color=(52, 38, 28)):
        off = int(math.sin(step) * 3) if moving else 0
        pygame.draw.rect(surf, color, (x - 4, y - 6 + max(0, off), 3, 7), border_radius=1)
        pygame.draw.rect(surf, color, (x + 2, y - 6 + max(0, -off), 3, 7), border_radius=1)
        pygame.draw.rect(surf, (34, 26, 18), (x - 5, y - 1 + max(0, off), 4, 2))   # feet
        pygame.draw.rect(surf, (34, 26, 18), (x + 1, y - 1 + max(0, -off), 4, 2))

    def _figure(self, surf, x, y, skin, hair, tunic, style, step, moving, facing, hair_back=True):
        pygame.draw.ellipse(surf, SHADOW, (x - 8, y - 1, 16, 5))                 # shadow
        self._legs(surf, x, y, step, moving)
        shade = tuple(max(0, c - 26) for c in tunic)
        lift = self._lift(tunic, 22)
        body = pygame.Rect(x - 7, y - 19, 14, 15)
        pygame.draw.rect(surf, tunic, body, border_radius=5)                    # tunic
        pygame.draw.rect(surf, shade, (x - 7, y - 8, 14, 4), border_radius=3)    # hem shade
        pygame.draw.rect(surf, lift, (x - 2, y - 18, 4, 12), border_radius=2)    # centre highlight
        pygame.draw.rect(surf, OUTLINE, body, width=1, border_radius=5)
        pygame.draw.rect(surf, tunic, (x - 9, y - 18, 3, 9), border_radius=2)    # arms
        pygame.draw.rect(surf, tunic, (x + 6, y - 18, 3, 9), border_radius=2)
        pygame.draw.rect(surf, skin, (x - 2, y - 22, 4, 4))                      # neck
        hy = y - 26
        if hair_back:
            pygame.draw.circle(surf, hair, (x, hy - 1), 7)                       # hair behind
        pygame.draw.circle(surf, skin, (x, hy), 6)                              # head
        pygame.draw.circle(surf, OUTLINE, (x, hy), 6, 1)
        if style == 1:                                                          # long hair
            pygame.draw.rect(surf, hair, (x - 7, hy - 1, 3, 12), border_radius=2)
            pygame.draw.rect(surf, hair, (x + 4, hy - 1, 3, 12), border_radius=2)
        cap = 5 if style == 2 else 6                                            # short vs fuller
        pygame.draw.circle(surf, hair, (x, hy - 4), cap)                        # crown
        pygame.draw.circle(surf, self._lift(hair, 18), (x - 2, hy - 5), 2)      # sheen
        ex = 2 * facing
        pygame.draw.circle(surf, (24, 20, 16), (x - 2 + ex, hy), 1)             # eyes
        pygame.draw.circle(surf, (24, 20, 16), (x + 3 + ex, hy), 1)

    def draw_person(self, surf, x, y, appr, step, moving, facing, name, highlight=False):
        skin, hair, tunic, style = appr
        x, y = int(x), int(y)
        if highlight:
            pygame.draw.circle(surf, PLAYER, (x, y - 12), 22, 2)
        self._figure(surf, x, y, skin, hair, tunic, style, step, moving, facing)
        tag = self.small.render(name, True, INK if highlight else MUTE)
        surf.blit(tag, (x - tag.get_width() // 2, y + 4))

    def draw_player(self, surf, x, y, step, moving, facing):
        x, y = int(x), int(y)
        self._figure(surf, x, y, (245, 222, 178), (120, 90, 40), PLAYER, 1,
                     step, moving, facing)
        pygame.draw.polygon(surf, (198, 168, 96),                               # a gold cape
                            [(x - 7, y - 18), (x + 7, y - 18), (x + 5, y - 4), (x - 5, y - 4)])
        pygame.draw.polygon(surf, OUTLINE,
                            [(x - 7, y - 18), (x + 7, y - 18), (x + 5, y - 4), (x - 5, y - 4)], 1)

    # ---- overlays: sky wash, vignette, hud, panels ------------------------
    def apply_sky(self, screen, W, H, t):
        c = self.sky(t)
        if c[3]:
            wash = pygame.Surface((W, H), pygame.SRCALPHA)
            wash.fill(c)
            screen.blit(wash, (0, 0))

    def apply_vignette(self, screen, W, H):
        if self._vignette is None:
            v = pygame.Surface((W, H), pygame.SRCALPHA)
            for i in range(6):
                a = 8 + i * 6
                pygame.draw.rect(v, (0, 0, 0, a), (i * 3, i * 3, W - i * 6, H - i * 6), 3)
            self._vignette = v
        screen.blit(self._vignette, (0, 0))

    def draw_hud(self, screen, W, world):
        pygame.draw.rect(screen, PANEL, (0, 0, W, 44))
        pygame.draw.line(screen, LINE, (0, 44), (W, 44))
        screen.blit(self.big.render("Loam", True, INK), (16, 8))
        # a sun that arcs across the bar and dims to a moon at night
        phase = world.phase()
        night = phase == "night"
        sun_x = 82 + int(world.time_of_day * 44)
        color = (150, 160, 210) if night else (240, 210, 120)
        pygame.draw.circle(screen, color, (sun_x, 22), 8)
        if night:
            pygame.draw.circle(screen, PANEL, (sun_x + 3, 19), 7)   # crescent
        hud = (f"Day {world.day} · {phase} · {len(world.living())} alive · "
               "arrows/WASD to walk · E to meet · Esc to leave")
        screen.blit(self.font.render(hud, True, MUTE), (140, 15))

    def draw_meter(self, screen, W, world):
        """Your understanding of the village — the story's meter — top-right."""
        from .. import rifts
        frac, done, total = rifts.progress(world)
        bw, x, y = 240, W - 240 - 16, 52
        box = pygame.Rect(x, y, bw, 60)
        self._round(screen, box, PANEL, 10)
        self._round(screen, box, LINE, 10, width=2)
        title = ("You understand everyone" if rifts.all_understood(world)
                 else f"You understand  {done}/{total} families")
        screen.blit(self.small.render(title, True, INK), (x + 12, y + 8))
        bx, by, bwid = x + 12, y + 26, bw - 24
        pygame.draw.rect(screen, (40, 40, 34), (bx, by, bwid, 8), border_radius=4)
        pygame.draw.rect(screen, (150, 200, 150), (bx, by, int(bwid * frac), 8), border_radius=4)
        openr = world.rifts()
        focus = (f"nearest: {openr[0].family} · {int(openr[0].level * 100)}%"
                 if openr else "every tongue is open to you")
        screen.blit(self.small.render(focus, True, MUTE), (x + 12, y + 40))

    def draw_reading_panel(self, screen, being, world, W, H):
        ph = 176
        panel = pygame.Rect(16, H - ph - 16, W - 32, ph)
        self._round(screen, panel, PANEL, 14)
        self._round(screen, panel, LINE, 14, width=2)
        x, y = panel.x + 18, panel.y + 14
        screen.blit(self.big.render(being.name, True, INK), (x, y))
        sub = f"{being.condition} · {being.vocation or 'no trade'} · at {being.location}"
        screen.blit(self.font.render(sub, True, MUTE),
                    (x + self.big.size(being.name)[0] + 14, y + 6))
        y += 34
        for line in self._wrap(being.story or "(no story)", self.font, panel.w - 36)[:2]:
            screen.blit(self.font.render(line, True, INK), (x, y))
            y += 20
        screen.blit(self.font.render(f"thinks: {being.last_thought or '(quiet)'}",
                                     True, (200, 210, 190)), (x, y))
        y += 22
        goods = ", ".join(f"{amt:g} {g}" for g, amt in being.goods.items() if amt >= 0.5) or "nothing"
        screen.blit(self.font.render(f"carries: {goods}", True, MUTE), (x, y))
        y += 22
        bonds = sorted(being.relationships.items(), key=lambda kv: abs(kv[1]), reverse=True)
        parts = [f"{world.agents[oid].name} {'+' if v > 0 else ''}{v:.0f}"
                 for oid, v in bonds[:4] if oid in world.agents]
        screen.blit(self.font.render("ties: " + (", ".join(parts) or "none yet"), True, MUTE), (x, y))
        # the story line: their family, and how far you've come to understand it
        from .. import rifts
        fam = rifts.family_of(being)
        level = int(world.player.of(fam) * 100)
        understood = world.player.understands(fam)
        note = (f"the {fam} — you understand them {level}%"
                if not understood else f"the {fam} — you understand them")
        screen.blit(self.font.render(note, True, (200, 210, 190)),
                    (x, panel.bottom - 26))
        hint = "E / Esc — step back" if understood else "H — help them · E / Esc — step back"
        t = self.font.render(hint, True, MUTE)
        screen.blit(t, (panel.right - t.get_width() - 18, panel.bottom - 26))

    def draw_near_hint(self, screen, name, px, py):
        t = self.font.render(f"press E to meet {name}", True, INK)
        self._round(screen, (int(px) - t.get_width() // 2 - 10, int(py) - 46,
                             t.get_width() + 20, 24), PANEL, 8)
        screen.blit(t, (int(px) - t.get_width() // 2, int(py) - 42))

    # ---- primitives -------------------------------------------------------
    @staticmethod
    def _round(surf, rect, color, radius=12, width=0):
        pygame.draw.rect(surf, color, rect, width, border_radius=radius)

    @staticmethod
    def _wrap(text, font, width):
        words, lines, line = text.split(), [], ""
        for w in words:
            trial = f"{line} {w}".strip()
            if font.size(trial)[0] <= width:
                line = trial
            else:
                if line:
                    lines.append(line)
                line = w
        if line:
            lines.append(line)
        return lines
