import pygame
import json
import os
import math
import array

# --- звук: инициализируем микшер ДО pygame.init() ---
sound_ok = False
try:
    pygame.mixer.pre_init(44100, -16, 1, 512)
except Exception:
    pass
pygame.init()
try:
    pygame.mixer.init()
    sound_ok = pygame.mixer.get_init() is not None
except Exception:
    sound_ok = False

# --- Настройки ---
WIDTH, HEIGHT = 1000, 600
GRID = 40
FPS = 60
SPEED = 6
LEVEL_FILE = "level.json"
VERSION = "Beta 1.4"
TITLE = "Vithel Dash Redactor"
AUTHOR = "Vithel"
TIKTOK = "@vithel_tt"
MADE_WITH = "Claude Opus 4.8"

GRAVITY = 0.9
JUMP_FORCE = -14
SHIP_LIFT = 0.62
SHIP_GRAV = 0.34
SHIP_MAX_V = 8
UFO_GRAV = 0.5
UFO_FLAP = -9.5

BG        = (30, 30, 40)
GRID_COL  = (55, 55, 70)
BLOCK_C   = (200, 200, 210)
SPIKE_C   = (240, 80, 80)
GOAL_C    = (100, 240, 120)
TEXT_C    = (230, 230, 230)
HBOX_C    = (200, 220, 255)
LINE_C    = (80, 240, 120)
SEL_C     = (80, 240, 120)

P_COL = {
    "p_cube": (120, 200, 255),
    "p_ship": (255, 170, 60),
    "p_wave": (220, 100, 240),
    "p_ufo":  (90, 235, 210),
}
P_LETTER = {"p_cube": "C", "p_ship": "S", "p_wave": "W", "p_ufo": "U"}
P_MODE   = {"p_cube": "cube", "p_ship": "ship", "p_wave": "wave", "p_ufo": "ufo"}

COLOR_GROUPS = [
    ("Default", None), ("Red", (240, 70, 70)), ("Orange", (255, 150, 50)),
    ("Yellow", (250, 220, 70)), ("Green", (90, 220, 110)), ("Cyan", (70, 200, 230)),
    ("Blue", (80, 140, 255)), ("Purple", (180, 110, 240)), ("Pink", (240, 110, 200)),
    ("White", (240, 240, 245)),
]

SPEED_LEVELS = [
    {"mult": 0.6, "col": (255, 150, 60),  "arrows": 1, "dir": -1},
    {"mult": 1.0, "col": (90, 180, 255),  "arrows": 1, "dir": 1},
    {"mult": 1.3, "col": (110, 230, 120), "arrows": 2, "dir": 1},
    {"mult": 1.6, "col": (240, 110, 220), "arrows": 3, "dir": 1},
    {"mult": 1.9, "col": (240, 70, 70),   "arrows": 4, "dir": 1},
]

SKINS = [
    ("Cyan", (60, 200, 255)), ("Lime", (120, 240, 120)), ("Magenta", (240, 90, 220)),
    ("Orange", (255, 160, 50)), ("Yellow", (250, 230, 70)), ("Red", (240, 70, 70)),
    ("White", (240, 240, 245)), ("Violet", (150, 110, 250)),
]
skin_index = 0

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 22)
big_font = pygame.font.SysFont("consolas", 44)
small_font = pygame.font.SysFont("consolas", 17)
tiny_font = pygame.font.SysFont("consolas", 14)
micro_font = pygame.font.SysFont("consolas", 12)

# --- генерация звуков без файлов ---
SND = {}
def build_sounds():
    if not sound_ok:
        return
    rate, fmt, ch = pygame.mixer.get_init()
    def tone(frq, ms, vol, wave="square", slide=0):
        n = int(rate * ms / 1000)
        buf = array.array("h")
        amp = int(32767 * vol)
        for i in range(n):
            f = frq + slide * (i / n)
            ph = (f * (i / rate)) % 1.0
            if wave == "square":
                s = amp if ph < 0.5 else -amp
            elif wave == "saw":
                s = int(amp * (2 * ph - 1))
            else:
                s = int(amp * math.sin(2 * math.pi * ph))
            env = 1.0
            if i < 0.02 * n:
                env = i / (0.02 * n)
            elif i > 0.7 * n:
                env = max(0.0, (n - i) / (0.3 * n))
            val = int(s * env)
            for _ in range(ch):
                buf.append(val)
        return pygame.mixer.Sound(buffer=buf.tobytes())
    try:
        SND["jump"]   = tone(680, 90, 0.35, "square")
        SND["flap"]   = tone(520, 110, 0.30, "sine")
        SND["portal"] = tone(760, 150, 0.32, "sine", slide=260)
        SND["death"]  = tone(220, 260, 0.35, "saw", slide=-130)
        SND["win"]    = tone(880, 380, 0.32, "sine", slide=200)
        SND["click"]  = tone(600, 45, 0.25, "square")
    except Exception:
        SND.clear()

def snd(name):
    s = SND.get(name)
    if s:
        try:
            s.play()
        except Exception:
            pass

build_sounds()

level = []

PALETTE = [
    ("block", "1"), ("spike", "2"), ("slope", "3"), ("goal", "4"),
    ("p_cube", "5"), ("p_ship", "6"), ("p_wave", "7"), ("p_ufo", "8"),
    ("speed", "9"), ("mtrig", "0"), ("startpos", "T"), ("hbox", "H"),
]
BRUSH_NAMES = {
    "block": "блок", "spike": "шип", "slope": "склон", "goal": "финиш",
    "p_cube": "портал КУБ", "p_ship": "портал КОРАБЛЬ", "p_wave": "портал ВОЛНА",
    "p_ufo": "портал НЛО", "speed": "скорость", "mtrig": "Move-триггер",
    "startpos": "StartPos", "hbox": "H-блок",
}
MOVABLE_TYPES = {"block", "spike", "slope", "hbox", "goal", "speed"} | set(P_COL)

PAL_X0, PAL_Y0, TILE, GAP = 10, 50, 40, 6


