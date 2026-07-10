import pygame
import json
import os
import math
import array
import urllib.request
import urllib.error

# --- звук ---
sound_ok = False
try:
    pygame.mixer.pre_init(44100, -16, 2, 512)
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
LEVEL_SLOTS = 5
cur_slot = 1
LEGACY_LEVEL_FILE = "level.json"
CONFIG_FILE = "config.json"
SOUND_DIR = "Звуки"
AUDIO_EXTS = (".ogg", ".wav", ".mp3", ".flac")
VERSION = "Beta 1.6"
TITLE = "Vithel Dash Redactor"
AUTHOR = "Vithel"
TIKTOK = "@vithel_tt"
MADE_WITH = "Claude Opus 4.8"
SERVER_URL = "https://vithel-dash-redactor.vercel.app"  # сервер аккаунтов

GRAVITY = 0.9
JUMP_FORCE = -14
SHIP_LIFT = 0.5      # полегче: слабее тянет вверх
SHIP_GRAV = 0.26     # и слабее тянет вниз
SHIP_MAX_V = 6       # ограничение скорости — проще держать в воздухе
SHIP_ENTER_CLAMP = 4 # при входе в портал корабля скорость обрезается
UFO_GRAV = 0.5
UFO_FLAP = -9.5
MINI_SCALE = 0.62
TRAIL_LIFE = 16
DEATH_FRAMES = 30


def level_file():
    return f"level{cur_slot}.json"

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
    {"mult": 0.75, "col": (255, 170, 40),  "arrows": 1, "dir": -1},
    {"mult": 1.0,  "col": (60, 190, 255),  "arrows": 1, "dir": 1},
    {"mult": 1.25, "col": (80, 220, 80),   "arrows": 2, "dir": 1},
    {"mult": 1.5,  "col": (240, 120, 240), "arrows": 3, "dir": 1},
    {"mult": 1.75, "col": (230, 50, 50),   "arrows": 4, "dir": 1},
]

# --- сферы (orbs) ---
ORB_TYPES = ["yellow", "pink", "cyan", "green", "red", "black"]
ORB_COL = {
    "yellow": (250, 225, 70),
    "pink":   (245, 110, 205),
    "cyan":   (85, 230, 245),
    "green":  (95, 235, 110),
    "red":    (245, 90, 45),
    "black":  (35, 35, 42),
}
ORB_RU = {
    "yellow": "Жёлтая", "pink": "Розовая", "cyan": "Голубая",
    "green": "Зелёная", "red": "Красная", "black": "Чёрная",
}

# --- доп. порталы: гравитация и размер ---
XPORTAL_COL = {
    "p_gup":  (250, 215, 60),   # жёлтый — гравитация вверх
    "p_gdn":  (100, 210, 250),  # голубой — обычная гравитация
    "p_mini": (240, 105, 220),  # розовый — мини
    "p_big":  (105, 230, 105),  # зелёный — обычный размер
}
XPORTAL_RU = {
    "p_gup": "портал ГРАВИТАЦИЯ ВВЕРХ", "p_gdn": "портал ГРАВИТАЦИЯ ВНИЗ",
    "p_mini": "портал МИНИ", "p_big": "портал ОБЫЧНЫЙ РАЗМЕР",
}

SKINS = [
    ("Cyan", (60, 200, 255)), ("Lime", (120, 240, 120)), ("Magenta", (240, 90, 220)),
    ("Orange", (255, 160, 50)), ("Yellow", (250, 230, 70)), ("Red", (240, 70, 70)),
    ("White", (240, 240, 245)), ("Violet", (150, 110, 250)),
]
skin_index = 0

# перевод значений-циклов на русский (внутри остаются английские)
CYCLE_RU = {
    "up": "Вверх", "right": "Вправо", "down": "Вниз", "left": "Влево",
    "vert": "Вертикальный", "horiz": "Горизонтальный",
    "tright": "Потолок вправо", "tleft": "Потолок влево",
    "smooth": "Плавно", "sharp": "Резко",
    "cube": "Куб", "ship": "Кораблик", "wave": "Волна", "ufo": "НЛО",
}
SLOPE_RU = {"right": "Подъём вправо", "left": "Подъём влево",
            "tright": "Потолок вправо", "tleft": "Потолок влево"}

# реконфигурируемые клавиши
KEYBINDS = {"action": pygame.K_w, "restart": pygame.K_r, "editor": pygame.K_e}

sel_music_name = None  # выбранная музыка для запуска уровня

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 22)
big_font = pygame.font.SysFont("consolas", 44)
small_font = pygame.font.SysFont("consolas", 17)
tiny_font = pygame.font.SysFont("consolas", 14)
micro_font = pygame.font.SysFont("consolas", 12)

# --- генерация запасных звуков (если нет файлов) ---
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
        SND["play"]   = tone(500, 120, 0.30, "square", slide=200)
        SND["quit"]   = tone(400, 160, 0.30, "sine", slide=-160)
    except Exception:
        SND.clear()

build_sounds()


# --- поиск аудиофайлов в папке Звуки ---
def find_audio(base):
    if not os.path.isdir(SOUND_DIR):
        return None
    for ext in AUDIO_EXTS:
        p = os.path.join(SOUND_DIR, base + ext)
        if os.path.exists(p):
            return p
    # без учёта регистра
    low = base.lower()
    try:
        for fn in os.listdir(SOUND_DIR):
            name, ext = os.path.splitext(fn)
            if name.lower() == low and ext.lower() in AUDIO_EXTS:
                return os.path.join(SOUND_DIR, fn)
    except Exception:
        pass
    return None


