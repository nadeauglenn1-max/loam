"""The explore client — walk the village, meet its people, watch it live.

A pygame window over the live sim, **in-process**: the World ticks as you move,
beings drift between places, and you can walk up to anyone to read who they are.
Rendering is code-drawn (no art assets yet): a tiled ground, soft place-rooms
tinted by danger, little humanoid figures coloured by tongue-tribe, and a reading
panel.

Cost: the world loops on the FREE rule cognition; the paid model is never touched
here. Meeting a being reads its already-lived state (story, thought, bonds) — a
future "converse" beat is where a model would plug in, on interaction only.
"""
from __future__ import annotations

import math
import random

import pygame

from .. import config, persistence
from ..cognition import RuleCognition
from ..config import PLACES
from . import layout

# palette
_GROUND = (17, 19, 14)
_GRASS = ((28, 42, 26), (32, 48, 30))
_INK = (239, 236, 226)
_MUTE = (168, 164, 150)
_PANEL = (26, 27, 21)
_LINE = (52, 52, 43)
_PLAYER = (245, 232, 180)
_LONE = (95, 94, 90)


def _room_tint(place: str) -> tuple[int, int, int]:
    d = PLACES[place]["danger"]
    if place == "the hearth":
        return (48, 40, 30)
    if d < 0.1:
        return (30, 44, 34)
    if d < 0.45:
        return (46, 38, 22)
    return (46, 26, 20)


def _danger_word(place: str) -> str:
    d = PLACES[place]["danger"]
    return "safe" if d < 0.1 else "risky" if d < 0.45 else "deadly"


def _sky(t):
    """A translucent day/night tint (r, g, b, a) for the fraction-of-day t."""
    if t < 0.18:
        return (28, 38, 82, 95)      # deep night
    if t < 0.28:
        return (70, 60, 85, 45)      # dawn
    if t < 0.68:
        return (0, 0, 0, 0)          # day — clear
    if t < 0.82:
        return (150, 80, 30, 55)     # dusk
    return (20, 24, 58, 110)         # night


# how each sim place reads as a village anchor
VILLAGE = {
    "the hearth":    ("Homes", "home"),
    "the commons":   ("The Square", "square"),
    "the meadow":    ("The Fields", "field"),
    "the mire":      ("The Marsh Wood", "wood"),
    "the thornwood": ("The Thornwood", "wood"),
    "the deepwood":  ("The Deep Wood", "wood"),
}


def _house_positions(home_rect, families):
    x, y, w, h = home_rect
    n = max(1, len(families))
    cols = min(3, n)
    rows = (n + cols - 1) // cols
    cw, ch = w / cols, (h - 34) / max(1, rows)
    out = {}
    for i, fam in enumerate(families):
        r, c = divmod(i, cols)
        out[fam] = (x + cw * (c + 0.5), y + 44 + ch * (r + 0.5))
    return out


