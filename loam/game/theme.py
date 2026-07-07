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
# A cozy, golden-hour storybook village: warm greens, packed earth, lamplight.
GROUND = (38, 52, 34)
GRASS = ((58, 92, 54), (66, 102, 60), (50, 82, 48), (74, 112, 66))
TUFT = (44, 74, 42)
FLOWERS = ((236, 210, 110), (218, 142, 172), (150, 180, 226), (236, 162, 120), (240, 240, 236))
PATH = (128, 102, 68)
PATH_EDGE = (104, 82, 54)
SHADOW = (20, 24, 18)
WATER = ((34, 74, 100), (52, 104, 132))
SHEEN = (156, 204, 212)
WOOD = (86, 60, 38)
ROOF = (170, 86, 62)
ROOF_LIT = (198, 112, 80)
ROOF_DARK = (128, 60, 44)
WALL = (200, 170, 128)
WALL_SHADE = (158, 130, 94)
STONE = (134, 136, 142)
STONE_DARK = (94, 96, 102)
LEAF = ((30, 66, 38), (46, 92, 52), (78, 132, 74))
WARMLIGHT = (255, 216, 150)
INK = (243, 240, 230)
MUTE = (178, 174, 158)
PANEL = (30, 30, 24)
PANEL_HI = (44, 44, 35)
LINE = (70, 68, 54)
PLAYER = (250, 236, 190)
CAPE = (238, 202, 112)

SKIN = [(244, 206, 168), (228, 184, 146), (200, 154, 114), (160, 116, 84), (122, 86, 62)]
HAIR = [(44, 34, 28), (104, 68, 40), (162, 118, 66), (214, 180, 104), (196, 198, 202), (140, 52, 38)]
TUNIC = [(74, 122, 168), (176, 90, 78), (96, 158, 102), (182, 148, 68),
         (140, 104, 172), (86, 156, 164), (192, 122, 154), (122, 138, 80)]
