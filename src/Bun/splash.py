#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import math
import random
import shutil
import sys
import time
from contextlib import contextmanager

try:
    import select
    import termios
    import tty
except Exception:  # pragma: no cover - platform specific
    select = None
    termios = None
    tty = None

# ========= ANSI =========
RESET = "\033[0m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
CLEAR = "\033[2J"
HOME = "\033[H"

# ========= ГРАДИЕНТ =========
GRADIENT = [
    "\033[38;2;80;60;20m",
    "\033[38;2;120;90;30m",
    "\033[38;2;170;130;40m",
    "\033[38;2;210;170;60m",
    "\033[38;2;238;178;64m",
    "\033[38;2;255;220;140m",
]

PARTICLES = ["·", "•"]

# ========= TEXT =========
BUN = [
    "█████  ██   ██ ███    ██",
    "██  ██ ██   ██ ████   ██",
    "█████  ██   ██ ██ ██  ██",
    "██  ██ ██   ██ ██  ██ ██",
    "█████   █████  ██   ████",
]


def move(x: int, y: int) -> None:
    print(f"\033[{y};{x}H", end="")


def clear() -> None:
    print(CLEAR + HOME, end="")


def flush() -> None:
    sys.stdout.flush()


def center() -> tuple[int, int]:
    cols, rows = shutil.get_terminal_size()
    return (cols - len(BUN[0])) // 2, (rows - len(BUN)) // 2


def text_points(offset: int, top: int) -> list[tuple[int, int, int, int]]:
    pts: list[tuple[int, int, int, int]] = []
    for y, row in enumerate(BUN):
        for x, ch in enumerate(row):
            if ch != " ":
                pts.append((offset + x, top + y, x, y))
    return pts


def make_text_map(points: list[tuple[int, int, int, int]]) -> set[tuple[int, int]]:
    return {(x, y) for (x, y, _, _) in points}


def create_particles(cx: float, cy: float, radius: float, n: int) -> list[dict]:
    parts: list[dict] = []
    for _ in range(n):
        a = random.uniform(0, 2 * math.pi)
        r = radius * random.random()

        parts.append(
            {
                "x": cx + math.cos(a) * r,
                "y": cy + math.sin(a) * r * 0.5,
                "vx": 0,
                "vy": 0,
                "target": None,
                "done": False,
                "gx": 0,
                "gy": 0,
            }
        )
    return parts


def assign_targets(parts: list[dict], targets: list[tuple[int, int, int, int]]) -> None:
    for i, p in enumerate(parts):
        tx, ty, gx, gy = targets[i % len(targets)]
        p["target"] = (tx, ty)
        p["gx"] = gx
        p["gy"] = gy


def create_ambient_particles(
    text_map: set[tuple[int, int]], cols: int, rows: int, count: int = 400
) -> list[dict]:
    parts: list[dict] = []

    cx = cols / 2
    cy = rows / 2
    max_dist = math.hypot(cx, cy)

    while len(parts) < count:
        x = random.randint(1, cols)
        y = random.randint(1, rows)

        if (x, y) in text_map:
            continue

        d = math.hypot(x - cx, y - cy)
        t = (d / max_dist) ** 1.6

        if random.random() > (1 - t):
            parts.append(
                {
                    "x": x,
                    "y": y,
                    "char": random.choice(PARTICLES),
                    "t": t,
                    "visible": False,
                    "delay": random.uniform(0, 0.6),
                }
            )

    return parts


def draw_ambient(parts: list[dict], text_map: set[tuple[int, int]]) -> None:
    for p in parts:
        if not p["visible"]:
            continue

        if (p["x"], p["y"]) in text_map:
            continue

        color_idx = int((1 - p["t"]) * (len(GRADIENT) - 1))
        color = GRADIENT[color_idx]

        move(p["x"], p["y"])
        print(f"{color}{p['char']}{RESET}", end="")


def update_idle(parts: list[dict]) -> None:
    for p in parts:
        p["x"] += random.uniform(-0.3, 0.3)
        p["y"] += random.uniform(-0.2, 0.2)