def scan_mfrl():
    tracks = []
    if os.path.isdir(SOUND_DIR):
        try:
            for fn in os.listdir(SOUND_DIR):
                name, ext = os.path.splitext(fn)
                if name.upper().startswith("MFRL") and ext.lower() in AUDIO_EXTS:
                    tracks.append((name, os.path.join(SOUND_DIR, fn)))
        except Exception:
            pass
    tracks.sort(key=lambda t: (len(t[0]), t[0]))
    return tracks


def load_file_sfx():
    if not sound_ok:
        return
    mapping = {"death": "Dead", "play": "PlaySound_01", "quit": "QuitSound_01"}
    for key, base in mapping.items():
        p = find_audio(base)
        if p:
            try:
                SND[key] = pygame.mixer.Sound(p)
            except Exception:
                pass

load_file_sfx()

MENU_MUSIC = find_audio("MenuLoop")
EDITOR_MUSIC = find_audio("Redactor")

_cur_music = "___init___"
def set_music(path, loops=-1):
    global _cur_music
    if not sound_ok:
        return
    if path == _cur_music:
        return
    _cur_music = path
    try:
        if path:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(loops)
        else:
            pygame.mixer.music.stop()
    except Exception:
        pass


def snd(name):
    s = SND.get(name)
    if s:
        try:
            s.play()
        except Exception:
            pass


def level_music_path():
    for n, p in scan_mfrl():
        if n == sel_music_name:
            return p
    return None


def stop_music():
    """Полная остановка музыки (например при смерти)."""
    global _cur_music
    if not sound_ok:
        return
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass
    _cur_music = None


def restart_level_music():
    """Запуск музыки уровня заново с самого начала."""
    global _cur_music
    _cur_music = None
    set_music(level_music_path())


# --- аккаунт ---
ACCOUNT = {"username": None, "token": None}


def api_request(path, payload):
    """POST-запрос к серверу аккаунтов. Возвращает (ok, data_or_error)."""
    try:
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            SERVER_URL.rstrip("/") + path, data=body,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return True, data
    except urllib.error.HTTPError as e:
        try:
            data = json.loads(e.read().decode("utf-8"))
            return False, data.get("error", f"Ошибка {e.code}")
        except Exception:
            return False, f"Ошибка сервера ({e.code})"
    except Exception:
        return False, "Нет связи с сервером"


# --- конфиг (клавиши + музыка + слот + аккаунт) ---
def load_config():
    global sel_music_name, cur_slot
    try:
        with open(CONFIG_FILE) as f:
            d = json.load(f)
        c = d.get("controls", {})
        for k in KEYBINDS:
            if isinstance(c.get(k), int):
                KEYBINDS[k] = c[k]
        m = d.get("music")
        if isinstance(m, str) or m is None:
            sel_music_name = m
        s = d.get("slot")
        if isinstance(s, int) and 1 <= s <= LEVEL_SLOTS:
            cur_slot = s
        acc = d.get("account")
        if isinstance(acc, dict):
            ACCOUNT["username"] = acc.get("username")
            ACCOUNT["token"] = acc.get("token")
    except Exception:
        pass


def save_config():
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"controls": KEYBINDS, "music": sel_music_name,
                       "slot": cur_slot, "account": ACCOUNT}, f)
    except Exception:
        pass


level = []
# настройки уровня (стартовый режим и скорость при запуске)
LEVEL_META = {"mode": "cube", "lvl": 1}

PALETTE = [
    ("block", "1"), ("spike", "2"), ("slope", "3"), ("goal", "4"),
    ("p_cube", "5"), ("p_ship", "6"), ("p_wave", "7"), ("p_ufo", "8"),
    ("speed", "9"), ("orb", "O"), ("p_gup", "G"), ("p_gdn", "g"),
    ("p_mini", "m"), ("p_big", "M"), ("saw", "П"), ("mtrig", "0"),
    ("atrig", "A"), ("deco1", "Д1"), ("deco2", "Д2"),
    ("startpos", "T"), ("hbox", "H"),
]
BRUSH_NAMES = {
    "block": "блок", "spike": "шип", "slope": "склон", "goal": "финиш",
    "p_cube": "портал КУБ", "p_ship": "портал КОРАБЛЬ", "p_wave": "портал ВОЛНА",
    "p_ufo": "портал НЛО", "speed": "скорость", "mtrig": "Move-триггер",
    "startpos": "StartPos", "hbox": "H-блок",
    "orb": "сфера", "saw": "пила", "atrig": "Alpha-триггер",
    "deco1": "декор: кристалл", "deco2": "декор: растение",
    "p_gup": XPORTAL_RU["p_gup"], "p_gdn": XPORTAL_RU["p_gdn"],
    "p_mini": XPORTAL_RU["p_mini"], "p_big": XPORTAL_RU["p_big"],
    "_lvlset": "Настройки уровня",
}
MOVABLE_TYPES = ({"block", "spike", "slope", "hbox", "goal", "speed",
                  "orb", "saw", "deco1", "deco2"}
                 | set(P_COL) | set(XPORTAL_COL))

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
    data = {"objects": level, "music": sel_music_name,
            "mode": LEVEL_META.get("mode", "cube"), "lvl": LEVEL_META.get("lvl", 1)}
    with open(level_file(), "w") as f:
        json.dump(data, f)
    print(f"Уровень {cur_slot} сохранён")


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
    if o.get("t") in P_COL or o.get("t") in XPORTAL_COL:
        o.setdefault("rot", "vert")
    if o.get("t") == "orb":
        o.setdefault("kind", "yellow")
    if o.get("t") == "saw":
        o.setdefault("size", "big")
    if o.get("t") == "atrig":
        o.setdefault("dur", 30)
        o.setdefault("op", 0)
    return o