def _draw_house(surf, x, y, label, font):
    x, y = int(x), int(y)
    pygame.draw.rect(surf, (96, 76, 55), (x - 17, y - 4, 34, 22), border_radius=3)
    pygame.draw.polygon(surf, (122, 62, 46), [(x - 22, y - 4), (x + 22, y - 4), (x, y - 22)])
    pygame.draw.rect(surf, (50, 36, 24), (x - 4, y + 6, 8, 12))
    tag = font.render(label, True, _MUTE)
    surf.blit(tag, (x - tag.get_width() // 2, y + 20))


def _draw_square(surf, rect):
    x, y, w, h = rect
    cx, cy = int(x + w * 0.34), int(y + h * 0.60)
    pygame.draw.circle(surf, (78, 78, 86), (cx, cy), 15)         # the well
    pygame.draw.circle(surf, (38, 38, 44), (cx, cy), 15, 2)
    pygame.draw.circle(surf, (24, 34, 52), (cx, cy), 8)
    sx, sy = int(x + w * 0.68), int(y + h * 0.44)               # a market stall
    pygame.draw.rect(surf, (104, 82, 58), (sx - 24, sy, 48, 20))
    pygame.draw.rect(surf, (152, 74, 60), (sx - 28, sy - 9, 56, 9))


def _draw_field(surf, rect):
    x, y, w, h = rect
    for ry in range(int(y + 46), int(y + h - 14), 15):
        for rx in range(int(x + 22), int(x + w - 14), 13):
            pygame.draw.line(surf, (86, 122, 52), (rx, ry), (rx, ry - 8), 2)


def _draw_wood(surf, rect, danger):
    x, y, w, h = rect
    rng = random.Random(f"{x}:{y}:wood")
    for _ in range(int(9 + danger * 16)):
        tx = rng.randint(int(x + 16), int(x + w - 16))
        ty = rng.randint(int(y + 44), int(y + h - 14))
        g = max(30, 74 - int(danger * 34))
        pygame.draw.polygon(surf, (28, g, 34), [(tx - 7, ty), (tx + 7, ty), (tx, ty - 16)])
        pygame.draw.rect(surf, (58, 42, 28), (tx - 1, ty, 2, 5))


def _being_pos(a, rects, houses):
    """Beings in the home quarter cluster at their family's house; elsewhere they
    stand at a stable spot in the area."""
    if a.location == "the hearth" and a.home in houses:
        hx, hy = houses[a.home]
        return (hx + (layout._unit(a.id + ":hx") - 0.5) * 26,
                hy + layout._unit(a.id + ":hy") * 16 + 20)
    return layout.being_home(a.id, a.location, rects)


def _round(surf, rect, color, radius=12, width=0):
    pygame.draw.rect(surf, color, rect, width, border_radius=radius)


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


def _background(w, h, rects, houses, font):
    bg = pygame.Surface((w, h))
    bg.fill(_GROUND)
    tile = 34
    for ty in range(0, h, tile):
        for tx in range(0, w, tile):
            bg.fill(_GRASS[(tx // tile + ty // tile) % 2], (tx, ty, tile, tile))
    for place, rect in rects.items():
        x, y, rw, rh = rect
        name, kind = VILLAGE.get(place, (place, "square"))
        _round(bg, rect, _room_tint(place), 14)
        _round(bg, rect, _LINE, 14, width=2)
        if kind == "home":
            for fam, (hx, hy) in houses.items():
                _draw_house(bg, hx, hy, fam, font)
        elif kind == "square":
            _draw_square(bg, rect)
        elif kind == "field":
            _draw_field(bg, rect)
        elif kind == "wood":
            _draw_wood(bg, rect, PLACES[place]["danger"])
        bg.blit(font.render(name, True, _INK), (x + 12, y + 8))
        bg.blit(font.render(_danger_word(place), True, _MUTE), (x + 12, y + 28))
    return bg


# ---- people: distinct, code-drawn villagers who walk -----------------------
_SKIN = [(242, 203, 165), (226, 182, 143), (198, 152, 112), (158, 114, 82), (120, 84, 60)]
_HAIR = [(38, 30, 26), (92, 62, 38), (150, 110, 62), (206, 172, 96), (184, 186, 190), (122, 44, 32)]
_TUNIC = [(70, 110, 150), (156, 82, 70), (90, 142, 92), (162, 132, 60),
          (120, 92, 150), (80, 140, 148), (172, 110, 140), (110, 122, 72)]


def _pick(palette, seed):
    return palette[int(layout._unit(seed) * len(palette)) % len(palette)]


def _appearance(a):
    """A distinct look, deterministic from id — with the tunic hue shared by
    household, so families read as kin while individuals stay recognizable."""
    skin = _pick(_SKIN, a.id + ":skin")
    hair = _pick(_HAIR, a.id + ":hair")
    tunic = _pick(_TUNIC, (a.home or a.id) + ":fam")
    style = int(layout._unit(a.id + ":style") * 3) % 3
    return skin, hair, tunic, style


def _legs(surf, x, y, step, moving, color=(58, 44, 32)):
    off = int(math.sin(step) * 3) if moving else 0
    pygame.draw.rect(surf, color, (x - 5, y - 7 + max(0, off), 3, 8))
    pygame.draw.rect(surf, color, (x + 2, y - 7 + max(0, -off), 3, 8))


def _draw_person(surf, x, y, appr, step, moving, facing, name, font, highlight=False):
    skin, hair, tunic, style = appr
    x, y = int(x), int(y)
    pygame.draw.ellipse(surf, (10, 12, 8), (x - 9, y - 1, 18, 6))            # shadow
    _legs(surf, x, y, step, moving)
    pygame.draw.rect(surf, tunic, (x - 7, y - 20, 14, 15), border_radius=4)  # tunic
    pygame.draw.rect(surf, tunic, (x - 9, y - 19, 3, 10), border_radius=2)   # arms
    pygame.draw.rect(surf, tunic, (x + 6, y - 19, 3, 10), border_radius=2)
    hy = y - 27
    pygame.draw.circle(surf, skin, (x, hy), 7)                              # head
    pygame.draw.circle(surf, hair, (x, hy - 3), 7)                          # hair
    if style == 1:                                                          # long hair
        pygame.draw.rect(surf, hair, (x - 8, hy - 1, 3, 11), border_radius=2)
        pygame.draw.rect(surf, hair, (x + 5, hy - 1, 3, 11), border_radius=2)
    pygame.draw.circle(surf, skin, (x, hy + (3 if style == 2 else 1)), 6)   # face
    ex = 2 * facing
    pygame.draw.circle(surf, (26, 22, 18), (x - 2 + ex, hy), 1)             # eyes
    pygame.draw.circle(surf, (26, 22, 18), (x + 3 + ex, hy), 1)
    if highlight:
        pygame.draw.circle(surf, _PLAYER, (x, y - 12), 24, 2)
    tag = font.render(name, True, _INK if highlight else _MUTE)
    surf.blit(tag, (x - tag.get_width() // 2, y + 4))


def _draw_player(surf, x, y, step, moving, facing):
    x, y = int(x), int(y)
    pygame.draw.ellipse(surf, (10, 12, 8), (x - 10, y - 1, 20, 6))
    _legs(surf, x, y, step, moving, color=(120, 96, 34))
    pygame.draw.rect(surf, _PLAYER, (x - 8, y - 21, 16, 16), border_radius=4)   # cloak
    pygame.draw.circle(surf, (245, 222, 178), (x, y - 28), 8)                   # head
    pygame.draw.circle(surf, (120, 90, 40), (x, y - 31), 8)                     # hair
    pygame.draw.circle(surf, (245, 222, 178), (x, y - 26), 6)
    ex = 2 * facing
    pygame.draw.circle(surf, (26, 22, 18), (x - 2 + ex, y - 28), 1)
    pygame.draw.circle(surf, (26, 22, 18), (x + 3 + ex, y - 28), 1)


def _reading_panel(surf, being, world, font, big, w, h):
    ph = 168
    panel = pygame.Rect(16, h - ph - 16, w - 32, ph)
    _round(surf, panel, _PANEL, 14)
    _round(surf, panel, _LINE, 14, width=2)
    x, y = panel.x + 18, panel.y + 14
    surf.blit(big.render(f"{being.name}", True, _INK), (x, y))
    surf.blit(font.render(f"{being.condition} · at {being.location}", True, _MUTE),
              (x + big.size(being.name)[0] + 14, y + 6))
    y += 34
    for line in _wrap(being.story or "(no story)", font, panel.w - 36)[:2]:
        surf.blit(font.render(line, True, _INK), (x, y))
        y += 20
    thought = being.last_thought or "(quiet)"
    surf.blit(font.render(f"thinks: {thought}", True, (200, 210, 190)), (x, y))
    y += 22
    bonds = sorted(being.relationships.items(), key=lambda kv: abs(kv[1]), reverse=True)
    parts = []
    for oid, v in bonds[:4]:
        if oid in world.agents:
            parts.append(f"{world.agents[oid].name} {'+' if v > 0 else ''}{v:.0f}")
    surf.blit(font.render("ties: " + (", ".join(parts) or "none yet"), True, _MUTE), (x, y))
    surf.blit(font.render("E / Esc — step back", True, _MUTE),
              (panel.right - 150, panel.bottom - 24))


def run(base_name, *, fresh=False, world_tps=None, max_frames=None, screenshot=None):
    """Open the window on a playthrough forked from `base_name` (or resumed).
    `screenshot` saves the final frame to a PNG (used to preview headless)."""
    if world_tps is None:                    # pace a full day to SECONDS_PER_DAY
        world_tps = config.TICKS_PER_DAY / config.SECONDS_PER_DAY
    world = None if fresh else persistence.load_play(base_name)
    if world is None:
        world = persistence.fork(base_name)
    world.cognition = RuleCognition()      # the world loops FREE
    world.present = True

    pygame.display.init()
    pygame.font.init()
    W, H = 1024, 680
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption(f"Loam · {base_name}")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas,menlo,monospace", 14)
    small = pygame.font.SysFont("consolas,menlo,monospace", 12)
    big = pygame.font.SysFont("segoeui,arial,sans-serif", 22, bold=True)

    rects = layout.place_rects(W, H)
    families = sorted({a.home for a in world.agents.values() if a.home})
    houses = _house_positions(rects["the hearth"], families)
    bg = _background(W, H, rects, houses, small)   # the static village — built once
    pos: dict[str, list[float]] = {}
    apprs: dict[str, tuple] = {}
    targets: dict[str, tuple] = {}
    facing: dict[str, int] = {}
    px, py, pfacing = W / 2, H - 120, 1
    reading = None
    accum, frame = 0.0, 0
    running = True
    while running:
        dt = clock.tick(60) / 1000
        frame += 1
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if reading:
                        reading = None       # close the panel
                    else:
                        running = False      # nothing open — leave
                elif e.key in (pygame.K_e, pygame.K_SPACE):
                    reading = None if reading else _near_id(pos, px, py)

        keys = pygame.key.get_pressed()
        pmoving = False
        if reading is None:
            speed = 230 * dt
            left = keys[pygame.K_LEFT] or keys[pygame.K_a]
            right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
            up = keys[pygame.K_UP] or keys[pygame.K_w]
            down = keys[pygame.K_DOWN] or keys[pygame.K_s]
            px += speed * (right - left)
            py += speed * (down - up)
            pmoving = left or right or up or down
            if left:
                pfacing = -1
            elif right:
                pfacing = 1
            px = max(14, min(W - 14, px))
            py = max(60, min(H - 20, py))
            accum += dt
            if accum >= 1 / world_tps and world.living():
                world.step()
                accum = 0

        for a in world.living():
            tgt = _being_pos(a, rects, houses)
            targets[a.id] = tgt
            if a.id not in pos:
                pos[a.id] = list(tgt)
            else:
                cur = pos[a.id]
                dx, dy = tgt[0] - cur[0], tgt[1] - cur[1]
                if abs(dx) > 0.6:
                    facing[a.id] = 1 if dx > 0 else -1
                cur[0] += dx * min(1, dt * 2.2)
                cur[1] += dy * min(1, dt * 2.2)
        for gone in [i for i in pos if i not in world.agents]:
            pos.pop(gone, None)

        near = None if reading else _near_id(pos, px, py)

        screen.blit(bg, (0, 0))
        for aid, (x, y) in sorted(pos.items(), key=lambda kv: kv[1][1]):
            a = world.agents.get(aid)
            if not a:
                continue
            if aid not in apprs:
                apprs[aid] = _appearance(a)
            tx, ty = targets.get(aid, (x, y))
            moving = (tx - x) ** 2 + (ty - y) ** 2 > 6
            _draw_person(screen, x, y, apprs[aid], frame * 0.35, moving,
                         facing.get(aid, 1), a.name, small,
                         highlight=(aid == near or aid == reading))
        _draw_player(screen, px, py, frame * 0.35, pmoving, pfacing)

        sky = _sky(world.time_of_day)        # day/night wash over the world
        if sky[3]:
            wash = pygame.Surface((W, H), pygame.SRCALPHA)
            wash.fill(sky)
            screen.blit(wash, (0, 0))

        pygame.draw.rect(screen, _PANEL, (0, 0, W, 44))
        pygame.draw.line(screen, _LINE, (0, 44), (W, 44))
        screen.blit(big.render("Loam", True, _INK), (16, 8))
        hud = (f"Day {world.day} · {world.phase()} · {len(world.living())} alive · "
               "arrows/WASD to walk · E to meet · Esc to leave")
        screen.blit(font.render(hud, True, _MUTE), (96, 15))

        if reading and reading in world.agents:
            _reading_panel(screen, world.agents[reading], world, font, big, W, H)
        elif near:
            hint = f"press E to meet {world.agents[near].name}"
            t = font.render(hint, True, _INK)
            _round(screen, (int(px) - t.get_width() // 2 - 10, int(py) - 46,
                            t.get_width() + 20, 24), _PANEL, 8)
            screen.blit(t, (int(px) - t.get_width() // 2, int(py) - 42))

        pygame.display.flip()
        if max_frames is not None and frame >= max_frames:
            running = False

    if screenshot:
        pygame.image.save(screen, screenshot)
    persistence.save_play(world)
    pygame.quit()


def _near_id(pos, px, py, radius=42):
    return layout.nearest_being(px, py, {i: tuple(p) for i, p in pos.items()}, radius)