def update_seek(parts: list[dict], strength: float) -> int:
    done_count = 0

    for p in parts:
        if p["done"]:
            done_count += 1
            continue

        tx, ty = p["target"]
        dx = tx - p["x"]
        dy = ty - p["y"]

        dist = math.hypot(dx, dy)

        if dist < 0.4:
            p["done"] = True
            p["x"], p["y"] = tx, ty
            done_count += 1
            continue

        p["vx"] += dx * strength
        p["vy"] += dy * strength

        p["vx"] *= 0.8
        p["vy"] *= 0.8

        p["x"] += p["vx"]
        p["y"] += p["vy"]

    return done_count


def draw_particles(parts: list[dict], w: int, h: int, text_map: set[tuple[int, int]]) -> None:
    for p in parts:
        x, y = int(p["x"]), int(p["y"])

        if not p["done"] and (x, y) in text_map:
            continue

        i = p["gx"] + p["gy"] * w
        color = GRADIENT[int(i / max(1, w * h) * (len(GRADIENT) - 1))]

        move(x, y)

        if p["done"]:
            print(f"{color}█{RESET}", end="")
        else:
            print(f"{color}{random.choice(PARTICLES)}{RESET}", end="")


def draw_text(points: list[tuple[int, int, int, int]], w: int, h: int) -> None:
    for (x, y, gx, gy) in points:
        i = gx + gy * w
        color = GRADIENT[int(i / max(1, w * h) * (len(GRADIENT) - 1))]

        move(x, y)
        print(f"{color}█{RESET}", end="")


def cinematic_intro() -> None:
    print(HIDE_CURSOR, end="")
    clear()

    offset, top = center()
    w, h = len(BUN[0]), len(BUN)

    cx = offset + w // 2
    cy = top + h // 2
    radius = max(w, h) + 10

    targets = text_points(offset, top)
    text_map = make_text_map(targets)

    particles = create_particles(cx, cy, radius, n=len(targets))

    for _ in range(30):
        if _should_abort():
            return
        clear()
        update_idle(particles)
        draw_particles(particles, w, h, text_map)
        flush()
        time.sleep(0.03)

    assign_targets(particles, targets)

    for i in range(120):
        if _should_abort():
            return
        clear()
        strength = 0.01 + i / 700
        done = update_seek(particles, strength)
        draw_particles(particles, w, h, text_map)

        flush()
        time.sleep(0.025)

        if done > len(particles) * 0.92:
            break

    cols, rows = shutil.get_terminal_size()
    ambient = create_ambient_particles(text_map, cols, rows, 400)

    fade_frames = 60
    appear_speed = 1.6

    for i in range(fade_frames):
        if _should_abort():
            return
        clear()

        t = (i / fade_frames) ** 1.3

        draw_text(targets, w, h)

        for p in ambient:
            if not p["visible"] and p["delay"] < t * appear_speed:
                p["visible"] = True

        draw_ambient(ambient, text_map)

        move(offset + 4, top + h + 2)
        print(f"{GRADIENT[-2]}B U N  CLI READY{RESET}")

        flush()
        time.sleep(0.04)

    clear()
    draw_text(targets, w, h)
    draw_ambient(ambient, text_map)

    move(offset + 4, top + h + 2)
    print(f"{GRADIENT[-2]}B U N  CLI READY{RESET}")

    print(SHOW_CURSOR, end="")

def run_splash() -> None:
    try:
        with _cbreak_mode():
            cinematic_intro()
    except KeyboardInterrupt:
        print(SHOW_CURSOR, end="")
        clear()


def _should_abort() -> bool:
    if select is None or not sys.__stdin__ or not sys.__stdin__.isatty():
        return False
    try:
        readable, _, _ = select.select([sys.__stdin__], [], [], 0)
        if readable:
            sys.__stdin__.read(1)
            return True
    except Exception:
        return False
    return False


@contextmanager
def _cbreak_mode():
    if termios is None or tty is None or not sys.__stdin__ or not sys.__stdin__.isatty():
        yield
        return
    fd = sys.__stdin__.fileno()
    try:
        old_settings = termios.tcgetattr(fd)
    except Exception:
        yield
        return
    try:
        tty.setcbreak(fd)
        yield
    finally:
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            pass