def load_level():
    global level, sel_music_name
    path = level_file()
    # миграция старого level.json в слот 1
    if not os.path.exists(path) and cur_slot == 1 and os.path.exists(LEGACY_LEVEL_FILE):
        try:
            os.rename(LEGACY_LEVEL_FILE, path)
            print("Старый level.json перенесён в слот 1")
        except Exception:
            path = LEGACY_LEVEL_FILE
    LEVEL_META["mode"] = "cube"
    LEVEL_META["lvl"] = 1
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, dict):
            level = [normalize(o) for o in data.get("objects", [])]
            m = data.get("music")
            if isinstance(m, str) or m is None:
                sel_music_name = m
            if data.get("mode") in ("cube", "ship", "wave", "ufo"):
                LEVEL_META["mode"] = data["mode"]
            if isinstance(data.get("lvl"), int) and 0 <= data["lvl"] < len(SPEED_LEVELS):
                LEVEL_META["lvl"] = data["lvl"]
        else:
            level = [normalize(o) for o in data]
        print(f"Уровень {cur_slot} загружен")
    else:
        level = []
        print(f"Слот {cur_slot}: пустой уровень")


def slot_object_count(n):
    """Количество объектов в слоте (для экрана выбора уровня)."""
    p = f"level{n}.json"
    if n == 1 and not os.path.exists(p) and os.path.exists(LEGACY_LEVEL_FILE):
        p = LEGACY_LEVEL_FILE
    try:
        with open(p) as f:
            data = json.load(f)
        return len(data.get("objects", []) if isinstance(data, dict) else data)
    except Exception:
        return None


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
    if d == "left":
        return [(x, y + GRID), (x + GRID, y + GRID), (x, y)]
    if d == "tright":
        return [(x, y), (x + GRID, y), (x + GRID, y + GRID)]
    if d == "tleft":
        return [(x, y), (x + GRID, y), (x, y + GRID)]
    return [(x, y + GRID), (x + GRID, y + GRID), (x + GRID, y)]


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


def saw_radius(o):
    return int(GRID * 1.35) if o.get("size", "big") == "big" else int(GRID * 0.55)


def saw_center(o, off=(0, 0)):
    return (o["x"] * GRID + GRID // 2 + off[0], o["y"] * GRID + GRID // 2 + off[1])


def draw_saw(surf, cx, cy, r, col, angle):
    """Вращающаяся пила: зубья + корпус + отверстие."""
    teeth = 10
    pts = []
    for i in range(teeth * 2):
        a = angle + (i / (teeth * 2)) * 2 * math.pi
        rad = r if i % 2 == 0 else r * 0.72
        pts.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad))
    pygame.draw.polygon(surf, col, pts)
    pygame.draw.polygon(surf, (255, 255, 255), pts, 2)
    pygame.draw.circle(surf, (255, 255, 255), (int(cx), int(cy)), max(3, int(r * 0.22)), 2)