def palette_rects():
    out = []
    for i, (k, lab) in enumerate(PALETTE):
        rx = PAL_X0 + i * (TILE + GAP)
        out.append((pygame.Rect(rx, PAL_Y0, TILE, TILE), k, lab, i))
    return out


def palette_bbox():
    w = len(PALETTE) * (TILE + GAP) - GAP
    return pygame.Rect(PAL_X0, PAL_Y0, w, TILE)


# ---------------- Сохранение / загрузка ----------------
def save_level():
    with open(LEVEL_FILE, "w") as f:
        json.dump(level, f)
    print("Уровень сохранён")


def normalize(o):
    if isinstance(o, list):
        return {"x": o[0], "y": o[1], "t": o[2], "c": 0, "grp": 0}
    o.setdefault("c", 0)
    o.setdefault("grp", 0)
    if o.get("t") == "p_bounce":
        o["t"] = "p_ufo"
    if o.get("t") == "startpos" and o.get("mode") == "bounce":
        o["mode"] = "ufo"
    if o.get("t") == "spike":
        o.setdefault("rot", "up")
    if o.get("t") == "slope":
        o.setdefault("rot", "right")
    if o.get("t") in P_COL:
        o.setdefault("rot", "vert")
    return o


def load_level():
    global level
    if os.path.exists(LEVEL_FILE):
        with open(LEVEL_FILE) as f:
            level = [normalize(o) for o in json.load(f)]
        print("Уровень загружен")
    else:
        print("Файл уровня не найден")


# ---------------- Геометрия / цвета ----------------
def rect_of(o, off=(0, 0)):
    return pygame.Rect(o["x"] * GRID + off[0], o["y"] * GRID + off[1], GRID, GRID)