OUTLINE = (16, 17, 12)

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
        self._glow_cache: dict = {}

    def _radial(self, r: int, color):
        s = self._glow_cache.get((r, color))
        if s is None:
            s = pygame.Surface((2 * r, 2 * r), pygame.SRCALPHA)
            for rad in range(r, 0, -1):
                f = (1 - rad / r) ** 1.6
                pygame.draw.circle(s, (int(color[0] * f), int(color[1] * f),
                                       int(color[2] * f)), (r, r), rad)
            self._glow_cache[(r, color)] = s
        return s

    def _glow(self, surf, cx, cy, r, color):
        surf.blit(self._radial(r, color), (int(cx - r), int(cy - r)),
                  special_flags=pygame.BLEND_RGB_ADD)

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
        """Each area reads as its own terrain, not a tinted box."""
        kind = VILLAGE.get(place, ("", ""))[1]
        if kind == "home":
            return (96, 78, 54)          # a packed-earth courtyard
        if kind == "square":
            return (98, 92, 80)          # cobblestone
        if kind == "field":
            return (108, 80, 52)         # tilled soil
        if kind == "marsh":
            return (44, 68, 68)          # wet ground
        if kind == "wood":
            d = PLACES[place]["danger"]
            b = 66 - int(d * 20)         # forest floor, darker the deadlier it is
            return (b - 18, b, b - 26)
        return (72, 100, 62)

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
        # a soft, dithered meadow — blended tiles, speckled, then strewn with life
        tile = 22
        for ty in range(0, H, tile):
            for tx in range(0, W, tile):
                shade = GRASS[int(layout._unit(f"{tx}:{ty}:g") * len(GRASS))]
                bg.fill(shade, (tx, ty, tile, tile))
        rng = random.Random("meadow")
        for _ in range(900):                                   # grain of texture
            gx, gy = rng.randint(0, W), rng.randint(64, H)
            bg.set_at((gx, gy), rng.choice(GRASS))
        self._paths(bg, rects)                                 # dirt lanes between the rooms
        for _ in range(360):                                   # grass tufts
            gx, gy = rng.randint(0, W), rng.randint(70, H)
            pygame.draw.line(bg, TUFT, (gx, gy), (gx, gy - rng.randint(2, 4)), 1)
        for _ in range(64):                                    # wildflowers, in little clusters
            fx, fy, col = rng.randint(0, W), rng.randint(70, H), rng.choice(FLOWERS)
            for _ in range(rng.randint(1, 3)):
                bg.set_at((fx + rng.randint(-3, 3), fy + rng.randint(-3, 3)), col)
        for place, rect in rects.items():
            x, y, rw, rh = rect
            name, kind = VILLAGE.get(place, (place, "square"))
            tint = self.room_tint(place)
            self._round(bg, (x + 3, y + 5, rw, rh), SHADOW, 18)     # soft drop shadow
            self._round(bg, rect, tint, 18)
            self._terrain_grain(bg, rect, tint)                     # a little texture within
            self._round(bg, (x + 2, y + 2, rw - 4, rh - 4), self._lift(tint, 20), 16, width=1)
            self._round(bg, rect, LINE, 18, width=2)
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
            plate = pygame.Surface((self.font.size(name)[0] + 18, 40), pygame.SRCALPHA)
            plate.fill((0, 0, 0, 70))
            bg.blit(plate, (x + 6, y + 6))
            bg.blit(self.font.render(name, True, INK), (x + 13, y + 9))
            bg.blit(self.small.render(self.danger_word(place), True, MUTE), (x + 13, y + 29))
        return bg

    def _paths(self, bg, rects):
        rs = list(rects.values())
        if not rs:
            return
        lefts = sorted({r[0] for r in rs})
        tops = sorted({r[1] for r in rs})
        w_of = {r[0]: r[2] for r in rs}
        h_of = {r[1]: r[3] for r in rs}
        x0, x1 = min(lefts) - 8, max(r[0] + r[2] for r in rs) + 8
        y0, y1 = min(tops) - 8, max(r[1] + r[3] for r in rs) + 8
        vg = [(lefts[i] + w_of[lefts[i]] + lefts[i + 1]) // 2 for i in range(len(lefts) - 1)]
        hg = [(tops[i] + h_of[tops[i]] + tops[i + 1]) // 2 for i in range(len(tops) - 1)]
        for gx in vg:
            self._lane(bg, (gx - 9, y0, 18, y1 - y0))
        for gy in hg:
            self._lane(bg, (x0, gy - 9, x1 - x0, 18))

    def _lane(self, bg, rect):
        x, y, w, h = rect
        pygame.draw.rect(bg, PATH_EDGE, (x - 1, y - 1, w + 2, h + 2), border_radius=8)
        pygame.draw.rect(bg, PATH, rect, border_radius=8)
        rng = random.Random(f"{x}:{y}:lane")
        for _ in range(max(w, h) // 12):                       # pebbles
            px = rng.randint(x + 2, x + w - 2)
            py = rng.randint(y + 2, y + h - 2)
            pygame.draw.circle(bg, self._lift(PATH, 22), (px, py), 1)

    def _terrain_grain(self, bg, rect, tint):
        x, y, w, h = rect
        rng = random.Random(f"{x}:{y}:grain")
        dark, lite = tuple(max(0, c - 12) for c in tint), self._lift(tint, 12)
        for _ in range(int(w * h / 340)):
            bg.set_at((rng.randint(x + 4, x + w - 4), rng.randint(y + 4, y + h - 4)),
                      rng.choice((dark, lite)))

    @staticmethod
    def _lift(color, by=14):
        return tuple(min(255, c + by) for c in color)

    def _house(self, surf, x, y, label):
        x, y = int(x), int(y)
        roof = [(x - 22, y - 2), (x + 22, y - 2), (x, y - 24)]
        pygame.draw.ellipse(surf, SHADOW, (x - 20, y + 13, 40, 8))               # ground shadow
        pygame.draw.rect(surf, WALL, (x - 17, y - 4, 34, 22), border_radius=3)   # wall
        pygame.draw.rect(surf, WALL_SHADE, (x - 17, y + 9, 34, 9), border_radius=3)  # wall shade
        pygame.draw.polygon(surf, ROOF, roof)
        pygame.draw.polygon(surf, ROOF_LIT, [(x - 22, y - 2), (x, y - 2), (x, y - 24)])  # sunlit slope
        for i in range(-16, 17, 5):                                             # thatch texture
            pygame.draw.line(surf, ROOF_DARK, (x + i, y - 3), (x + i * 0.45, y - 13), 1)
        pygame.draw.polygon(surf, OUTLINE, roof, 1)
        pygame.draw.rect(surf, WALL_SHADE, (x + 11, y - 22, 4, 10))              # chimney
        pygame.draw.rect(surf, OUTLINE, (x + 11, y - 22, 4, 10), 1)
        pygame.draw.rect(surf, (44, 30, 20), (x - 5, y + 4, 9, 14), border_radius=3)  # door
        pygame.draw.circle(surf, (196, 168, 110), (x + 2, y + 11), 1)            # door knob
        self._glow(surf, x + 10, y + 4, 16, (150, 110, 46))                     # lamplight bloom
        pygame.draw.rect(surf, (238, 198, 112), (x + 7, y, 6, 6))               # lit window
        pygame.draw.line(surf, (120, 92, 40), (x + 10, y), (x + 10, y + 6), 1)
        pygame.draw.rect(surf, OUTLINE, (x + 7, y, 6, 6), 1)
        tag = self.small.render(label, True, INK)
        surf.blit(tag, (x - tag.get_width() // 2, y + 21))

    def _square(self, surf, rect):
        x, y, w, h = rect
        rng = random.Random(f"{x}:sq")
        for _ in range(int(w * h / 1100)):                            # cobbles
            pygame.draw.circle(surf, STONE_DARK,
                               (rng.randint(int(x + 16), int(x + w - 16)),
                                rng.randint(int(y + 46), int(y + h - 14))), rng.randint(2, 3))
        cx, cy = int(x + w * 0.32), int(y + h * 0.62)                 # the well
        pygame.draw.ellipse(surf, SHADOW, (cx - 17, cy + 9, 34, 9))
        pygame.draw.circle(surf, STONE, (cx, cy), 15)
        pygame.draw.circle(surf, STONE_DARK, (cx, cy), 15, 2)
        pygame.draw.circle(surf, WATER[0], (cx, cy), 8)
        pygame.draw.circle(surf, WATER[1], (cx - 2, cy - 2), 4)
        pygame.draw.rect(surf, WOOD, (cx - 14, cy - 28, 3, 24))       # roof posts
        pygame.draw.rect(surf, WOOD, (cx + 11, cy - 28, 3, 24))
        pygame.draw.polygon(surf, ROOF, [(cx - 19, cy - 26), (cx + 19, cy - 26), (cx, cy - 36)])
        pygame.draw.polygon(surf, OUTLINE, [(cx - 19, cy - 26), (cx + 19, cy - 26), (cx, cy - 36)], 1)
        pygame.draw.rect(surf, WOOD, (cx - 3, cy - 20, 6, 5))         # bucket
        sx, sy = int(x + w * 0.70), int(y + h * 0.44)                 # market stall
        pygame.draw.ellipse(surf, SHADOW, (sx - 26, sy + 19, 54, 8))
        pygame.draw.rect(surf, (122, 94, 62), (sx - 24, sy, 48, 20), border_radius=2)
        awning = [(sx - 28, sy - 9), (sx + 28, sy - 9), (sx + 24, sy), (sx - 24, sy)]
        for i in range(4):                                           # striped awning
            col = (178, 90, 72) if i % 2 == 0 else (218, 202, 170)
            pygame.draw.rect(surf, col, (sx - 28 + i * 14, sy - 9, 14, 9))
        pygame.draw.polygon(surf, OUTLINE, awning, 1)
        pygame.draw.circle(surf, (208, 172, 76), (sx - 12, sy + 8), 3)   # apples on the counter
        pygame.draw.circle(surf, (176, 92, 80), (sx + 2, sy + 8), 3)
        for bx in (sx - 32, sx + 26):                                # barrels
            pygame.draw.rect(surf, WOOD, (bx, sy + 5, 8, 13), border_radius=2)
            pygame.draw.line(surf, (44, 30, 20), (bx, sy + 10), (bx + 8, sy + 10), 1)

    def _field(self, surf, rect):
        x, y, w, h = rect
        rows = list(range(int(y + 48), int(y + h - 16), 16))
        for ry in rows:
            pygame.draw.line(surf, (76, 56, 36), (x + 18, ry + 5), (x + w - 14, ry + 5), 3)  # furrow
            pygame.draw.line(surf, (128, 96, 62), (x + 18, ry + 4), (x + w - 14, ry + 4), 1)
        for i, ry in enumerate(rows):
            for rx in range(int(x + 22), int(x + w - 14), 15):
                pygame.draw.line(surf, (74, 116, 48), (rx, ry + 4), (rx, ry - 6), 2)  # stalk
                ripe = (i + rx) % 3 == 0
                pygame.draw.circle(surf, (208, 176, 88) if ripe else (150, 182, 78), (rx, ry - 7), 3)
                pygame.draw.circle(surf, self._lift((208, 176, 88) if ripe else (150, 182, 78), 26),
                                   (rx - 1, ry - 8), 1)
        sx, sy = int(x + w - 40), int(y + 60)                        # a scarecrow
        pygame.draw.rect(surf, WOOD, (sx - 1, sy, 2, 22))
        pygame.draw.rect(surf, WOOD, (sx - 10, sy + 6, 20, 2))
        pygame.draw.circle(surf, (198, 168, 96), (sx, sy - 2), 4)
        pygame.draw.polygon(surf, (150, 120, 60), [(sx - 6, sy - 3), (sx + 6, sy - 3), (sx, sy - 9)])

    def _marsh(self, surf, rect):
        x, y, w, h = rect
        rng = random.Random(f"{x}:{y}:marsh")
        for _ in range(6):                                             # still pools, layered
            px = rng.randint(int(x + 20), int(x + w - 46))
            py = rng.randint(int(y + 46), int(y + h - 26))
            pw, ph = rng.randint(32, 58), rng.randint(15, 24)
            pygame.draw.ellipse(surf, WATER[0], (px, py, pw, ph))
            pygame.draw.ellipse(surf, WATER[1], (px + 2, py + 2, pw - 4, ph - 5))
            pygame.draw.ellipse(surf, SHEEN, (px + 6, py + 3, pw - 18, 3))       # sheen
            self._glow(surf, px + pw // 2, py + ph // 2, 12, (16, 34, 40))       # water shimmer
            if rng.random() < 0.6:                                     # a lily pad + bloom
                lx, ly = px + pw // 2, py + ph // 2
                pygame.draw.circle(surf, (58, 110, 66), (lx, ly), 4)
                pygame.draw.circle(surf, (224, 172, 192), (lx, ly), 1)
        for _ in range(20):                                            # cattails
            tx = rng.randint(int(x + 16), int(x + w - 16))
            ty = rng.randint(int(y + 44), int(y + h - 12))
            pygame.draw.line(surf, (92, 116, 66), (tx, ty), (tx, ty - rng.randint(9, 14)), 1)
            if rng.random() < 0.4:
                pygame.draw.rect(surf, (96, 66, 40), (tx - 1, ty - 14, 2, 4))    # the head

    def _wood(self, surf, rect, danger):
        x, y, w, h = rect
        rng = random.Random(f"{x}:{y}:wood")
        for _ in range(int(6 + danger * 6)):                           # ferns / bushes underfoot
            bx = rng.randint(int(x + 16), int(x + w - 16))
            by = rng.randint(int(y + 46), int(y + h - 12))
            pygame.draw.circle(surf, LEAF[0], (bx, by), 4)
            pygame.draw.circle(surf, LEAF[1], (bx - 1, by - 1), 2)
            if rng.random() < 0.12:                                    # a mushroom
                pygame.draw.rect(surf, (222, 214, 196), (bx + 5, by - 2, 2, 4))
                pygame.draw.circle(surf, (176, 74, 62), (bx + 6, by - 3), 2)
        trees = [(rng.randint(int(x + 18), int(x + w - 18)),
                  rng.randint(int(y + 48), int(y + h - 14))) for _ in range(int(9 + danger * 14))]
        for tx, ty in sorted(trees, key=lambda t: t[1]):              # painter's order
            r = rng.randint(9, 13)
            dk = max(0, 1 - danger * 0.35)                            # deeper woods, darker leaves
            base = tuple(int(c * dk) for c in LEAF[0])
            mid = tuple(int(c * dk) for c in LEAF[1])
            hi = tuple(int(c * dk) for c in LEAF[2])
            pygame.draw.ellipse(surf, SHADOW, (tx - r, ty - 1, r * 2, 6))
            pygame.draw.rect(surf, WOOD, (tx - 2, ty - 7, 4, 9))                 # trunk
            pygame.draw.circle(surf, base, (tx, ty - r - 4), r)                  # canopy base
            pygame.draw.circle(surf, mid, (tx - 2, ty - r - 6), r - 2)           # mid
            pygame.draw.circle(surf, hi, (tx - 4, ty - r - 8), r - 5)            # sunlit highlight

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

    def draw_player(self, surf, x, y, step, moving, facing, gender=""):
        x, y = int(x), int(y)
        style = 1 if gender == "female" else 2 if gender == "male" else 0  # hair only — no difference
        self._figure(surf, x, y, (245, 222, 178), (120, 90, 40), PLAYER, style,
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
        ph = 200
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
        rels = sorted(being.relationships.items(), key=lambda kv: abs(kv[1]), reverse=True)
        parts = [f"{world.agents[oid].name} {'+' if v > 0 else ''}{v:.0f}"
                 for oid, v in rels[:4] if oid in world.agents]
        screen.blit(self.font.render("ties: " + (", ".join(parts) or "none yet"), True, MUTE), (x, y))
        y += 22
        # you and them: how drawn you are, and how close you've grown
        from .. import bonds as bondlib
        lvl = world.player.bond(being.id)
        wed = world.player.spouse == being.id
        drawn = bondlib.attraction_word(bondlib.attraction(being))
        you_line = (f"you and {being.name}: {bondlib.tier(lvl, wed=wed)} — you find them {drawn}")
        screen.blit(self.font.render(you_line, True, (224, 196, 176)), (x, y))
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