def draw_orb(surf, cx, cy, kind, r=None):
    r = r or GRID // 2 - 4
    col = ORB_COL.get(kind, (250, 225, 70))
    pygame.draw.circle(surf, (255, 255, 255), (cx, cy), r + 4, 2)
    pygame.draw.circle(surf, col, (cx, cy), r)
    hl = max(2, r // 3)
    pygame.draw.circle(surf, (255, 255, 255), (cx - r // 3, cy - r // 3), hl)
    if kind == "green":
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), max(2, r // 2), 2)


def draw_deco(surf, kind, x, y, col):
    cx = x + GRID // 2
    if kind == "deco1":  # кристалл
        c = col or (120, 210, 250)
        pts = [(cx, y + 4), (x + GRID - 6, y + GRID // 2), (cx, y + GRID - 2), (x + 6, y + GRID // 2)]
        pygame.draw.polygon(surf, c, pts)
        pygame.draw.polygon(surf, (255, 255, 255), pts, 2)
        pygame.draw.line(surf, (255, 255, 255), (cx, y + 8), (x + GRID - 12, y + GRID // 2), 1)
    else:  # растение
        c = col or (95, 220, 110)
        pygame.draw.line(surf, c, (cx, y + GRID - 2), (cx, y + 10), 3)
        pygame.draw.polygon(surf, c, [(cx, y + 14), (cx - 12, y + GRID - 6), (cx - 2, y + GRID - 2)])
        pygame.draw.polygon(surf, c, [(cx, y + 14), (cx + 12, y + GRID - 6), (cx + 2, y + GRID - 2)])
        pygame.draw.circle(surf, (255, 255, 255), (cx, y + 9), 3)


def draw_object(surf, o, cam_x, editor_mode, off=(0, 0), alpha=255):
    """Обёртка с поддержкой прозрачности (Alpha-триггер)."""
    if alpha >= 250:
        return _draw_object(surf, o, cam_x, editor_mode, off)
    if alpha <= 4:
        return
    sx = o["x"] * GRID - cam_x + off[0]
    sy = o["y"] * GRID + off[1]
    if sx < -GRID * 3 or sx > WIDTH + GRID * 2:
        return
    pad = GRID * 2
    temp = pygame.Surface((GRID * 5, GRID * 5), pygame.SRCALPHA)
    # рисуем объект в локальных координатах (pad, pad)
    fake_cam = o["x"] * GRID + off[0] - pad
    fake_off = (off[0], off[1] - sy + pad)
    _draw_object(temp, o, fake_cam, editor_mode, fake_off)
    temp.set_alpha(alpha)
    surf.blit(temp, (sx - pad, sy - pad))


def _draw_object(surf, o, cam_x, editor_mode, off=(0, 0)):
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
            surf.blit(tiny_font.render(str(o["grp"]), True, (255, 255, 255)), (rect.x + 3, rect.y + 2))
    elif kind == "speed":
        lvl = SPEED_LEVELS[o.get("lvl", 1)]
        pygame.draw.rect(surf, lvl["col"], (x + 8, y - GRID + 4, GRID - 16, GRID * 2 - 8), border_radius=8)
        pygame.draw.rect(surf, (255, 255, 255), (x + 8, y - GRID + 4, GRID - 16, GRID * 2 - 8), 2, border_radius=8)
        draw_chevrons(surf, x + GRID // 2, y + GRID // 2, lvl["arrows"], lvl["dir"], (255, 255, 255))
        if editor_mode and o.get("grp", 0):
            surf.blit(tiny_font.render(str(o["grp"]), True, (255, 255, 255)), (x + 10, y - GRID + 6))
    elif kind in XPORTAL_COL:
        col = XPORTAL_COL[kind]
        if o.get("rot") == "horiz":
            rect = pygame.Rect(x - GRID // 2, y + 10, GRID * 2, GRID - 20)
        else:
            rect = pygame.Rect(x + 10, y - GRID, GRID - 20, GRID * 2)
        pygame.draw.rect(surf, col, rect, border_radius=12)
        pygame.draw.rect(surf, (255, 255, 255), rect, 2, border_radius=12)
        # стрелка-указатель
        cx2, cy2 = rect.centerx, rect.centery
        if kind == "p_gup":
            pygame.draw.polygon(surf, (30, 30, 40), [(cx2 - 6, cy2 + 5), (cx2, cy2 - 6), (cx2 + 6, cy2 + 5)])
        elif kind == "p_gdn":
            pygame.draw.polygon(surf, (30, 30, 40), [(cx2 - 6, cy2 - 5), (cx2, cy2 + 6), (cx2 + 6, cy2 - 5)])
        elif kind == "p_mini":
            pygame.draw.rect(surf, (30, 30, 40), (cx2 - 4, cy2 - 4, 8, 8), 2)
        else:
            pygame.draw.rect(surf, (30, 30, 40), (cx2 - 7, cy2 - 7, 14, 14), 2)
        if editor_mode and o.get("grp", 0):
            surf.blit(tiny_font.render(str(o["grp"]), True, (255, 255, 255)), (rect.x + 3, rect.y + 2))
    elif kind == "orb":
        draw_orb(surf, x + GRID // 2, y + GRID // 2, o.get("kind", "yellow"))
        if editor_mode and o.get("grp", 0):
            surf.blit(tiny_font.render(str(o["grp"]), True, (255, 255, 255)), (x + 3, y + 3))
    elif kind == "saw":
        ang = pygame.time.get_ticks() * 0.004
        draw_saw(surf, x + GRID // 2, y + GRID // 2, saw_radius(o),
                 obj_color(o, (150, 160, 180)), ang)
        if editor_mode and o.get("grp", 0):
            surf.blit(tiny_font.render(str(o["grp"]), True, (255, 255, 255)), (x + 3, y + 3))
    elif kind in ("deco1", "deco2"):
        draw_deco(surf, kind, x, y, obj_color(o, None))
        if editor_mode and o.get("grp", 0):
            surf.blit(tiny_font.render(str(o["grp"]), True, (255, 255, 255)), (x + 3, y + 3))
    elif kind == "atrig":
        if editor_mode:
            pygame.draw.line(surf, (90, 220, 240), (x + GRID // 2, 0), (x + GRID // 2, HEIGHT), 1)
            pygame.draw.circle(surf, (80, 230, 245), (x + GRID // 2, y + GRID // 2), GRID // 2 - 2)
            pygame.draw.circle(surf, (20, 20, 30), (x + GRID // 2, y + GRID // 2), GRID // 2 - 2, 3)
            t = small_font.render("A" + str(o.get("grp", 0)), True, (20, 20, 30))
            surf.blit(t, t.get_rect(center=(x + GRID // 2, y + GRID // 2)))
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


# ---------------- Иконки ----------------
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
    elif kind == "atrig":
        pygame.draw.circle(surf, (80, 230, 245), (cx, cy), 11)
        pygame.draw.circle(surf, (20, 20, 30), (cx, cy), 11, 3)
    elif kind == "orb":
        draw_orb(surf, cx, cy, "yellow", r=9)
    elif kind == "saw":
        draw_saw(surf, cx, cy, 13, (150, 160, 180), 0.4)
    elif kind in XPORTAL_COL:
        pygame.draw.rect(surf, XPORTAL_COL[kind], (x + 12, y + 5, g - 24, g - 10), border_radius=8)
        pygame.draw.rect(surf, (255, 255, 255), (x + 12, y + 5, g - 24, g - 10), 1, border_radius=8)
    elif kind in ("deco1", "deco2"):
        draw_deco(surf, kind, x, y, None)
    elif kind == "startpos":
        pygame.draw.rect(surf, (90, 240, 120), (x + 8, y + 8, g - 16, g - 16), 2)
        surf.blit(tiny_font.render("St", True, (90, 240, 120)),
                  tiny_font.render("St", True, (90, 240, 120)).get_rect(center=(cx, cy)))
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


# ---------------- Настройки объекта ----------------
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
            {"key": "rot", "label": "Поворот", "kind": "cycle",
             "values": ["right", "left", "tright", "tleft"], "ru": SLOPE_RU},
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
            {"key": "dx", "label": "Сдвиг по X (клетки)", "kind": "int", "min": -15, "max": 15, "step": 1, "dir": "x"},
            {"key": "dy", "label": "Сдвиг по Y (клетки)", "kind": "int", "min": -15, "max": 15, "step": 1, "dir": "y"},
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
    if t in XPORTAL_COL:
        return [
            {"key": "rot", "label": "Ориентация", "kind": "cycle", "values": ["vert", "horiz"]},
            grp_field,
        ]
    if t == "orb":
        return [
            {"key": "kind", "label": "Тип сферы", "kind": "cycle",
             "values": ORB_TYPES, "ru": ORB_RU},
            grp_field,
        ]
    if t == "saw":
        return [
            {"key": "size", "label": "Размер", "kind": "cycle",
             "values": ["big", "small"], "ru": {"big": "Большая", "small": "Маленькая"}},
            {"key": "c", "label": "Цвет", "kind": "index", "names": [n for n, _ in COLOR_GROUPS]},
            grp_field,
        ]
    if t == "atrig":
        return [
            {"key": "grp", "label": "Группа", "kind": "int", "min": 1, "max": 999, "step": 1},
            {"key": "op", "label": "Непрозрачность (%)", "kind": "int", "min": 0, "max": 100, "step": 10},
            {"key": "dur", "label": "Длительность (кадры)", "kind": "int", "min": 0, "max": 180, "step": 5},
        ]
    if t in ("deco1", "deco2"):
        return [
            {"key": "c", "label": "Цвет", "kind": "index", "names": [n for n, _ in COLOR_GROUPS]},
            grp_field,
        ]
    if t == "_lvlset":
        return [
            {"key": "mode", "label": "Режим при старте уровня", "kind": "cycle",
             "values": ["cube", "ship", "wave", "ufo"]},
            {"key": "lvl", "label": "Скорость при старте", "kind": "index", "names": speed_names},
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
    if f["kind"] == "cycle":
        ru = f.get("ru", CYCLE_RU)
        return ru.get(v, str(v))
    # int с подсказкой направления
    try:
        iv = int(v)
    except Exception:
        return str(v)
    if f.get("dir") == "x":
        if iv > 0:
            return f"{iv} (вправо)"
        if iv < 0:
            return f"{iv} (влево)"
        return "0"
    if f.get("dir") == "y":
        if iv > 0:
            return f"{iv} (вниз)"
        if iv < 0:
            return f"{iv} (вверх)"
        return "0"
    return str(iv)


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

    pw, ph = 560, 100 + max(1, len(spec)) * 40
    pxp, pyp = (WIDTH - pw) // 2, (HEIGHT - ph) // 2

    def row_y(i):
        return pyp + 54 + i * 40

    def minus_rect(i):
        return pygame.Rect(pxp + pw - 210, row_y(i) - 4, 28, 28)

    def plus_rect(i):
        return pygame.Rect(pxp + pw - 44, row_y(i) - 4, 28, 28)

    def row_rect(i):
        return pygame.Rect(pxp + 10, row_y(i) - 6, pw - 20, 34)

    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            w = wheel_delta(e)
            if w and spec:
                field_adjust(o, spec[sel], w)
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and spec:
                mp = e.pos
                for i in range(len(spec)):
                    if minus_rect(i).collidepoint(mp):
                        sel = i; field_adjust(o, spec[i], -1); break
                    if plus_rect(i).collidepoint(mp):
                        sel = i; field_adjust(o, spec[i], 1); break
                    if row_rect(i).collidepoint(mp):
                        sel = i; break
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

        pygame.draw.rect(screen, (40, 40, 55), (pxp, pyp, pw, ph), border_radius=12)
        pygame.draw.rect(screen, (90, 90, 120), (pxp, pyp, pw, ph), 2, border_radius=12)
        screen.blit(font.render("Настройки: " + BRUSH_NAMES.get(o["t"], o["t"]), True, TEXT_C),
                    (pxp + 16, pyp + 14))

        if not spec:
            screen.blit(small_font.render("У этого объекта нет параметров.", True, (180, 180, 190)),
                        (pxp + 16, pyp + 54))
        for i, f in enumerate(spec):
            yy = row_y(i)
            active = (i == sel)
            if active:
                pygame.draw.rect(screen, (60, 60, 85), row_rect(i), border_radius=6)
            screen.blit(small_font.render(f["label"], True, (200, 200, 210)), (pxp + 20, yy))
            # кнопки - / +
            for rct, sym in ((minus_rect(i), "-"), (plus_rect(i), "+")):
                pygame.draw.rect(screen, (70, 70, 95), rct, border_radius=6)
                pygame.draw.rect(screen, (120, 120, 150), rct, 1, border_radius=6)
                ts = font.render(sym, True, (255, 255, 255))
                screen.blit(ts, ts.get_rect(center=rct.center))
            val = field_display(o, f)
            vs = small_font.render(val, True, (255, 230, 120) if active else (200, 200, 210))
            screen.blit(vs, vs.get_rect(center=(pxp + pw - 127, yy + 8)))

        screen.blit(tiny_font.render("W/S выбрать · A/D или колесо менять · клик по - / + мышкой · E/ESC закрыть",
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


# ---------------- Экран выбора музыки ----------------
def music_screen(cam_x):
    global sel_music_name, _cur_music
    tracks = scan_mfrl()
    rows = [("Нет музыки", None)] + [(n, p) for n, p in tracks]

    def preview(path):
        global _cur_music
        try:
            pygame.mixer.music.stop()
            if path:
                pygame.mixer.music.load(path)
                pygame.mixer.music.play(0)
            _cur_music = None  # чтобы редактор потом восстановил свою музыку
        except Exception:
            pass

    def row_rect(i):
        return pygame.Rect(WIDTH // 2 - 240, 130 + i * 46, 480, 40)

    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for i, (nm, pth) in enumerate(rows):
                    if row_rect(i).collidepoint(e.pos):
                        sel_music_name = nm if pth is not None else None
                        snd("click")
                        preview(pth)   # тестовое воспроизведение
                        save_config()
                        break
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_u, pygame.K_RETURN):
                    try:
                        pygame.mixer.music.stop()
                    except Exception:
                        pass
                    _cur_music = None
                    return None

        screen.fill(BG)
        title = big_font.render("МУЗЫКА УРОВНЯ", True, (240, 110, 200))
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 70)))
        if len(rows) == 1:
            screen.blit(small_font.render("Положи файлы MFRL1, MFRL2... в папку 'Звуки'", True, (200, 200, 210)),
                        (WIDTH // 2 - 220, 120))
        for i, (nm, pth) in enumerate(rows):
            r = row_rect(i)
            selected = (sel_music_name == nm) if pth is not None else (sel_music_name is None)
            pygame.draw.rect(screen, (44, 44, 58), r, border_radius=8)
            if selected:
                pygame.draw.rect(screen, SEL_C, r, 3, border_radius=8)
            else:
                pygame.draw.rect(screen, (72, 72, 92), r, 1, border_radius=8)
            screen.blit(font.render(nm, True, TEXT_C), (r.x + 14, r.y + 8))
            if pth is not None:
                screen.blit(tiny_font.render("клик — выбрать и прослушать", True, (150, 150, 165)),
                            (r.right - 210, r.y + 13))
        screen.blit(tiny_font.render("Зелёный контур = выбрано и будет играть при запуске уровня · U/ESC — назад",
                                     True, (160, 160, 175)), (WIDTH // 2 - 300, HEIGHT - 40))
        pygame.display.flip()


# ---------------- Редактор ----------------
def editor():
    cam_x = 0
    bi = 0
    cur_color = 0
    cur_group = 0
    cur_speed = 1
    cur_orb = 0
    cur_saw = "big"
    cur_start_mode = "cube"
    cur_rot = {"spike": "up", "slope": "right", "portal": "vert"}

    key_to_idx = {}
    for idx, (k, lab) in enumerate(PALETTE):
        if lab.isdigit():
            key_to_idx[getattr(pygame, "K_" + lab)] = idx
    key_to_idx[pygame.K_t] = next(i for i, (k, _) in enumerate(PALETTE) if k == "startpos")
    key_to_idx[pygame.K_h] = next(i for i, (k, _) in enumerate(PALETTE) if k == "hbox")

    def brush_rot(kind):
        if kind == "spike":
            return cur_rot["spike"]
        if kind == "slope":
            return cur_rot["slope"]
        if kind in P_COL or kind in XPORTAL_COL:
            return cur_rot["portal"]
        return None

    while True:
        clock.tick(FPS)
        set_music(EDITOR_MUSIC)
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
                elif kind == "orb":
                    cur_orb = (cur_orb + w) % len(ORB_TYPES)
                elif kind == "saw":
                    cur_saw = "small" if cur_saw == "big" else "big"
                elif kind in ("block", "spike", "slope", "deco1", "deco2"):
                    cur_color = (cur_color + w) % len(COLOR_GROUPS)
                elif kind in ("mtrig", "atrig") or kind in P_COL or kind in XPORTAL_COL:
                    cur_group = max(0, min(999, cur_group + w))
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
                    cur_group = max(0, cur_group - 1)
                if e.key == pygame.K_EQUALS:
                    cur_group = min(999, cur_group + 1)
                if e.key == pygame.K_COMMA:
                    cur_speed = (cur_speed - 1) % len(SPEED_LEVELS)
                if e.key == pygame.K_PERIOD:
                    cur_speed = (cur_speed + 1) % len(SPEED_LEVELS)
                if e.key == pygame.K_m:
                    order = ["cube", "ship", "wave", "ufo"]
                    cur_start_mode = order[(order.index(cur_start_mode) + 1) % len(order)]
                if e.key == pygame.K_u:
                    if music_screen(cam_x) == "quit":
                        pygame.quit(); return "quit"
                if e.key == pygame.K_n:
                    # настройки уровня: стартовый режим и скорость
                    ls = {"t": "_lvlset", "mode": LEVEL_META.get("mode", "cube"),
                          "lvl": LEVEL_META.get("lvl", 1)}
                    if edit_object_settings(ls, cam_x) == "quit":
                        pygame.quit(); return "quit"
                    LEVEL_META["mode"] = ls["mode"]
                    LEVEL_META["lvl"] = ls["lvl"]
                if e.key == pygame.K_r:
                    # поворот: объект под курсором ИЛИ кисть (до постановки)
                    obj = next((o for o in level if o["x"] == gx and o["y"] == gy
                                and any(f["key"] == "rot" for f in get_spec(o))), None)
                    if obj:
                        rf = next(f for f in get_spec(obj) if f["key"] == "rot")
                        obj.setdefault("rot", rf["values"][0])
                        field_adjust(obj, rf, 1)
                    else:
                        if kind == "spike":
                            vals = ["up", "right", "down", "left"]
                            cur_rot["spike"] = vals[(vals.index(cur_rot["spike"]) + 1) % 4]
                        elif kind == "slope":
                            vals = ["right", "left", "tright", "tleft"]
                            cur_rot["slope"] = vals[(vals.index(cur_rot["slope"]) + 1) % 4]
                        elif kind in P_COL or kind in XPORTAL_COL:
                            cur_rot["portal"] = "horiz" if cur_rot["portal"] == "vert" else "vert"
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
                    obj["rot"] = cur_rot["spike"]
                if kind == "slope":
                    obj["rot"] = cur_rot["slope"]
                if kind in P_COL:
                    obj["rot"] = cur_rot["portal"]
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
            prot = brush_rot(kind) or "up"
            preview = {"x": gx, "y": gy, "t": kind, "c": cur_color, "grp": cur_group,
                       "lvl": cur_speed, "mode": cur_start_mode, "rot": prot}
            draw_object(screen, preview, cam_x, editor_mode=True)
            pygame.draw.rect(screen, (255, 255, 0), (gx * GRID - cam_x, gy * GRID, GRID, GRID), 2)

        screen.blit(small_font.render(f"{TITLE}   {VERSION}   —   РЕДАКТОР", True, TEXT_C), (10, 8))
        screen.blit(tiny_font.render(
            "ЛКМ ставить · ПКМ удалять · A/D камера · E настройки · R поворот · U музыка · S сохр · L загр · C стереть · P играть · ESC",
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
                pills.append(("Группа - = колесо", str(cur_group), (240, 110, 200)))
            if kind in ("spike", "slope"):
                pills.append(("Поворот (R)", CYCLE_RU.get(brush_rot(kind), brush_rot(kind)), (255, 220, 120)))
            if kind in P_COL:
                pills.append(("Группа - = колесо", str(cur_group), (240, 110, 200)))
                pills.append(("Ориентация (R)", CYCLE_RU.get(brush_rot(kind), ""), (255, 220, 120)))
            if kind == "speed":
                pills.append(("Скорость , . / колесо", "x" + str(SPEED_LEVELS[cur_speed]["mult"]),
                              SPEED_LEVELS[cur_speed]["col"]))
                pills.append(("Группа - =", str(cur_group), (240, 110, 200)))
            if kind == "mtrig":
                pills.append(("Группа - = колесо", str(cur_group), (240, 110, 200)))
                pills.append(("Настрой", "жми E на нём", (255, 220, 120)))
            if kind == "startpos":
                pills.append(("Режим (m)", CYCLE_RU.get(cur_start_mode, cur_start_mode), (120, 200, 255)))
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

    snd("play")
    set_music(level_music_path())

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
        st["trail"] = []
        st["explode"] = []
        st["death_timer"] = 0
    reset()

    def spawn_explosion():
        cx = px + size / 2
        cy = st["py"] + size / 2
        for i in range(18):
            ang = (i / 18) * 2 * math.pi
            spd = 2.5 + (i % 4)
            st["explode"].append([cx, cy, math.cos(ang) * spd, math.sin(ang) * spd,
                                   DEATH_FRAMES, 3 + (i % 3)])

    while True:
        clock.tick(FPS)
        flap = False
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); return "quit"
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return "menu"
                if e.key == KEYBINDS["editor"]:
                    return "editor"          # в редактор одним нажатием
                if e.key == KEYBINDS["restart"]:
                    reset()
                if e.key == KEYBINDS["action"] or e.key in (pygame.K_SPACE, pygame.K_UP):
                    flap = True
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                flap = True

        keys = pygame.key.get_pressed()
        hold = (keys[KEYBINDS["action"]] or keys[pygame.K_SPACE] or keys[pygame.K_UP]
                or pygame.mouse.get_pressed()[0])

        # --- смерть: заморозка + взрыв + авто-возрождение ---
        if st["dead"]:
            st["death_timer"] -= 1
            for p in st["explode"]:
                p[0] += p[2]; p[1] += p[3]; p[3] += 0.15; p[4] -= 1
            st["explode"] = [p for p in st["explode"] if p[4] > 0]
            if st["death_timer"] <= 0:
                reset()

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
                    if pr.colliderect(portal_rect(o, ooff)):
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
                    else:
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
                else:
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
                    else:
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

            # след
            for tp in st["trail"]:
                tp[0] -= cur_speed; tp[2] -= 1
            st["trail"] = [tp for tp in st["trail"] if tp[2] > 0]
            st["trail"].append([float(px), float(py), TRAIL_LIFE])

            st["py"] = py; st["vy"] = vy

            if st["mode"] != prev_mode:
                snd("portal")
            if st["dead"] and not was_dead:
                snd("death")
                spawn_explosion()
                st["death_timer"] = DEATH_FRAMES
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

        # след (полупрозрачная аура)
        for tp in st["trail"]:
            a = int(70 * tp[2] / TRAIL_LIFE)
            s_ = pygame.Surface((size, size), pygame.SRCALPHA)
            s_.fill((color[0], color[1], color[2], a))
            screen.blit(s_, (tp[0], tp[1]))

        py = st["py"]; vy = st["vy"]; mode = st["mode"]
        if not st["dead"]:
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

        # взрыв
        for p in st["explode"]:
            a = max(0, int(255 * p[4] / DEATH_FRAMES))
            rad = int(p[5] * (0.4 + p[4] / DEATH_FRAMES))
            ps = pygame.Surface((rad * 2 + 2, rad * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (color[0], color[1], color[2], a), (rad + 1, rad + 1), rad)
            screen.blit(ps, (p[0] - rad, p[1] - rad))

        mode_ru = {"cube": "КУБ", "ship": "КОРАБЛИК", "wave": "ВОЛНА", "ufo": "НЛО"}[mode]
        screen.blit(font.render(f"Режим: {mode_ru}   x{st['mult']}", True, TEXT_C), (10, 10))
        screen.blit(small_font.render("Действие · R заново · E редактор · ESC меню", True, TEXT_C), (10, 40))

        if st["won"]:
            m = big_font.render("Уровень пройден!  R — заново", True, GOAL_C)
            screen.blit(m, m.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

        pygame.display.flip()


# ---------------- Настройки управления ----------------
def controls_screen():
    actions = [("action", "Прыжок / Действие"), ("restart", "Возрождение"),
               ("editor", "В редактор (из игры)")]
    sel = 0
    capturing = False
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            if e.type == pygame.KEYDOWN:
                if capturing:
                    if e.key != pygame.K_ESCAPE:
                        KEYBINDS[actions[sel][0]] = e.key
                        save_config()
                    capturing = False
                else:
                    if e.key == pygame.K_ESCAPE:
                        save_config(); return "menu"
                    if e.key == pygame.K_w:
                        sel = (sel - 1) % len(actions)
                    if e.key == pygame.K_s:
                        sel = (sel + 1) % len(actions)
                    if e.key == pygame.K_RETURN:
                        capturing = True
                    if e.key == pygame.K_BACKSPACE:
                        KEYBINDS.update({"action": pygame.K_w, "restart": pygame.K_r, "editor": pygame.K_e})
                        save_config()

        screen.fill(BG)
        title = big_font.render("УПРАВЛЕНИЕ", True, SKINS[skin_index][1])
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 80)))
        for i, (k, label) in enumerate(actions):
            yy = 180 + i * 60
            r = pygame.Rect(WIDTH // 2 - 260, yy, 520, 46)
            pygame.draw.rect(screen, (44, 44, 58), r, border_radius=8)
            if i == sel:
                pygame.draw.rect(screen, SEL_C, r, 3, border_radius=8)
            else:
                pygame.draw.rect(screen, (72, 72, 92), r, 1, border_radius=8)
            screen.blit(font.render(label, True, TEXT_C), (r.x + 16, r.y + 11))
            keyname = pygame.key.name(KEYBINDS[k]).upper()
            if capturing and i == sel:
                keyname = "нажми клавишу..."
            screen.blit(font.render(keyname, True, (255, 230, 120)), (r.right - 220, r.y + 11))
        screen.blit(tiny_font.render(
            "W/S выбрать · Enter — переназначить · Backspace — сброс · SPACE/мышь всегда работают · ESC назад",
            True, (160, 160, 175)), (WIDTH // 2 - 320, HEIGHT - 60))
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
        set_music(MENU_MUSIC)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_e: return "editor"
                if e.key == pygame.K_p:
                    load_level(); return "play"
                if e.key == pygame.K_i: return "help"
                if e.key == pygame.K_k: return "controls"
                if e.key == pygame.K_a:
                    skin_index = (skin_index - 1) % len(SKINS)
                if e.key == pygame.K_d:
                    skin_index = (skin_index + 1) % len(SKINS)
                if e.key == pygame.K_ESCAPE:
                    snd("quit")
                    if sound_ok:
                        pygame.time.wait(350)
                    return "quit"

        screen.fill(BG)
        title = big_font.render("VITHEL DASH REDACTOR", True, SKINS[skin_index][1])
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 100)))
        screen.blit(small_font.render(VERSION + ("  ♪" if sound_ok else "  (без звука)"), True, TEXT_C),
                    (WIDTH // 2 - 40, 138))
        for i, t in enumerate(["E — Редактор уровней", "P — Играть (level.json)",
                               "I — Справочник", "K — Управление", "ESC — Выход"]):
            r = font.render(t, True, TEXT_C)
            screen.blit(r, r.get_rect(center=(WIDTH // 2, 200 + i * 36)))
        name, col = SKINS[skin_index]
        screen.blit(font.render("Скин (A / D):", True, TEXT_C), (WIDTH // 2 - 210, 430))
        pygame.draw.rect(screen, col, (WIDTH // 2 - 20, 422, 40, 40), border_radius=6)
        screen.blit(font.render(name, True, col), (WIDTH // 2 + 40, 430))
        pygame.display.flip()


# ---------------- Главный цикл ----------------
def main():
    load_config()
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
        elif state == "controls":
            state = controls_screen()
        else:
            break
    pygame.quit()


if __name__ == "__main__":
    main()
