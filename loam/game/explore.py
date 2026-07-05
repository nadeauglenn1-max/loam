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

from .. import config, dashboard, persistence
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


def _draw_being(surf, x, y, color, bob, label, font, highlight=False):
    x, y = int(x), int(y + bob)
    pygame.draw.ellipse(surf, (0, 0, 0), (x - 9, y + 12, 18, 6))          # shadow
    pygame.draw.rect(surf, color, (x - 6, y - 2, 12, 14), border_radius=5)  # body
    pygame.draw.circle(surf, color, (x, y - 7), 6)                        # head
    pygame.draw.circle(surf, (12, 12, 10), (x, y - 7), 6, 1)
    if highlight:
        pygame.draw.circle(surf, _PLAYER, (x, y + 2), 20, 2)
    tag = font.render(label, True, _INK if highlight else _MUTE)
    surf.blit(tag, (x - tag.get_width() // 2, y + 16))


def _draw_player(surf, x, y, bob):
    x, y = int(x), int(y + bob)
    pygame.draw.ellipse(surf, (0, 0, 0), (x - 10, y + 13, 20, 6))
    pygame.draw.rect(surf, _PLAYER, (x - 7, y - 3, 14, 16), border_radius=5)
    pygame.draw.circle(surf, _PLAYER, (x, y - 9), 7)
    pygame.draw.circle(surf, (40, 34, 12), (x, y - 9), 7, 1)


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
    colors = {n: c for n, c in dashboard._tribe_colors(world).items()}
    families = sorted({a.home for a in world.agents.values() if a.home})
    houses = _house_positions(rects["the hearth"], families)
    bg = _background(W, H, rects, houses, small)   # the static village — built once
    pos: dict[str, list[float]] = {}
    px, py = W / 2, H - 120
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
        if reading is None:
            speed = 230 * dt
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                px -= speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                px += speed
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                py -= speed
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                py += speed
            px = max(14, min(W - 14, px))
            py = max(60, min(H - 14, py))
            accum += dt
            if accum >= 1 / world_tps and world.living():
                world.step()
                accum = 0

        for a in world.living():
            home = _being_pos(a, rects, houses)
            if a.id not in pos:
                pos[a.id] = list(home)
            else:
                cur = pos[a.id]
                cur[0] += (home[0] - cur[0]) * min(1, dt * 3)
                cur[1] += (home[1] - cur[1]) * min(1, dt * 3)
        for gone in [i for i in pos if i not in world.agents]:
            pos.pop(gone, None)

        near = None if reading else _near_id(pos, px, py)

        screen.blit(bg, (0, 0))
        for aid, (x, y) in sorted(pos.items(), key=lambda kv: kv[1][1]):
            a = world.agents.get(aid)
            if not a:
                continue
            bob = math.sin(frame * 0.12 + hash(aid) % 7) * 1.6
            _draw_being(screen, x, y, colors.get(a.name, _LONE), bob, a.name, small,
                        highlight=(aid == near or aid == reading))
        _draw_player(screen, px, py, math.sin(frame * 0.15) * 1.2)

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
