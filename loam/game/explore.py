"""The explore client — walk the village, meet its people, watch it live.

A pygame window over the live sim, **in-process**: the World ticks as you move,
beings drift between places, and you can walk up to anyone to read who they are.
This module owns only the *core* — the loop, the input, and stepping the sim; how
it all *looks* belongs to a swappable ``Theme`` (see theme.py). Pass a different
theme to reskin the whole world without touching a line here.

Cost: the world loops on the FREE rule cognition; the paid model is never touched
here. Meeting a being reads its already-lived state (story, thought, bonds) — a
future "converse" beat is where a model would plug in, on interaction only.
"""
from __future__ import annotations

import pygame

from .. import config, persistence
from ..cognition import RuleCognition
from . import layout, theme as theme_mod
from .theme import Theme

# a stable, font-free handle on the look for tests and external callers
_appearance = theme_mod.appearance


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


def _being_pos(a, rects, houses):
    """Beings in the home quarter cluster at their family's house; elsewhere they
    stand at a stable spot in the area."""
    if a.location == "the hearth" and a.home in houses:
        hx, hy = houses[a.home]
        return (hx + (layout._unit(a.id + ":hx") - 0.5) * 26,
                hy + layout._unit(a.id + ":hy") * 16 + 20)
    return layout.being_home(a.id, a.location, rects)


def run(base_name, *, fresh=False, world_tps=None, max_frames=None,
        screenshot=None, theme=None):
    """Open the window on a playthrough forked from `base_name` (or resumed).
    `theme` swaps the whole look; `screenshot` saves the final frame to a PNG."""
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
    theme = theme or Theme()

    rects = layout.place_rects(W, H)
    families = sorted({a.home for a in world.agents.values() if a.home})
    houses = _house_positions(rects["the hearth"], families)
    bg = theme.build_background(W, H, rects, houses)   # the static village — built once

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
            pmoving = bool(left or right or up or down)
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
                apprs[aid] = theme.appearance(a)
            tx, ty = targets.get(aid, (x, y))
            moving = (tx - x) ** 2 + (ty - y) ** 2 > 6
            theme.draw_person(screen, x, y, apprs[aid], frame * 0.35, moving,
                              facing.get(aid, 1), a.name,
                              highlight=(aid == near or aid == reading))
        theme.draw_player(screen, px, py, frame * 0.35, pmoving, pfacing)

        theme.apply_sky(screen, W, H, world.time_of_day)
        theme.apply_vignette(screen, W, H)
        theme.draw_hud(screen, W, world)

        if reading and reading in world.agents:
            theme.draw_reading_panel(screen, world.agents[reading], world, W, H)
        elif near:
            theme.draw_near_hint(screen, world.agents[near].name, px, py)

        pygame.display.flip()
        if max_frames is not None and frame >= max_frames:
            running = False

    if screenshot:
        pygame.image.save(screen, screenshot)
    persistence.save_play(world)
    pygame.quit()


def _near_id(pos, px, py, radius=42):
    return layout.nearest_being(px, py, {i: tuple(p) for i, p in pos.items()}, radius)
