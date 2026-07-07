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
GROUND = (17, 19, 14)
GRASS = ((27, 41, 25), (31, 47, 29), (24, 38, 23))
INK = (239, 236, 226)
MUTE = (168, 164, 150)
PANEL = (26, 27, 21)
LINE = (52, 52, 43)
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
        tile = 34
        for ty in range(0, H, tile):
            for tx in range(0, W, tile):
                shade = GRASS[int(layout._unit(f"{tx}:{ty}:g") * len(GRASS))]
                bg.fill(shade, (tx, ty, tile, tile))
        for place, rect in rects.items():
            x, y, rw, rh = rect
            name, kind = VILLAGE.get(place, (place, "square"))
            self._round(bg, rect, self.room_tint(place), 14)
            self._round(bg, rect, LINE, 14, width=2)
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
            bg.blit(self.font.render(name, True, INK), (x + 12, y + 8))
            bg.blit(self.small.render(self.danger_word(place), True, MUTE), (x + 12, y + 28))
        return bg

    def _house(self, surf, x, y, label):
        x, y = int(x), int(y)
        pygame.draw.rect(surf, (96, 76, 55), (x - 17, y - 4, 34, 22), border_radius=3)
        pygame.draw.polygon(surf, (122, 62, 46), [(x - 22, y - 4), (x + 22, y - 4), (x, y - 22)])
        pygame.draw.polygon(surf, OUTLINE, [(x - 22, y - 4), (x + 22, y - 4), (x, y - 22)], 1)
        pygame.draw.rect(surf, (50, 36, 24), (x - 4, y + 6, 8, 12))
        pygame.draw.rect(surf, (214, 176, 96), (x + 8, y + 2, 5, 5))     # a lit window
        tag = self.small.render(label, True, MUTE)
        surf.blit(tag, (x - tag.get_width() // 2, y + 20))

    def _square(self, surf, rect):
        x, y, w, h = rect
        cx, cy = int(x + w * 0.34), int(y + h * 0.60)
        pygame.draw.circle(surf, (78, 78, 86), (cx, cy), 15)            # the well
        pygame.draw.circle(surf, (38, 38, 44), (cx, cy), 15, 2)
        pygame.draw.circle(surf, (24, 34, 52), (cx, cy), 8)
        sx, sy = int(x + w * 0.68), int(y + h * 0.44)                   # a market stall
        pygame.draw.rect(surf, (104, 82, 58), (sx - 24, sy, 48, 20))
        pygame.draw.rect(surf, (152, 74, 60), (sx - 28, sy - 9, 56, 9))

    def _field(self, surf, rect):
        x, y, w, h = rect
        for ry in range(int(y + 46), int(y + h - 14), 15):
            for rx in range(int(x + 22), int(x + w - 14), 13):
                pygame.draw.line(surf, (86, 122, 52), (rx, ry), (rx, ry - 8), 2)

    def _marsh(self, surf, rect):
        x, y, w, h = rect
        rng = random.Random(f"{x}:{y}:marsh")
        for _ in range(5):                                             # still pools
            px = rng.randint(int(x + 22), int(x + w - 34))
            py = rng.randint(int(y + 48), int(y + h - 22))
            pw = rng.randint(20, 40)
            pygame.draw.ellipse(surf, (36, 66, 78), (px, py, pw, pw // 2))
            pygame.draw.ellipse(surf, (58, 96, 104), (px + 3, py + 2, pw - 6, 3))
        for _ in range(14):                                            # reeds
            tx = rng.randint(int(x + 16), int(x + w - 16))
            ty = rng.randint(int(y + 44), int(y + h - 12))
            pygame.draw.line(surf, (74, 96, 58), (tx, ty), (tx, ty - 10), 1)

    def _wood(self, surf, rect, danger):
        x, y, w, h = rect
        rng = random.Random(f"{x}:{y}:wood")
        for _ in range(int(9 + danger * 16)):
            tx = rng.randint(int(x + 16), int(x + w - 16))
            ty = rng.randint(int(y + 44), int(y + h - 14))
            g = max(30, 74 - int(danger * 34))
            pygame.draw.polygon(surf, (28, g, 34), [(tx - 7, ty), (tx + 7, ty), (tx, ty - 16)])
            pygame.draw.polygon(surf, OUTLINE, [(tx - 7, ty), (tx + 7, ty), (tx, ty - 16)], 1)
            pygame.draw.rect(surf, (58, 42, 28), (tx - 1, ty, 2, 5))

    # ---- people -----------------------------------------------------------
    def _legs(self, surf, x, y, step, moving, color=(58, 44, 32)):
        off = int(math.sin(step) * 3) if moving else 0
        pygame.draw.rect(surf, color, (x - 5, y - 7 + max(0, off), 3, 8))
        pygame.draw.rect(surf, color, (x + 2, y - 7 + max(0, -off), 3, 8))

    def draw_person(self, surf, x, y, appr, step, moving, facing, name, highlight=False):
        skin, hair, tunic, style = appr
        x, y = int(x), int(y)
        pygame.draw.ellipse(surf, (10, 12, 8), (x - 9, y - 1, 18, 6))            # shadow
        self._legs(surf, x, y, step, moving)
        body = pygame.Rect(x - 7, y - 20, 14, 15)
        pygame.draw.rect(surf, tunic, body, border_radius=4)                    # tunic
        pygame.draw.rect(surf, OUTLINE, body, width=1, border_radius=4)
        pygame.draw.rect(surf, tunic, (x - 9, y - 19, 3, 10), border_radius=2)  # arms
        pygame.draw.rect(surf, tunic, (x + 6, y - 19, 3, 10), border_radius=2)
        hy = y - 27
        pygame.draw.circle(surf, hair, (x, hy - 3), 8)                          # hair
        pygame.draw.circle(surf, skin, (x, hy), 7)                              # head
        pygame.draw.circle(surf, OUTLINE, (x, hy), 7, 1)
        if style == 1:                                                          # long hair
            pygame.draw.rect(surf, hair, (x - 8, hy - 1, 3, 11), border_radius=2)
            pygame.draw.rect(surf, hair, (x + 5, hy - 1, 3, 11), border_radius=2)
        ex = 2 * facing
        pygame.draw.circle(surf, (26, 22, 18), (x - 2 + ex, hy), 1)             # eyes
        pygame.draw.circle(surf, (26, 22, 18), (x + 3 + ex, hy), 1)
        if highlight:
            pygame.draw.circle(surf, PLAYER, (x, y - 12), 24, 2)
        tag = self.small.render(name, True, INK if highlight else MUTE)
        surf.blit(tag, (x - tag.get_width() // 2, y + 4))

    def draw_player(self, surf, x, y, step, moving, facing):
        x, y = int(x), int(y)
        pygame.draw.ellipse(surf, (10, 12, 8), (x - 10, y - 1, 20, 6))
        self._legs(surf, x, y, step, moving, color=(120, 96, 34))
        cloak = pygame.Rect(x - 8, y - 21, 16, 16)
        pygame.draw.rect(surf, PLAYER, cloak, border_radius=4)                  # cloak
        pygame.draw.rect(surf, OUTLINE, cloak, width=1, border_radius=4)
        pygame.draw.circle(surf, (120, 90, 40), (x, y - 31), 8)                 # hair
        pygame.draw.circle(surf, (245, 222, 178), (x, y - 28), 8)              # head
        pygame.draw.circle(surf, OUTLINE, (x, y - 28), 8, 1)
        ex = 2 * facing
        pygame.draw.circle(surf, (26, 22, 18), (x - 2 + ex, y - 28), 1)
        pygame.draw.circle(surf, (26, 22, 18), (x + 3 + ex, y - 28), 1)

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
        screen.blit(self.font.render("E / Esc — step back", True, MUTE),
                    (panel.right - 150, panel.bottom - 24))

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
