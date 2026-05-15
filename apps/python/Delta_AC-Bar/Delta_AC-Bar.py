# -*- coding: utf-8 -*-
import ac
import acsys
import math

APP_NAME = "Delta AC Bar"

# Visual constants
HEIGHT_PX = 10
WIDTH_RATIO = 1.0  # 100% of screen width
BACKGROUND = (0.05, 0.05, 0.05, 0.65)
PROGRESS_COLOR = (1.0, 1.0, 1.0, 0.18)
FLASH_COLOR = (1.0, 1.0, 1.0, 0.45)

COLOR_PURPLE = (0.70, 0.35, 1.00, 0.90)
COLOR_GREEN = (0.20, 0.95, 0.45, 0.90)
COLOR_RED = (0.95, 0.25, 0.25, 0.90)

# State
app = 0
labels = [0, 0, 0]

last_norm = 0.0
current_sector = 0

# sector boundaries (normalized positions 0..1)
sector_bounds = [0.0, None, None, 1.0]

best_sector_times = [None, None, None]
prev_lap_sector_times = [None, None, None]
current_lap_sector_times = [None, None, None]

sector_results = [None, None, None]  # each: (color, delta_text)

flash_timer = 0.0
flash_duration = 0.18

# cached geometry
cached_res = (0, 0)
bar_rect = (0, 0, 600, HEIGHT_PX)


def clamp(v, a, b):
    return max(a, min(b, v))


def format_delta(dt):
    sign = "-" if dt < 0 else "+"
    return "%s%.3f" % (sign, abs(dt))


def get_resolution():
    try:
        return ac.getGameResolution()
    except Exception:
        return (1920, 1080)


def update_geometry():
    global cached_res, bar_rect
    res = get_resolution()
    if res != cached_res:
        cached_res = res
    w = int(res[0] * WIDTH_RATIO)
    h = HEIGHT_PX
    x = 0
    y = 0
    bar_rect = (x, y, w, h)
    if app:
        ac.setSize(app, w, h)
        ac.setPosition(app, x, y)
        # label positions
        for i in range(3):
            sx, ex = get_sector_bounds(i)
            cx = int(w * (sx + ex) * 0.5)
            ac.setPosition(labels[i], cx - 12, 0)


def get_sector_bounds(i):
    # fallback to equal thirds if unknown
    b1 = sector_bounds[1] if sector_bounds[1] is not None else (1.0 / 3.0)
    b2 = sector_bounds[2] if sector_bounds[2] is not None else (2.0 / 3.0)
    bounds = [0.0, b1, b2, 1.0]
    return (bounds[i], bounds[i + 1])


def register_sector_boundary(sector_index, norm_pos):
    # sector_index: 0->1 boundary sets bounds[1], 1->2 sets bounds[2]
    if sector_index == 0 and sector_bounds[1] is None:
        sector_bounds[1] = clamp(norm_pos, 0.05, 0.95)
    elif sector_index == 1 and sector_bounds[2] is None:
        sector_bounds[2] = clamp(norm_pos, 0.10, 0.98)


def on_sector_complete(idx, time_s):
    if idx < 0 or idx > 2:
        return
    current_lap_sector_times[idx] = time_s

    color = COLOR_RED
    delta = 0.0

    if best_sector_times[idx] is None or time_s <= best_sector_times[idx]:
        best_sector_times[idx] = time_s
        color = COLOR_PURPLE
        delta = time_s - best_sector_times[idx]
    else:
        prev = prev_lap_sector_times[idx]
        if prev is not None and time_s < prev:
            color = COLOR_GREEN
            delta = time_s - best_sector_times[idx]
        else:
            color = COLOR_RED
            delta = time_s - best_sector_times[idx]

    sector_results[idx] = (color, format_delta(delta))


def on_lap_complete():
    global prev_lap_sector_times, current_lap_sector_times, sector_results, flash_timer
    prev_lap_sector_times = list(current_lap_sector_times)
    current_lap_sector_times = [None, None, None]
    sector_results = [None, None, None]
    flash_timer = flash_duration


def draw_rect(x, y, w, h, color):
    ac.glColor4f(color[0], color[1], color[2], color[3])
    ac.glBegin(acsys.GL.Quads)
    ac.glVertex2f(x, y)
    ac.glVertex2f(x + w, y)
    ac.glVertex2f(x + w, y + h)
    ac.glVertex2f(x, y + h)
    ac.glEnd()


def render(deltaT):
    global flash_timer
    x, y, w, h = bar_rect

    # base background
    draw_rect(0, 0, w, h, BACKGROUND)

    # completed sectors
    for i in range(3):
        if sector_results[i] is None:
            continue
        sx, ex = get_sector_bounds(i)
        color, _ = sector_results[i]
        draw_rect(int(w * sx), 0, int(w * (ex - sx)), h, color)

    # progress overlay (current sector)
    if current_sector in [0, 1, 2]:
        sx, ex = get_sector_bounds(current_sector)
        start = sx
        end = ex
        if end - start > 0.0001:
            norm = ac.getCarState(0, acsys.CS.NormalizedCarPosition)
            p = (norm - start) / (end - start)
            p = clamp(p, 0.0, 1.0)
            draw_rect(int(w * start), 0, int(w * (end - start) * p), h, PROGRESS_COLOR)

    # flash at lap end
    if flash_timer > 0:
        alpha = clamp(flash_timer / flash_duration, 0.0, 1.0)
        draw_rect(0, 0, w, h, (FLASH_COLOR[0], FLASH_COLOR[1], FLASH_COLOR[2], FLASH_COLOR[3] * alpha))
        flash_timer -= deltaT


def acMain(ac_version):
    global app, labels
    app = ac.newApp(APP_NAME)
    ac.setTitle(app, "")
    ac.drawBorder(app, 0)
    ac.setBackgroundOpacity(app, 0)

    update_geometry()

    # labels
    for i in range(3):
        labels[i] = ac.addLabel(app, "")
        ac.setFontSize(labels[i], 10)
        ac.setPosition(labels[i], 10, 0)

    ac.addRenderCallback(app, render)
    return APP_NAME


def acUpdate(deltaT):
    global last_norm, current_sector

    update_geometry()

    norm = ac.getCarState(0, acsys.CS.NormalizedCarPosition)
    sector = int(ac.getCarState(0, acsys.CS.Sector))

    # Lap completed when normalized position wraps
    if norm < last_norm - 0.5:
        on_lap_complete()

    # Sector change
    if sector != current_sector:
        # register boundary based on the sector just finished
        register_sector_boundary(current_sector, norm)

        # sector time for the sector just finished
        try:
            last_sector_time = ac.getCarState(0, acsys.CS.LastSectorTime)
        except Exception:
            last_sector_time = None

        if last_sector_time is not None and last_sector_time > 0:
            on_sector_complete(current_sector, last_sector_time)

        current_sector = sector

    # update labels
    for i in range(3):
        if sector_results[i] is None:
            ac.setText(labels[i], "")
        else:
            color, text = sector_results[i]
            ac.setText(labels[i], text)
            ac.setFontColor(labels[i], color[0], color[1], color[2], 1)

    last_norm = norm