def portal_rect(o, off=(0, 0)):
    x = o["x"] * GRID + off[0]
    y = o["y"] * GRID + off[1]
    if o.get("rot") == "horiz":
        return pygame.Rect(x - GRID // 2, y, GRID * 2, GRID)
    return pygame.Rect(x, y - GRID, GRID, GRID * 2)


def obj_color(o, default):
    idx = o.get("c", 0)
    if 0 < idx < len(COLOR_GROUPS):
        return COLOR_GROUPS[idx][1]
    return default


SPIKE_ROT_K = {"up": 0, "right": 1, "down": 2, "left": 3}


def rot_pts(pts, cx, cy, k):
    out = []
    for px, py in pts:
        dx, dy = px - cx, py - cy
        for _ in range(k % 4):
            dx, dy = -dy, dx
        out.append((cx + dx, cy + dy))
    return out


def slope_pts(x, y, d):
    # right  — подъём вправо (пол)
    # left   — подъём влево  (пол)
    # tright — перевёрнутый вправо (потолок)
    # tleft  — перевёрнутый влево  (потолок)
    if d == "left":
        return [(x, y + GRID), (x + GRID, y + GRID), (x, y)]
    if d == "tright":
        return [(x, y), (x + GRID, y), (x + GRID, y + GRID)]
    if d == "tleft":
        return [(x, y), (x + GRID, y), (x, y + GRID)]
    return [(x, y + GRID), (x + GRID, y + GRID), (x + GRID, y)]  # right


def draw_chevrons(surf, cx, cy, n, direction, col):
    step = 9
    total = (n - 1) * step
    for i in range(n):
        ox = cx - total // 2 + i * step
        if direction > 0:
            pts = [(ox - 5, cy - 9), (ox + 5, cy), (ox - 5, cy + 9)]
        else:
            pts = [(ox + 5, cy - 9), (ox - 5, cy), (ox + 5, cy + 9)]
        pygame.draw.lines(surf, col, False, pts, 3)


def draw_object(surf, o, cam_x, editor_mode, off=(0, 0)):
    kind = o["t"]
    x = o["x"] * GRID - cam_x + off[0]
    y = o["y"] * GRID + off[1]
    if x < -GRID * 2 or x > WIDTH + GRID:
        return

    if kind == "block":
        pygame.draw.rect(surf, obj_color(o, BLOCK_C), (x, y, GRID, GRID))
        pygame.draw.rect(surf, (60, 60, 70), (x, y, GRID, GRID), 2)
        if editor_mode and o.get("grp", 0):
            surf.blit(tiny_font.render(str(o["grp"]), True, (20, 20, 30)), (x + 3, y + 3))
    elif kind == "spike":
        base = [(x, y + GRID), (x + GRID // 2, y), (x + GRID, y + GRID)]
        pts = rot_pts(base, x + GRID // 2, y + GRID // 2, SPIKE_ROT_K.get(o.get("rot", "up"), 0))
        pygame.draw.polygon(surf, obj_color(o, SPIKE_C), pts)
        if editor_mode and o.get("grp", 0):
            surf.blit(tiny_font.render(str(o["grp"]), True, (255, 255, 255)),
                      (x + GRID // 2 - 5, y + GRID - 16))
    elif kind == "slope":
        d = o.get("rot", "right")
        pygame.draw.polygon(surf, obj_color(o, BLOCK_C), slope_pts(x, y, d))
        pygame.draw.polygon(surf, (60, 60, 70), slope_pts(x, y, d), 2)
        if editor_mode and o.get("grp", 0):
            surf.blit(tiny_font.render(str(o["grp"]), True, (20, 20, 30)), (x + 3, y + GRID - 16))
    elif kind == "goal":
        pygame.draw.rect(surf, GOAL_C, (x, y, GRID, GRID))
        pygame.draw.rect(surf, (255, 255, 255), (x, y, GRID, GRID), 3)
    elif kind in P_COL:
        col = P_COL[kind]
        if o.get("rot") == "horiz":
            rect = pygame.Rect(x - GRID // 2, y + 6, GRID * 2, GRID - 12)
        else:
            rect = pygame.Rect(x + 6, y - GRID, GRID - 12, GRID * 2)
        pygame.draw.rect(surf, col, rect, border_radius=10)
        pygame.draw.rect(surf, (255, 255, 255), rect, 2, border_radius=10)
        t = font.render(P_LETTER[kind], True, (20, 20, 30))
        surf.blit(t, t.get_rect(center=(x + GRID // 2, y + GRID // 2)))
        if editor_mode and o.get("grp", 0):
            surf.blit(tiny_font.render(str(o["grp"]), True, (255, 255, 255)),
                      (rect.x + 3, rect.y + 2))
    elif kind == "speed":
        lvl = SPEED_LEVELS[o.get("lvl", 1)]
        pygame.draw.rect(surf, lvl["col"], (x + 8, y - GRID + 4, GRID - 16, GRID * 2 - 8), border_radius=8)
        pygame.draw.rect(surf, (255, 255, 255), (x + 8, y - GRID + 4, GRID - 16, GRID * 2 - 8), 2, border_radius=8)
        draw_chevrons(surf, x + GRID // 2, y + GRID // 2, lvl["arrows"], lvl["dir"], (255, 255, 255))
        if editor_mode and o.get("grp", 0):
            surf.blit(tiny_font.render(str(o["grp"]), True, (255, 255, 255)), (x + 10, y - GRID + 6))
    elif kind == "mtrig":
        if editor_mode:
            pygame.draw.line(surf, LINE_C, (x + GRID // 2, 0), (x + GRID // 2, HEIGHT), 1)
            pygame.draw.circle(surf, (240, 90, 200), (x + GRID // 2, y + GRID // 2), GRID // 2 - 2)
            pygame.draw.circle(surf, (255, 255, 255), (x + GRID // 2, y + GRID // 2), GRID // 2 - 2, 2)
            t = small_font.render(str(o.get("grp", 0)), True, (20, 20, 30))
            surf.blit(t, t.get_rect(center=(x + GRID // 2, y + GRID // 2)))
    elif kind == "startpos":
        if editor_mode:
            pygame.draw.rect(surf, (90, 240, 120), (x, y, GRID, GRID), 3)
            surf.blit(small_font.render("S", True, (90, 240, 120)), (x + 4, y + 3))
            surf.blit(tiny_font.render(o.get("mode", "cube")[:4], True, (200, 230, 200)), (x + 2, y + GRID - 16))
    elif kind == "hbox":
        if editor_mode:
            pygame.draw.rect(surf, (110, 110, 130), (x, y, GRID, GRID), 1)
            s = 7
            for cx, cy in [(x, y), (x + GRID - s, y), (x, y + GRID - s), (x + GRID - s, y + GRID - s)]:
                pygame.draw.rect(surf, HBOX_C, (cx, cy, s, s))


# ---------------- Иконки палитры / справочника ----------------
def draw_palette_icon(surf, kind, r):
    x, y, g = r.x, r.y, TILE
    cx, cy = r.centerx, r.centery
    if kind == "block":
        pygame.draw.rect(surf, BLOCK_C, (x + 8, y + 8, g - 16, g - 16))
    elif kind == "spike":
        pygame.draw.polygon(surf, SPIKE_C, [(x + 8, y + g - 8), (cx, y + 8), (x + g - 8, y + g - 8)])
    elif kind == "slope":
        pygame.draw.polygon(surf, BLOCK_C, [(x + 8, y + g - 8), (x + g - 8, y + g - 8), (x + g - 8, y + 8)])
    elif kind == "goal":
        pygame.draw.rect(surf, GOAL_C, (x + 8, y + 8, g - 16, g - 16))
        pygame.draw.rect(surf, (255, 255, 255), (x + 8, y + 8, g - 16, g - 16), 2)
    elif kind in P_COL:
        pygame.draw.rect(surf, P_COL[kind], (x + 11, y + 6, g - 22, g - 12), border_radius=6)
        t = tiny_font.render(P_LETTER[kind], True, (20, 20, 30))
        surf.blit(t, t.get_rect(center=(cx, cy + 1)))
    elif kind == "speed":
        lvl = SPEED_LEVELS[1]
        pygame.draw.rect(surf, lvl["col"], (x + 10, y + 8, g - 20, g - 16), border_radius=5)
        draw_chevrons(surf, cx, cy, 2, 1, (255, 255, 255))
    elif kind == "mtrig":
        pygame.draw.circle(surf, (240, 90, 200), (cx, cy), 11)
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 11, 2)
    elif kind == "startpos":
        pygame.draw.rect(surf, (90, 240, 120), (x + 8, y + 8, g - 16, g - 16), 2)
        t = tiny_font.render("St", True, (90, 240, 120))
        surf.blit(t, t.get_rect(center=(cx, cy)))
    elif kind == "hbox":
        pygame.draw.rect(surf, (110, 110, 130), (x + 8, y + 8, g - 16, g - 16), 1)
        s = 5
        for px, py in [(x + 8, y + 8), (x + g - 8 - s, y + 8),
                       (x + 8, y + g - 8 - s), (x + g - 8 - s, y + g - 8 - s)]:
            pygame.draw.rect(surf, HBOX_C, (px, py, s, s))


def draw_palette(bi):
    for r, k, lab, i in palette_rects():
        pygame.draw.rect(screen, (44, 44, 58), r, border_radius=7)
        draw_palette_icon(screen, k, r)
        if bi == i:
            pygame.draw.rect(screen, SEL_C, r, 3, border_radius=7)
        else:
            pygame.draw.rect(screen, (72, 72, 92), r, 1, border_radius=7)
        badge = micro_font.render(lab, True, (255, 255, 255))
        bx, by = r.x + 2, r.y + 1
        pygame.draw.rect(screen, (20, 20, 28), (bx, by, badge.get_width() + 4, 14))
        screen.blit(badge, (bx + 2, by))


# ---------------- Настройки объекта (панель по E) ----------------
def get_spec(o):
    t = o["t"]
    speed_names = ["x" + str(s["mult"]) for s in SPEED_LEVELS]
    grp_field = {"key": "grp", "label": "Группа (Move)", "kind": "int", "min": 0, "max": 999, "step": 1}
    if t == "block":
        return [
            {"key": "c", "label": "Цвет", "kind": "index", "names": [n for n, _ in COLOR_GROUPS]},
            grp_field,
        ]
    if t == "spike":
        return [
            {"key": "c", "label": "Цвет", "kind": "index", "names": [n for n, _ in COLOR_GROUPS]},
            {"key": "rot", "label": "Поворот", "kind": "cycle", "values": ["up", "right", "down", "left"]},
            grp_field,
        ]
    if t == "slope":
        return [
            {"key": "c", "label": "Цвет", "kind": "index", "names": [n for n, _ in COLOR_GROUPS]},
            {"key": "rot", "label": "Поворот", "kind": "cycle", "values": ["right", "left", "tright", "tleft"]},
            grp_field,
        ]
    if t == "goal":
        return [grp_field]
    if t in P_COL:
        return [
            {"key": "rot", "label": "Ориентация", "kind": "cycle", "values": ["vert", "horiz"]},
            grp_field,
        ]
    if t == "mtrig":
        return [
            {"key": "grp", "label": "Группа", "kind": "int", "min": 1, "max": 999, "step": 1},
            {"key": "dx", "label": "Сдвиг X (клетки)", "kind": "int", "min": -15, "max": 15, "step": 1},
            {"key": "dy", "label": "Сдвиг Y (клетки)", "kind": "int", "min": -15, "max": 15, "step": 1},
            {"key": "dur", "label": "Длительность (кадры)", "kind": "int", "min": 5, "max": 180, "step": 5},
            {"key": "easing", "label": "Тип движения", "kind": "cycle", "values": ["smooth", "sharp"]},
        ]
    if t == "speed":
        return [
            {"key": "lvl", "label": "Скорость", "kind": "index", "names": speed_names},
            grp_field,
        ]
    if t == "startpos":
        return [
            {"key": "mode", "label": "Стартовый режим", "kind": "cycle", "values": ["cube", "ship", "wave", "ufo"]},
            {"key": "lvl", "label": "Стартовая скорость", "kind": "index", "names": speed_names},
        ]
    return []


def field_default(f):
    if f["kind"] == "int":
        return f["min"]
    if f["kind"] == "index":
        return 0
    return f["values"][0]


def field_display(o, f):
    v = o.get(f["key"])
    if f["kind"] == "index":
        v = int(v or 0)
        return f["names"][v] if 0 <= v < len(f["names"]) else str(v)
    return str(v)


def field_adjust(o, f, d):
    if f["kind"] == "int":
        v = int(o.get(f["key"], f["min"])) + d * f["step"]
        o[f["key"]] = max(f["min"], min(f["max"], v))
    elif f["kind"] == "index":
        n = len(f["names"])
        o[f["key"]] = (int(o.get(f["key"], 0)) + d) % n
    elif f["kind"] == "cycle":
        vals = f["values"]
        cur = o.get(f["key"], vals[0])
        i = vals.index(cur) if cur in vals else 0
        o[f["key"]] = vals[(i + d) % len(vals)]


def wheel_delta(e):
    if e.type == pygame.MOUSEWHEEL:
        return e.y
    return 0


def edit_object_settings(o, cam_x):
    spec = get_spec(o)
    for f in spec:
        o.setdefault(f["key"], field_default(f))
    sel = 0
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            w = wheel_delta(e)
            if w and spec:
                field_adjust(o, spec[sel], w)
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_e, pygame.K_RETURN):
                    return None
                if e.key == pygame.K_w:
                    sel = (sel - 1) % max(1, len(spec))
                if e.key == pygame.K_s:
                    sel = (sel + 1) % max(1, len(spec))
                if e.key == pygame.K_a and spec:
                    field_adjust(o, spec[sel], -1)
                if e.key == pygame.K_d and spec:
                    field_adjust(o, spec[sel], 1)

        screen.fill(BG)
        for oo in level:
            draw_object(screen, oo, cam_x, editor_mode=True)
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        screen.blit(dim, (0, 0))

        pw, ph = 540, 92 + max(1, len(spec)) * 40
        pxp, pyp = (WIDTH - pw) // 2, (HEIGHT - ph) // 2
        pygame.draw.rect(screen, (40, 40, 55), (pxp, pyp, pw, ph), border_radius=12)
        pygame.draw.rect(screen, (90, 90, 120), (pxp, pyp, pw, ph), 2, border_radius=12)
        screen.blit(font.render("Настройки: " + BRUSH_NAMES.get(o["t"], o["t"]), True, TEXT_C),
                    (pxp + 16, pyp + 12))

        if not spec:
            screen.blit(small_font.render("У этого объекта нет параметров.", True, (180, 180, 190)),
                        (pxp + 16, pyp + 50))
        for i, f in enumerate(spec):
            yy = pyp + 50 + i * 40
            active = (i == sel)
            if active:
                pygame.draw.rect(screen, (60, 60, 85), (pxp + 10, yy - 4, pw - 20, 34), border_radius=6)
            screen.blit(small_font.render(f["label"], True, (200, 200, 210)), (pxp + 20, yy))
            val = field_display(o, f)
            vs = font.render("< " + val + " >" if active else val, True,
                             (255, 230, 120) if active else (200, 200, 210))
            screen.blit(vs, (pxp + pw - 20 - vs.get_width(), yy - 2))

        screen.blit(tiny_font.render("W/S выбрать · A/D или колесо менять · E или ESC закрыть",
                                     True, (160, 160, 175)), (pxp + 16, pyp + ph - 26))
        pygame.display.flip()


def confirm_dialog(text, cam_x):
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_y:
                    return True
                if e.key in (pygame.K_n, pygame.K_ESCAPE):
                    return False
        screen.fill(BG)
        for oo in level:
            draw_object(screen, oo, cam_x, editor_mode=True)
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 165))
        screen.blit(dim, (0, 0))
        pw, ph = 480, 150
        pxp, pyp = (WIDTH - pw) // 2, (HEIGHT - ph) // 2
        pygame.draw.rect(screen, (52, 40, 45), (pxp, pyp, pw, ph), border_radius=12)
        pygame.draw.rect(screen, (210, 90, 90), (pxp, pyp, pw, ph), 2, border_radius=12)
        t1 = font.render(text, True, (255, 220, 220))
        screen.blit(t1, t1.get_rect(center=(WIDTH // 2, pyp + 48)))
        t2 = small_font.render("Y — да, стереть ВСЁ     N / ESC — отмена", True, TEXT_C)
        screen.blit(t2, t2.get_rect(center=(WIDTH // 2, pyp + 100)))
        pygame.display.flip()


def draw_pill(x, y, label, value, accent):
    lab = tiny_font.render(label, True, (150, 150, 165))
    val = small_font.render(value, True, accent)
    w = max(lab.get_width(), val.get_width()) + 18
    pygame.draw.rect(screen, (44, 44, 58), (x, y, w, 42), border_radius=8)
    pygame.draw.rect(screen, (72, 72, 92), (x, y, w, 42), 1, border_radius=8)
    screen.blit(lab, (x + 9, y + 4))
    screen.blit(val, (x + 9, y + 20))
    return w


# ---------------- Редактор ----------------
def editor():
    cam_x = 0
    bi = 0
    cur_color = 0
    cur_group = 0
    cur_speed = 1
    cur_start_mode = "cube"

    key_to_idx = {}
    for idx, (k, lab) in enumerate(PALETTE):
        if lab.isdigit():
            key_to_idx[getattr(pygame, "K_" + lab)] = idx
    key_to_idx[pygame.K_t] = next(i for i, (k, _) in enumerate(PALETTE) if k == "startpos")
    key_to_idx[pygame.K_h] = next(i for i, (k, _) in enumerate(PALETTE) if k == "hbox")

    while True:
        clock.tick(FPS)
        mx, my = pygame.mouse.get_pos()
        gx = int((mx + cam_x) // GRID)
        gy = int(my // GRID)
        kind = PALETTE[bi][0] if bi is not None else None
        over_pal = palette_bbox().collidepoint(mx, my)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); return "quit"

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and over_pal:
                for r, k, lab, i in palette_rects():
                    if r.collidepoint(mx, my):
                        bi = None if bi == i else i
                        snd("click")
                        break

            w = wheel_delta(e)
            if w and kind is not None:
                if kind in ("speed", "startpos"):
                    cur_speed = (cur_speed + w) % len(SPEED_LEVELS)
                elif kind in ("block", "spike", "slope"):
                    cur_color = (cur_color + w) % len(COLOR_GROUPS)
                else:
                    bi = (bi + w) % len(PALETTE)

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return "menu"
                if e.key in key_to_idx:
                    bi = key_to_idx[e.key]
                if e.key == pygame.K_LEFTBRACKET:
                    cur_color = (cur_color - 1) % len(COLOR_GROUPS)
                if e.key == pygame.K_RIGHTBRACKET:
                    cur_color = (cur_color + 1) % len(COLOR_GROUPS)
                if e.key == pygame.K_MINUS:
                    cur_group = max(0, cur_group - 1)       # без закольцовки → не прыгает на 999
                if e.key == pygame.K_EQUALS:
                    cur_group = min(999, cur_group + 1)
                if e.key == pygame.K_COMMA:
                    cur_speed = (cur_speed - 1) % len(SPEED_LEVELS)
                if e.key == pygame.K_PERIOD:
                    cur_speed = (cur_speed + 1) % len(SPEED_LEVELS)
                if e.key == pygame.K_m:
                    order = ["cube", "ship", "wave", "ufo"]
                    cur_start_mode = order[(order.index(cur_start_mode) + 1) % len(order)]
                if e.key == pygame.K_r:
                    for o in level:
                        if o["x"] == gx and o["y"] == gy:
                            sp = get_spec(o)
                            rf = next((f for f in sp if f["key"] == "rot"), None)
                            if rf:
                                o.setdefault("rot", rf["values"][0])
                                field_adjust(o, rf, 1)
                                break
                if e.key == pygame.K_e:
                    cands = [o for o in level if o["x"] == gx and o["y"] == gy and get_spec(o)]
                    if cands:
                        if edit_object_settings(cands[-1], cam_x) == "quit":
                            pygame.quit(); return "quit"
                if e.key == pygame.K_s: save_level()
                if e.key == pygame.K_l: load_level()
                if e.key == pygame.K_p: return "play"
                if e.key == pygame.K_c:
                    res = confirm_dialog("Очистить весь уровень?", cam_x)
                    if res == "quit":
                        pygame.quit(); return "quit"
                    if res:
                        level.clear()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]: cam_x = max(0, cam_x - SPEED * 2)
        if keys[pygame.K_d]: cam_x += SPEED * 2

        mb = pygame.mouse.get_pressed()
        if mb[0] and kind is not None and not over_pal:
            if kind == "hbox":
                level[:] = [o for o in level if not (o["x"] == gx and o["y"] == gy and o["t"] == "hbox")]
                level.append({"x": gx, "y": gy, "t": "hbox", "c": 0, "grp": 0})
            elif kind == "startpos":
                level[:] = [o for o in level if o["t"] != "startpos"]
                level.append({"x": gx, "y": gy, "t": "startpos", "c": 0, "grp": 0,
                              "mode": cur_start_mode, "lvl": cur_speed})
            else:
                level[:] = [o for o in level if not (o["x"] == gx and o["y"] == gy and o["t"] != "hbox")]
                obj = {"x": gx, "y": gy, "t": kind, "c": cur_color, "grp": cur_group}
                if kind == "speed":
                    obj["lvl"] = cur_speed
                if kind == "spike":
                    obj["rot"] = "up"
                if kind == "slope":
                    obj["rot"] = "right"
                if kind in P_COL:
                    obj["rot"] = "vert"
                if kind == "mtrig":
                    obj.update({"dx": 0, "dy": -3, "dur": 30, "easing": "smooth"})
                level.append(obj)
        if mb[2] and not over_pal:
            level[:] = [o for o in level if not (o["x"] == gx and o["y"] == gy)]

        # --- рисуем ---
        screen.fill(BG)
        grid_off = cam_x % GRID
        for x in range(-1, WIDTH // GRID + 2):
            pygame.draw.line(screen, GRID_COL, (x * GRID - grid_off, 0), (x * GRID - grid_off, HEIGHT))
        for y in range(HEIGHT // GRID + 1):
            pygame.draw.line(screen, GRID_COL, (0, y * GRID), (WIDTH, y * GRID))

        for o in level:
            draw_object(screen, o, cam_x, editor_mode=True)

        if kind is not None and not over_pal:
            prot = "up" if kind == "spike" else ("vert" if kind in P_COL else "right")
            preview = {"x": gx, "y": gy, "t": kind, "c": cur_color, "grp": cur_group,
                       "lvl": cur_speed, "mode": cur_start_mode, "rot": prot}
            draw_object(screen, preview, cam_x, editor_mode=True)
            pygame.draw.rect(screen, (255, 255, 0), (gx * GRID - cam_x, gy * GRID, GRID, GRID), 2)

        screen.blit(small_font.render(f"{TITLE}   {VERSION}   —   РЕДАКТОР", True, TEXT_C), (10, 8))
        screen.blit(tiny_font.render(
            "ЛКМ ставить · ПКМ удалять · A/D камера · E настройки · R повернуть · S сохр · L загр · C стереть · P играть · ESC",
            True, (170, 170, 185)), (10, 28))
        draw_palette(bi)

        if kind is None:
            draw_pill(10, HEIGHT - 50, "Кисть", "не выбрана", (200, 200, 205))
        else:
            accent = P_COL.get(kind, SPEED_LEVELS[cur_speed]["col"] if kind == "speed" else (230, 230, 235))
            pills = [("Кисть", BRUSH_NAMES[kind], accent)]
            if kind in ("block", "spike", "slope"):
                pills.append(("Цвет [ ]", COLOR_GROUPS[cur_color][0],
                              COLOR_GROUPS[cur_color][1] or (200, 200, 210)))
                pills.append(("Группа - =", str(cur_group), (240, 110, 200)))
            if kind in ("spike", "slope"):
                pills.append(("Поворот", "R или E", (255, 220, 120)))
            if kind in P_COL:
                pills.append(("Группа - =", str(cur_group), (240, 110, 200)))
                pills.append(("Ориентация", "R или E", (255, 220, 120)))
            if kind == "speed":
                pills.append(("Скорость , . / колесо", "x" + str(SPEED_LEVELS[cur_speed]["mult"]),
                              SPEED_LEVELS[cur_speed]["col"]))
                pills.append(("Группа - =", str(cur_group), (240, 110, 200)))
            if kind == "mtrig":
                pills.append(("Группа - =", str(cur_group), (240, 110, 200)))
                pills.append(("Настрой", "жми E на нём", (255, 220, 120)))
            if kind == "startpos":
                pills.append(("Режим (m)", cur_start_mode, (120, 200, 255)))
                pills.append(("Скорость , .", "x" + str(SPEED_LEVELS[cur_speed]["mult"]),
                              SPEED_LEVELS[cur_speed]["col"]))
            px = 10
            for lab, val, acc in pills:
                px += draw_pill(px, HEIGHT - 50, lab, val, acc) + 8

        pygame.display.flip()


# ---------------- Игра ----------------
def ease(t, kind):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t) if kind == "smooth" else t


def play():
    px = 3 * GRID
    size = GRID - 6
    color = SKINS[skin_index][1]
    hcells = set((o["x"], o["y"]) for o in level if o["t"] == "hbox")

    ship_surf = pygame.Surface((size + 14, size), pygame.SRCALPHA)
    pygame.draw.rect(ship_surf, color, (0, 0, size, size), border_radius=8)
    pygame.draw.polygon(ship_surf, (255, 255, 255),
                        [(size, 4), (size + 12, size // 2), (size, size - 4)])

    cube_surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(cube_surf, color, (0, 0, size, size), border_radius=4)
    pygame.draw.rect(cube_surf, (255, 255, 255), (0, 0, size, size), 2, border_radius=4)

    st = {}
    def reset():
        sp = next((o for o in level if o["t"] == "startpos"), None)
        if sp:
            st["cam_x"] = float(sp["x"] * GRID - px)
            st["py"] = float(sp["y"] * GRID)
            st["mode"] = sp.get("mode", "cube")
            st["mult"] = SPEED_LEVELS[sp.get("lvl", 1)]["mult"]
        else:
            st["cam_x"] = 0.0
            st["py"] = float(HEIGHT - 5 * GRID)
            st["mode"] = "cube"
            st["mult"] = 1.0
        st["vy"] = 0.0
        st["dead"] = False
        st["won"] = False
        st["on_ground"] = False
        st["offsets"] = {}
        st["anims"] = []
        st["fired"] = set()
        st["cube_rot"] = 0.0
        st["spin"] = 0.0
        st["ground_slope"] = None
    reset()

    while True:
        clock.tick(FPS)
        flap = False
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); return "quit"
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return "menu"
                if e.key == pygame.K_r:
                    reset()
                if e.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    flap = True
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                flap = True

        keys = pygame.key.get_pressed()
        hold = (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
                or pygame.mouse.get_pressed()[0])

        if not st["dead"] and not st["won"]:
            was_dead, was_won, prev_mode = st["dead"], st["won"], st["mode"]
            cur_speed = SPEED * st["mult"]
            st["cam_x"] += cur_speed

            mode = st["mode"]
            vy = st["vy"]
            if mode == "cube":
                vy += GRAVITY
            elif mode == "ship":
                vy += (-SHIP_LIFT if hold else 0) + SHIP_GRAV
                vy = max(-SHIP_MAX_V, min(SHIP_MAX_V, vy))
            elif mode == "wave":
                vy = -cur_speed if hold else cur_speed
            elif mode == "ufo":
                vy += UFO_GRAV
                if flap:
                    vy = UFO_FLAP
                    snd("flap")
                vy = max(-13, min(14, vy))
            py = st["py"] + vy

            offsets = st["offsets"]
            for a in st["anims"][:]:
                a["f"] += 1
                p = ease(a["f"] / a["dur"], a["easing"])
                offsets[a["id"]] = [a["sx"] + (a["ex"] - a["sx"]) * p,
                                    a["sy"] + (a["ey"] - a["sy"]) * p]
                if a["f"] >= a["dur"]:
                    offsets[a["id"]] = [a["ex"], a["ey"]]
                    st["anims"].remove(a)

            world_x = px + st["cam_x"]
            pr = pygame.Rect(world_x, py, size, size)
            prev_bottom = st["py"] + size
            prev_top = st["py"]
            was_falling = vy > 0
            TOL = 6

            st["on_ground"] = False
            st["ground_slope"] = None
            for o in level:
                t = o["t"]
                ooff = offsets.get(id(o), (0, 0))
                if t in P_COL:
                    if pr.colliderect(portal_rect(o, ooff)):     # зона теперь едет за порталом
                        mode = P_MODE[t]; st["mode"] = mode
                    continue
                if t == "speed":
                    if pr.colliderect(portal_rect(o, ooff)):
                        st["mult"] = SPEED_LEVELS[o.get("lvl", 1)]["mult"]
                    continue
                if t == "mtrig":
                    line_x = o["x"] * GRID + GRID // 2
                    if world_x + size / 2 >= line_x and id(o) not in st["fired"]:
                        st["fired"].add(id(o))
                        grp = o.get("grp", 0)
                        if grp:
                            for tgt in level:
                                if tgt.get("grp", 0) == grp and tgt["t"] in MOVABLE_TYPES:
                                    base = offsets.get(id(tgt), [0, 0])
                                    st["anims"].append({
                                        "id": id(tgt), "f": 0, "dur": o.get("dur", 30),
                                        "easing": o.get("easing", "smooth"),
                                        "sx": base[0], "sy": base[1],
                                        "ex": base[0] + o.get("dx", 0) * GRID,
                                        "ey": base[1] + o.get("dy", 0) * GRID})
                    continue
                if t == "slope":
                    d = o.get("rot", "right")
                    if d in ("right", "left"):
                        left = o["x"] * GRID + ooff[0]
                        bottom = (o["y"] + 1) * GRID + ooff[1]
                        cxp = world_x + size / 2
                        lx = cxp - left
                        if 0 <= lx <= GRID and mode in ("cube", "ship", "ufo"):
                            surf_y = bottom - lx if d == "right" else bottom - (GRID - lx)
                            if py + size > surf_y and prev_bottom <= bottom + GRID:
                                py = surf_y - size; vy = 0
                                st["on_ground"] = True
                                st["ground_slope"] = d
                                pr.y = int(py)
                    else:  # перевёрнутый склон = сплошной блок
                        r = rect_of(o, ooff)
                        if pr.colliderect(r):
                            if mode == "wave":
                                st["dead"] = True
                            elif was_falling and prev_bottom <= r.top + TOL:
                                py = r.top - size; vy = 0; st["on_ground"] = True; pr.y = int(py)
                            elif (not was_falling) and prev_top >= r.bottom - TOL:
                                py = r.bottom; vy = 0; pr.y = int(py)
                            else:
                                st["dead"] = True
                    continue
                if t in ("startpos", "hbox"):
                    continue

                r = rect_of(o, ooff)
                if not pr.colliderect(r):
                    continue

                if t == "spike":
                    st["dead"] = True
                elif t == "goal":
                    st["won"] = True
                else:  # block
                    if mode == "wave":
                        if (o["x"], o["y"]) in hcells and was_falling and prev_bottom <= r.top + TOL:
                            py = r.top - size; vy = 0
                            st["on_ground"] = True; pr.y = int(py)
                        else:
                            st["dead"] = True
                    elif mode == "ship":
                        if prev_bottom <= r.top + TOL:
                            py = r.top - size; vy = 0
                            st["on_ground"] = True; pr.y = int(py)
                        elif prev_top >= r.bottom - TOL:
                            py = r.bottom; vy = 0; pr.y = int(py)
                        else:
                            st["dead"] = True
                    else:  # cube / ufo
                        if was_falling and prev_bottom <= r.top + TOL:
                            py = r.top - size; vy = 0
                            st["on_ground"] = True; pr.y = int(py)
                        elif (not was_falling) and prev_top >= r.bottom - TOL:
                            py = r.bottom; vy = 0; pr.y = int(py)
                        else:
                            ov = min(pr.right, r.right) - max(pr.left, r.left)
                            if ov > 6:
                                st["dead"] = True
                            else:
                                py = r.top - size; vy = 0
                                st["on_ground"] = True; pr.y = int(py)

            floor = HEIGHT - GRID
            if py + size >= floor:
                py = floor - size; vy = 0
                st["on_ground"] = True
            if py < 0:
                py = 0
                if vy < 0:
                    vy = 0

            if mode == "cube" and hold and st["on_ground"]:
                vy = JUMP_FORCE
                st["spin"] = -12.0
                snd("jump")

            if mode == "cube":
                if st["on_ground"] and vy >= 0:
                    st["cube_rot"] = 0.0
                    st["spin"] = 0.0
                else:
                    st["cube_rot"] += st["spin"]

            st["py"] = py; st["vy"] = vy

            if st["mode"] != prev_mode:
                snd("portal")
            if st["dead"] and not was_dead:
                snd("death")
            if st["won"] and not was_won:
                snd("win")

        # --- отрисовка ---
        screen.fill(BG)
        grid_off = st["cam_x"] % GRID
        for x in range(WIDTH // GRID + 2):
            pygame.draw.line(screen, GRID_COL, (x * GRID - grid_off, 0), (x * GRID - grid_off, HEIGHT))
        pygame.draw.rect(screen, (50, 50, 65), (0, HEIGHT - GRID, WIDTH, GRID))

        for o in level:
            draw_object(screen, o, st["cam_x"], editor_mode=False, off=st["offsets"].get(id(o), (0, 0)))

        py = st["py"]; vy = st["vy"]; mode = st["mode"]
        if mode == "cube":
            ang = st["cube_rot"]
            if st["ground_slope"]:
                ang += (-45 if st["ground_slope"] == "right" else 45)
            if abs(ang) < 0.5:
                screen.blit(cube_surf, (px, py))
            else:
                rot = pygame.transform.rotate(cube_surf, ang)
                screen.blit(rot, rot.get_rect(center=(px + size // 2, py + size // 2)))
        elif mode == "ship":
            angle = max(-32, min(32, -vy * 3))
            rot = pygame.transform.rotate(ship_surf, angle)
            screen.blit(rot, rot.get_rect(center=(px + size // 2, py + size // 2)))
        elif mode == "wave":
            if vy < 0:
                pts = [(px + size, py), (px, py + size * 0.55), (px + size * 0.55, py + size)]
            else:
                pts = [(px + size, py + size), (px, py + size * 0.45), (px + size * 0.55, py)]
            pygame.draw.polygon(screen, color, pts)
        elif mode == "ufo":
            body = pygame.Rect(px - 6, py + size * 0.4, size + 12, size * 0.45)
            pygame.draw.ellipse(screen, color, body)
            dome = pygame.Rect(px + size * 0.2, py + size * 0.02, size * 0.6, size * 0.55)
            pygame.draw.ellipse(screen, (255, 255, 255), dome)
            pygame.draw.ellipse(screen, color, dome, 2)

        mode_ru = {"cube": "КУБ", "ship": "КОРАБЛИК", "wave": "ВОЛНА", "ufo": "НЛО"}[mode]
        screen.blit(font.render(f"Режим: {mode_ru}   x{st['mult']}", True, TEXT_C), (10, 10))
        screen.blit(small_font.render("SPACE/W/ЛКМ действие · R заново · ESC меню", True, TEXT_C), (10, 40))

        if st["dead"]:
            m = big_font.render("Разбился! R — заново", True, SPIKE_C)
            screen.blit(m, m.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        if st["won"]:
            m = big_font.render("Уровень пройден!", True, GOAL_C)
            screen.blit(m, m.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

        pygame.display.flip()


# ---------------- Справочник ----------------
def help_screen():
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_i, pygame.K_RETURN):
                    return "menu"

        screen.fill(BG)
        title = big_font.render("СПРАВОЧНИК", True, SKINS[skin_index][1])
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 46)))

        # авторство
        credits = [
            (f"Игру сделал: {AUTHOR}", (255, 230, 120)),
            (f"Версия: {VERSION}", TEXT_C),
            (f"Создано при помощи нейросети: {MADE_WITH}", (150, 200, 255)),
            (f"TikTok: {TIKTOK}", (240, 110, 200)),
        ]
        yy = 92
        for txt, col in credits:
            screen.blit(font.render(txt, True, col), (60, yy))
            yy += 30

        pygame.draw.line(screen, (70, 70, 90), (60, yy + 6), (WIDTH - 60, yy + 6), 1)
        screen.blit(small_font.render("Блоки редактора:", True, TEXT_C), (60, yy + 16))

        # список блоков в 2 колонки: иконка + подпись
        start_y = yy + 44
        col_x = [70, 540]
        per_col = (len(PALETTE) + 1) // 2
        for idx, (k, lab) in enumerate(PALETTE):
            col = idx // per_col
            row = idx % per_col
            ix = col_x[col]
            iy = start_y + row * 46
            r = pygame.Rect(ix, iy, TILE, TILE)
            pygame.draw.rect(screen, (44, 44, 58), r, border_radius=7)
            draw_palette_icon(screen, k, r)
            pygame.draw.rect(screen, (72, 72, 92), r, 1, border_radius=7)
            screen.blit(small_font.render(f"{lab} — {BRUSH_NAMES[k]}", True, (210, 210, 220)),
                        (ix + TILE + 12, iy + 11))

        screen.blit(tiny_font.render("ESC / I / Enter — назад в меню", True, (160, 160, 175)),
                    (60, HEIGHT - 30))
        pygame.display.flip()


# ---------------- Меню ----------------
def menu():
    global skin_index
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_e: return "editor"
                if e.key == pygame.K_p:
                    load_level(); return "play"
                if e.key == pygame.K_i: return "help"
                if e.key == pygame.K_a:
                    skin_index = (skin_index - 1) % len(SKINS)
                if e.key == pygame.K_d:
                    skin_index = (skin_index + 1) % len(SKINS)
                if e.key == pygame.K_ESCAPE: return "quit"

        screen.fill(BG)
        title = big_font.render("VITHEL DASH REDACTOR", True, SKINS[skin_index][1])
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 110)))
        screen.blit(small_font.render(VERSION + ("  ♪" if sound_ok else "  (без звука)"), True, TEXT_C),
                    (WIDTH // 2 - 40, 148))
        for i, t in enumerate(["E — Редактор уровней", "P — Играть (level.json)",
                               "I — Справочник", "ESC — Выход"]):
            r = font.render(t, True, TEXT_C)
            screen.blit(r, r.get_rect(center=(WIDTH // 2, 220 + i * 38)))
        screen.blit(tiny_font.render(f"by {AUTHOR}  ·  {TIKTOK}  ·  нейросеть {MADE_WITH}",
                                     True, (150, 150, 165)),
                    (WIDTH // 2 - 220, 388))
        name, col = SKINS[skin_index]
        screen.blit(font.render("Скин (A / D):", True, TEXT_C), (WIDTH // 2 - 210, 430))
        pygame.draw.rect(screen, col, (WIDTH // 2 - 20, 422, 40, 40), border_radius=6)
        screen.blit(font.render(name, True, col), (WIDTH // 2 + 40, 430))
        pygame.display.flip()


# ---------------- Главный цикл ----------------
def main():
    load_level()
    state = "menu"
    while True:
        if state == "menu":
            state = menu()
        elif state == "editor":
            state = editor()
        elif state == "play":
            state = play()
        elif state == "help":
            state = help_screen()
        else:
            break
    pygame.quit()


if __name__ == "__main__":
    main()
