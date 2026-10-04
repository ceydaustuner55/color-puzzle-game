import pygame
import random
import math
import json
import os
import wave
import struct

pygame.init()

try:
    pygame.mixer.init()
    MIXER_OK = True
except:
    MIXER_OK = False

WIDTH, HEIGHT = 1000, 700
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SHAPE LIQUID")
clock = pygame.time.Clock()

SAVE_FILE = "shape_liquid_save.json"

# =========================================================
# RENKLER
# =========================================================

BG = (10, 16, 32)
BG2 = (22, 34, 62)

WHITE = (245, 248, 255)
BLACK = (5, 8, 15)

RED = (235, 65, 80)
ORANGE = (245, 135, 45)
YELLOW = (245, 205, 55)
GREEN = (65, 200, 115)
BLUE = (65, 145, 245)
PURPLE = (150, 90, 235)
PINK = (240, 90, 175)

COLORS = [
    RED, ORANGE, YELLOW,
    GREEN, BLUE, PURPLE, PINK
]

SHAPES = [
    "circle",
    "star",
    "heart",
    "triangle"
]

# =========================================================
# FONTLAR
# =========================================================

FONT_BIG = pygame.font.SysFont("arial", 58, bold=True)
FONT_TITLE = pygame.font.SysFont("arial", 42, bold=True)
FONT_MED = pygame.font.SysFont("arial", 27, bold=True)
FONT_SMALL = pygame.font.SysFont("arial", 20, bold=True)
FONT_TINY = pygame.font.SysFont("arial", 16, bold=True)

# =========================================================
# SES
# =========================================================

def make_tone(filename, frequency, duration, volume=0.3):
    sample_rate = 44100
    samples = int(sample_rate * duration)

    with wave.open(filename, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        for i in range(samples):
            t = i / sample_rate

            fade = min(
                1,
                i / 1000,
                (samples - i) / 1000
            )

            value = math.sin(
                2 * math.pi * frequency * t
            )

            value *= volume * fade

            wav.writeframes(
                struct.pack(
                    "<h",
                    int(value * 32767)
                )
            )


def make_music(filename):
    sample_rate = 44100
    duration = 4

    notes = [
        261.63,
        329.63,
        392.00,
        329.63,
        293.66,
        349.23,
        440.00,
        349.23
    ]

    with wave.open(filename, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        total = int(sample_rate * duration)

        for i in range(total):
            t = i / sample_rate

            note_index = int(t / 0.5) % len(notes)
            freq = notes[note_index]

            value = (
                math.sin(2 * math.pi * freq * t) * 0.12
                +
                math.sin(2 * math.pi * freq * 2 * t) * 0.04
            )

            wav.writeframes(
                struct.pack(
                    "<h",
                    int(value * 32767)
                )
            )


MOVE_SOUND = "move_sound.wav"
DROP_SOUND = "drop_sound.wav"
COMPLETE_SOUND = "complete_sound.wav"
MUSIC_FILE = "shape_music.wav"

if not os.path.exists(MOVE_SOUND):
    make_tone(MOVE_SOUND, 520, 0.08)

if not os.path.exists(DROP_SOUND):
    make_tone(DROP_SOUND, 250, 0.10)

if not os.path.exists(COMPLETE_SOUND):
    make_tone(COMPLETE_SOUND, 780, 0.35)

if not os.path.exists(MUSIC_FILE):
    make_music(MUSIC_FILE)

if MIXER_OK:
    move_sound = pygame.mixer.Sound(MOVE_SOUND)
    drop_sound = pygame.mixer.Sound(DROP_SOUND)
    complete_sound = pygame.mixer.Sound(COMPLETE_SOUND)

    move_sound.set_volume(0.35)
    drop_sound.set_volume(0.30)
    complete_sound.set_volume(0.45)


def play_sound(sound):
    if MIXER_OK and save_data.get("sound", True):
        sound.play()


# =========================================================
# KAYIT
# =========================================================

save_data = {
    "unlocked": 1,
    "best_moves": {},
    "sound": True,
    "music": True
}


def load_save():
    global save_data

    if os.path.exists(SAVE_FILE):
        try:
            with open(
                SAVE_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

            if isinstance(data, dict):
                save_data.update(data)

        except:
            pass


def save_game():
    try:
        with open(
            SAVE_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                save_data,
                f,
                ensure_ascii=False,
                indent=2
            )

    except:
        pass


load_save()

# =========================================================
# MÜZİK
# =========================================================

def update_audio():

    if not MIXER_OK:
        return

    if save_data.get("music", True):

        try:
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.load(MUSIC_FILE)
                pygame.mixer.music.set_volume(0.20)
                pygame.mixer.music.play(-1)

        except:
            pass

    else:
        pygame.mixer.music.stop()


update_audio()

# =========================================================
# OYUN DURUMLARI
# =========================================================

STATE_MENU = "menu"
STATE_SELECT = "select"
STATE_GAME = "game"
STATE_SETTINGS = "settings"
STATE_COMPLETE = "complete"

state = STATE_MENU

current_level = 1
moves = 0

selected_tube = None
history = []
tubes = []

# =========================================================
# ANİMASYONLAR
# =========================================================

menu_time = 0
game_time = 0
completion_time = 0

ANIMATION_TIME = 0.38

moving_animation = None

transition_alpha = 0
transition_active = False
transition_speed = 700

tube_bounce = {}

confetti = []

level_page = 0

# =========================================================
# PARÇA
# =========================================================

def create_piece(color_index, shape):

    return {
        "color": color_index,
        "shape": shape
    }


# =========================================================
# SEVİYE AYARLARI
# =========================================================

def settings_for_level(level):

    if level <= 10:
        return {
            "colors": min(2 + level // 4, 4),
            "shapes": ["circle"],
            "groups": min(2 + level // 3, 4)
        }

    if level <= 20:
        return {
            "colors": min(
                3 + (level - 11) // 4,
                5
            ),
            "shapes": ["circle", "star"],
            "groups": min(
                4 + (level - 11) // 3,
                6
            )
        }

    if level <= 40:
        return {
            "colors": min(
                4 + (level - 21) // 5,
                6
            ),
            "shapes": ["circle", "star"],
            "groups": min(
                5 + (level - 21) // 4,
                7
            )
        }

    if level <= 60:
        return {
            "colors": min(
                4 + (level - 41) // 5,
                6
            ),
            "shapes": [
                "circle",
                "star",
                "heart"
            ],
            "groups": min(
                6 + (level - 41) // 5,
                8
            )
        }

    if level <= 80:
        return {
            "colors": min(
                5 + (level - 61) // 5,
                7
            ),
            "shapes": SHAPES,
            "groups": min(
                7 + (level - 61) // 5,
                9
            )
        }

    return {
        "colors": min(
            6 + (level - 81) // 5,
            7
        ),
        "shapes": SHAPES,
        "groups": min(
            8 + (level - 81) // 5,
            10
        )
    }


# =========================================================
# SEVİYE OLUŞTUR
# =========================================================

def create_level(level):

    settings = settings_for_level(level)

    color_count = settings["colors"]
    shape_list = settings["shapes"]
    group_count = settings["groups"]

    combinations = []

    for c in range(color_count):
        for shape in shape_list:
            combinations.append(
                (c, shape)
            )

    random.shuffle(combinations)

    selected = combinations[:group_count]

    pieces = []

    for color_index, shape in selected:

        for _ in range(4):

            pieces.append(
                create_piece(
                    color_index,
                    shape
                )
            )

    random.shuffle(pieces)

    tube_count = group_count + 1

    result = [
        []
        for _ in range(tube_count)
    ]

    for piece in pieces:

        possible = [
            i
            for i in range(group_count)
            if len(result[i]) < 4
        ]

        tube = random.choice(possible)

        result[tube].append(piece)

    result[-1] = []

    return result


# =========================================================
# SEVİYE BAŞLAT
# =========================================================

def start_level(level, fade=True):

    global current_level
    global tubes
    global moves
    global selected_tube
    global history
    global moving_animation
    global transition_alpha
    global transition_active
    global game_time
    global tube_bounce

    current_level = level

    tubes = create_level(level)

    moves = 0
    selected_tube = None
    history = []

    moving_animation = None

    game_time = 0
    tube_bounce = {
        i: 0
        for i in range(len(tubes))
    }

    if fade:
        transition_alpha = 255
        transition_active = True
    else:
        transition_alpha = 0
        transition_active = False

    state_change(STATE_GAME)


def state_change(new_state):

    global state

    state = new_state


# =========================================================
# TÜP POZİSYONLARI
# =========================================================

def get_tube_positions(count):

    tube_width = 68
    tube_height = 250
    gap = 15

    total_width = (
        count * tube_width
        +
        (count - 1) * gap
    )

    start_x = (
        WIDTH - total_width
    ) // 2

    y = 285

    positions = []

    for i in range(count):

        x = (
            start_x
            +
            i * (tube_width + gap)
        )

        positions.append(
            (
                x,
                y,
                tube_width,
                tube_height
            )
        )

    return positions


# =========================================================
# ARKA PLAN
# =========================================================

def draw_background():

    for y in range(HEIGHT):

        t = y / HEIGHT

        r = int(
            BG[0] * (1 - t)
            +
            BG2[0] * t
        )

        g = int(
            BG[1] * (1 - t)
            +
            BG2[1] * t
        )

        b = int(
            BG[2] * (1 - t)
            +
            BG2[2] * t
        )

        pygame.draw.line(
            screen,
            (r, g, b),
            (0, y),
            (WIDTH, y)
        )


# =========================================================
# MENÜ PARÇACIKLARI
# =========================================================

def update_menu_animation(dt):

    global menu_time

    menu_time += dt


def draw_menu_particles():

    for i in range(20):

        x = (
            (
                i * 137
                +
                menu_time * (15 + i % 4 * 5)
            )
            %
            (WIDTH + 100)
        ) - 50

        y = (
            100
            +
            math.sin(
                menu_time * 0.7 + i
            ) * 60
            +
            (i * 47) % 520
        )

        radius = 3 + i % 4

        surf = pygame.Surface(
            (
                radius * 4,
                radius * 4
            ),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            surf,
            (100, 170, 255, 45),
            (
                radius * 2,
                radius * 2
            ),
            radius
        )

        screen.blit(
            surf,
            (
                int(x),
                int(y)
            )
        )


# =========================================================
# ŞEKİLLER
# =========================================================

def draw_circle(surface, color, x, y, r):

    pygame.draw.circle(
        surface,
        (0, 0, 0),
        (x + 2, y + 3),
        r
    )

    pygame.draw.circle(
        surface,
        color,
        (x, y),
        r
    )

    highlight = tuple(
        min(255, c + 55)
        for c in color
    )

    pygame.draw.circle(
        surface,
        highlight,
        (
            x - r // 3,
            y - r // 3
        ),
        max(2, r // 4)
    )

    pygame.draw.circle(
        surface,
        WHITE,
        (
            x - r // 3,
            y - r // 3
        ),
        max(1, r // 8)
    )


def star_points(cx, cy, r):

    points = []

    for i in range(10):

        angle = (
            -math.pi / 2
            +
            i * math.pi / 5
        )

        radius = (
            r
            if i % 2 == 0
            else r * 0.45
        )

        points.append(
            (
                cx + math.cos(angle) * radius,
                cy + math.sin(angle) * radius
            )
        )

    return points


def draw_star(surface, color, x, y, r):

    points = star_points(
        x,
        y,
        r
    )

    pygame.draw.polygon(
        surface,
        (0, 0, 0),
        [
            (
                px + 2,
                py + 3
            )
            for px, py in points
        ]
    )

    pygame.draw.polygon(
        surface,
        color,
        points
    )

    pygame.draw.circle(
        surface,
        WHITE,
        (
            x - r // 3,
            y - r // 3
        ),
        max(2, r // 6)
    )


def heart_points(cx, cy, r):

    points = []

    for i in range(41):

        t = (
            math.pi * 2 * i / 40
        )

        xx = (
            16 * math.sin(t) ** 3
        )

        yy = (
            13 * math.cos(t)
            -
            5 * math.cos(2 * t)
            -
            2 * math.cos(3 * t)
            -
            math.cos(4 * t)
        )

        points.append(
            (
                cx + xx * r / 32,
                cy - yy * r / 32
            )
        )

    return points


def draw_heart(surface, color, x, y, r):

    points = heart_points(
        x,
        y,
        r
    )

    shadow = [
        (
            px + 2,
            py + 3
        )
        for px, py in points
    ]

    pygame.draw.polygon(
        surface,
        (0, 0, 0),
        shadow
    )

    pygame.draw.polygon(
        surface,
        color,
        points
    )

    pygame.draw.circle(
        surface,
        WHITE,
        (
            x - r // 4,
            y - r // 3
        ),
        max(2, r // 6)
    )


def draw_triangle(surface, color, x, y, r):

    points = []

    for i in range(3):

        angle = (
            -math.pi / 2
            +
            i * 2 * math.pi / 3
        )

        points.append(
            (
                x + math.cos(angle) * r,
                y + math.sin(angle) * r
            )
        )

    shadow = [
        (
            px + 2,
            py + 3
        )
        for px, py in points
    ]

    pygame.draw.polygon(
        surface,
        (0, 0, 0),
        shadow
    )

    pygame.draw.polygon(
        surface,
        color,
        points
    )

    pygame.draw.circle(
        surface,
        WHITE,
        (
            x - r // 4,
            y - r // 4
        ),
        max(2, r // 6)
    )


def draw_shape(
    surface,
    color,
    shape,
    x,
    y,
    r
):

    if shape == "circle":

        draw_circle(
            surface,
            color,
            x,
            y,
            r
        )

    elif shape == "star":

        draw_star(
            surface,
            color,
            x,
            y,
            r
        )

    elif shape == "heart":

        draw_heart(
            surface,
            color,
            x,
            y,
            r
        )

    elif shape == "triangle":

        draw_triangle(
            surface,
            color,
            x,
            y,
            r
        )


# =========================================================
# TÜP
# =========================================================

def draw_tube(x, y, w, h, bounce=0):

    y += int(bounce)

    # Gölge
    shadow = pygame.Surface(
        (
            w + 30,
            h + 35
        ),
        pygame.SRCALPHA
    )

    pygame.draw.rect(
        shadow,
        (0, 0, 0, 80),
        (
            15,
            12,
            w,
            h
        ),
        border_radius=22
    )

    screen.blit(
        shadow,
        (
            x - 15,
            y + 8
        )
    )

    # Cam
    glass = pygame.Surface(
        (w, h),
        pygame.SRCALPHA
    )

    pygame.draw.rect(
        glass,
        (75, 160, 235, 35),
        (
            1,
            1,
            w - 2,
            h - 2
        ),
        border_radius=22
    )

    pygame.draw.rect(
        glass,
        (125, 205, 255, 100),
        (
            1,
            1,
            w - 2,
            h - 2
        ),
        width=2,
        border_radius=22
    )

    pygame.draw.line(
        glass,
        (220, 245, 255, 130),
        (12, 15),
        (12, h - 20),
        3
    )

    screen.blit(
        glass,
        (x, y)
    )


# =========================================================
# PARÇALARI TÜP İÇİNE ÇİZ
# =========================================================

def draw_pieces(
    tube_index,
    tube,
    x,
    y,
    w,
    h
):

    if not tube:
        return

    bounce = tube_bounce.get(
        tube_index,
        0
    )

    for i, piece in enumerate(tube):

        base_y = (
            y
            +
            h
            -
            35
            -
            i * 48
        )

        idle = (
            math.sin(
                game_time * 3
                +
                tube_index * 0.8
                +
                i * 0.65
            )
            * 1.8
        )

        settle = (
            math.sin(
                bounce * math.pi * 2
            )
            *
            bounce
            *
            7
        )

        px = x + w // 2
        py = base_y + idle + settle

        draw_shape(
            screen,
            COLORS[piece["color"]],
            piece["shape"],
            int(px),
            int(py),
            18
        )


# =========================================================
# TÜP SEÇİMİ
# =========================================================

def draw_selection(
    x,
    y,
    w,
    h
):

    pygame.draw.rect(
        screen,
        (100, 200, 255),
        (
            x - 4,
            y - 4,
            w + 8,
            h + 8
        ),
        width=3,
        border_radius=24
    )


# =========================================================
# BUTON
# =========================================================

def draw_button(
    rect,
    text,
    enabled=True,
    font=FONT_MED
):

    if enabled:
        color = (55, 115, 205)
    else:
        color = (55, 60, 75)

    pygame.draw.rect(
        screen,
        (0, 0, 0),
        (
            rect.x + 3,
            rect.y + 5,
            rect.w,
            rect.h
        ),
        border_radius=16
    )

    pygame.draw.rect(
        screen,
        color,
        rect,
        border_radius=16
    )

    pygame.draw.rect(
        screen,
        (130, 200, 255),
        rect,
        width=2,
        border_radius=16
    )

    txt = font.render(
        text,
        True,
        WHITE
    )

    screen.blit(
        txt,
        (
            rect.centerx
            -
            txt.get_width() // 2,
            rect.centery
            -
            txt.get_height() // 2
        )
    )


# =========================================================
# BAŞLIK
# =========================================================

def draw_header(title):

    text = FONT_TITLE.render(
        title,
        True,
        WHITE
    )

    screen.blit(
        text,
        (
            WIDTH // 2
            -
            text.get_width() // 2,
            25
        )
    )


# =========================================================
# GRUP BUL
# =========================================================

def get_group_size(tube):

    if not tube:
        return 0

    top = tube[-1]

    count = 0

    for piece in reversed(tube):

        if (
            piece["color"] == top["color"]
            and
            piece["shape"] == top["shape"]
            and
            count < 3
        ):

            count += 1

        else:
            break

    return count


# =========================================================
# HAMLE
# =========================================================

def copy_tubes():

    return [
        [
            dict(piece)
            for piece in tube
        ]
        for tube in tubes
    ]


def can_move(source, target):

    if source == target:
        return False

    if not tubes[source]:
        return False

    group_size = get_group_size(
        tubes[source]
    )

    if (
        len(tubes[target])
        +
        group_size
        >
        4
    ):
        return False

    return True


def move_group(source, target):

    global moving_animation

    if not can_move(
        source,
        target
    ):
        return False

    group_size = get_group_size(
        tubes[source]
    )

    group = tubes[source][
        -group_size:
    ]

    history.append(
        copy_tubes()
    )

    del tubes[source][
        -group_size:
    ]

    moving_animation = {
        "source": source,
        "target": target,
        "group": [
            dict(p)
            for p in group
        ],
        "progress": 0
    }

    if MIXER_OK:
        play_sound(move_sound)

    return True


# =========================================================
# HAREKET ANİMASYONU
# =========================================================

def smoothstep(t):

    return t * t * (3 - 2 * t)


def draw_moving_animation():

    if moving_animation is None:
        return

    source = moving_animation["source"]
    target = moving_animation["target"]

    group = moving_animation["group"]
    progress = moving_animation["progress"]

    positions = get_tube_positions(
        len(tubes)
    )

    sx, sy, sw, sh = positions[source]
    tx, ty, tw, th = positions[target]

    t = smoothstep(progress)

    start_x = sx + sw // 2
    start_y = sy + sh - 40

    end_x = tx + tw // 2

    target_height = len(
        tubes[target]
    )

    end_y = (
        ty
        +
        th
        -
        35
        -
        target_height * 48
    )

    arc = (
        math.sin(
            math.pi * progress
        )
        * 120
    )

    x = (
        start_x
        +
        (end_x - start_x) * t
    )

    y = (
        start_y
        +
        (end_y - start_y) * t
        -
        arc
    )

    for i, piece in enumerate(group):

        wobble = (
            math.sin(
                progress * math.pi * 5
                +
                i
            )
            * 4
        )

        draw_shape(
            screen,
            COLORS[piece["color"]],
            piece["shape"],
            int(x + wobble),
            int(y + i * 45),
            18
        )


def finish_move_animation():

    global moving_animation
    global moves
    global selected_tube
    global completion_time

    if moving_animation is None:
        return

    target = moving_animation["target"]
    group = moving_animation["group"]

    tubes[target].extend(group)

    moves += 1

    tube_bounce[target] = 1

    moving_animation = None
    selected_tube = None

    if MIXER_OK:
        play_sound(drop_sound)

    if is_solved():

        create_confetti()

        if MIXER_OK:
            play_sound(complete_sound)

        best = save_data[
            "best_moves"
        ].get(
            str(current_level)
        )

        if (
            best is None
            or
            moves < best
        ):

            save_data[
                "best_moves"
            ][
                str(current_level)
            ] = moves

        save_data["unlocked"] = max(
            save_data.get(
                "unlocked",
                1
            ),
            min(
                100,
                current_level + 1
            )
        )

        save_game()

        completion_time = 0

        state_change(
            STATE_COMPLETE
        )


def update_animation(dt):

    if moving_animation is None:
        return

    moving_animation["progress"] += (
        dt / ANIMATION_TIME
    )

    if (
        moving_animation["progress"]
        >= 1
    ):

        moving_animation["progress"] = 1

        finish_move_animation()


# =========================================================
# UNDO
# =========================================================

def undo_move():

    global tubes
    global moves
    global selected_tube

    if moving_animation is not None:
        return

    if not history:
        return

    tubes = history.pop()

    moves = max(
        0,
        moves - 1
    )

    selected_tube = None


# =========================================================
# ÇÖZÜLDÜ MÜ?
# =========================================================

def is_solved():

    for tube in tubes:

        if not tube:
            continue

        if len(tube) != 4:
            return False

        first = tube[0]

        for piece in tube:

            if (
                piece["color"]
                != first["color"]
                or
                piece["shape"]
                != first["shape"]
            ):
                return False

    return True


# =========================================================
# TÜP FİZİĞİ
# =========================================================

def update_tube_physics(dt):

    for key in list(
        tube_bounce.keys()
    ):

        if tube_bounce[key] > 0:

            tube_bounce[key] -= (
                dt * 2.5
            )

            if tube_bounce[key] < 0:
                tube_bounce[key] = 0


# =========================================================
# KONFETİ
# =========================================================

def create_confetti():

    global confetti

    confetti = []

    for _ in range(100):

        confetti.append({
            "x": WIDTH // 2
            +
            random.randint(-250, 250),

            "y": 150
            +
            random.randint(-50, 40),

            "vx": random.uniform(
                -3.5,
                3.5
            ),

            "vy": random.uniform(
                -8,
                -3
            ),

            "size": random.randint(
                4,
                8
            ),

            "color": random.choice(
                COLORS
            ),

            "life": random.uniform(
                1.5,
                3
            )
        })


def update_confetti(dt):

    for p in confetti:

        p["x"] += (
            p["vx"] * 60 * dt
        )

        p["vy"] += (
            12 * dt
        )

        p["y"] += p["vy"]

        p["life"] -= dt

    confetti[:] = [
        p
        for p in confetti
        if p["life"] > 0
    ]


def draw_confetti():

    for p in confetti:

        pygame.draw.rect(
            screen,
            p["color"],
            (
                int(p["x"]),
                int(p["y"]),
                p["size"],
                p["size"] * 2
            )
        )


# =========================================================
# ANA MENÜ
# =========================================================

def draw_menu():

    draw_background()
    draw_menu_particles()

    # Hareketli şekiller
    menu_shapes = [
        (120, 160, 30, BLUE, "circle", 0),
        (850, 150, 28, PINK, "heart", 1),
        (180, 540, 27, YELLOW, "star", 2),
        (830, 530, 28, GREEN, "triangle", 3)
    ]

    for x, y, r, color, shape, phase in menu_shapes:

        bob = (
            math.sin(
                menu_time * 1.8
                +
                phase
            )
            * 8
        )

        draw_shape(
            screen,
            color,
            shape,
            x,
            int(y + bob),
            r
        )

    title1 = FONT_BIG.render(
        "SHAPE",
        True,
        WHITE
    )

    title2 = FONT_BIG.render(
        "LIQUID",
        True,
        BLUE
    )

    screen.blit(
        title1,
        (
            WIDTH // 2
            -
            title1.get_width() // 2,
            110
        )
    )

    screen.blit(
        title2,
        (
            WIDTH // 2
            -
            title2.get_width() // 2,
            165
        )
    )

    subtitle = FONT_SMALL.render(
        "Renkleri ve şekilleri doğru tüplerde birleştir!",
        True,
        (185, 205, 235)
    )

    screen.blit(
        subtitle,
        (
            WIDTH // 2
            -
            subtitle.get_width() // 2,
            235
        )
    )

    play_rect = pygame.Rect(
        WIDTH // 2 - 140,
        315,
        280,
        65
    )

    level_rect = pygame.Rect(
        WIDTH // 2 - 140,
        395,
        280,
        60
    )

    settings_rect = pygame.Rect(
        WIDTH // 2 - 140,
        470,
        280,
        60
    )

    draw_button(
        play_rect,
        "OYNA"
    )

    draw_button(
        level_rect,
        "BÖLÜMLER"
    )

    draw_button(
        settings_rect,
        "AYARLAR"
    )

    unlocked = save_data.get(
        "unlocked",
        1
    )

    progress = FONT_TINY.render(
        f"{unlocked - 1}/100 bölüm tamamlandı",
        True,
        (170, 185, 215)
    )

    screen.blit(
        progress,
        (
            WIDTH // 2
            -
            progress.get_width() // 2,
            565
        )
    )

    return (
        play_rect,
        level_rect,
        settings_rect
    )


# =========================================================
# BÖLÜM SEÇİM
# =========================================================

def draw_level_select(page):

    draw_background()

    draw_header(
        "BÖLÜM SEÇ"
    )

    start = (
        1
        if page == 0
        else 51
    )

    end = (
        50
        if page == 0
        else 100
    )

    unlocked = save_data.get(
        "unlocked",
        1
    )

    buttons = []

    cols = 10
    rows = 5

    button_w = 72
    button_h = 58

    gap_x = 17
    gap_y = 15

    total_w = (
        cols * button_w
        +
        (cols - 1) * gap_x
    )

    start_x = (
        WIDTH - total_w
    ) // 2

    start_y = 115

    level = start

    for row in range(rows):

        for col in range(cols):

            if level > end:
                break

            x = (
                start_x
                +
                col * (
                    button_w + gap_x
                )
            )

            y = (
                start_y
                +
                row * (
                    button_h + gap_y
                )
            )

            rect = pygame.Rect(
                x,
                y,
                button_w,
                button_h
            )

            available = (
                level <= unlocked
            )

            color = (
                (65, 150, 235)
                if available
                else
                (50, 55, 70)
            )

            pygame.draw.rect(
                screen,
                color,
                rect,
                border_radius=13
            )

            pygame.draw.rect(
                screen,
                (120, 195, 255),
                rect,
                width=2,
                border_radius=13
            )

            text = FONT_SMALL.render(
                str(level),
                True,
                WHITE
            )

            screen.blit(
                text,
                (
                    rect.centerx
                    -
                    text.get_width() // 2,
                    rect.y + 7
                )
            )

            best = save_data[
                "best_moves"
            ].get(
                str(level)
            )

            if best is not None:

                best_text = FONT_TINY.render(
                    str(best),
                    True,
                    (225, 240, 255)
                )

                screen.blit(
                    best_text,
                    (
                        rect.centerx
                        -
                        best_text.get_width() // 2,
                        rect.y + 33
                    )
                )

            buttons.append(
                (
                    rect,
                    level,
                    available
                )
            )

            level += 1

    back_rect = pygame.Rect(
        30,
        620,
        120,
        48
    )

    page_rect = pygame.Rect(
        WIDTH - 150,
        620,
        120,
        48
    )

    draw_button(
        back_rect,
        "GERİ",
        font=FONT_SMALL
    )

    draw_button(
        page_rect,
        "1-50"
        if page == 0
        else "51-100",
        font=FONT_SMALL
    )

    return (
        buttons,
        back_rect,
        page_rect
    )


# =========================================================
# OYUN EKRANI
# =========================================================

def draw_game():

    draw_background()

    draw_header(
        f"BÖLÜM {current_level}"
    )

    positions = get_tube_positions(
        len(tubes)
    )

    move_text = FONT_SMALL.render(
        f"Hamle: {moves}",
        True,
        WHITE
    )

    screen.blit(
        move_text,
        (30, 30)
    )

    best = save_data[
        "best_moves"
    ].get(
        str(current_level)
    )

    if best is not None:

        best_text = FONT_TINY.render(
            f"En iyi: {best}",
            True,
            (170, 200, 235)
        )

        screen.blit(
            best_text,
            (30, 58)
        )

    menu_rect = pygame.Rect(
        WIDTH - 150,
        22,
        120,
        44
    )

    undo_rect = pygame.Rect(
        30,
        HEIGHT - 70,
        120,
        45
    )

    restart_rect = pygame.Rect(
        WIDTH - 150,
        HEIGHT - 70,
        120,
        45
    )

    draw_button(
        menu_rect,
        "MENÜ",
        font=FONT_SMALL
    )

    draw_button(
        undo_rect,
        "GERİ AL",
        enabled=(
            bool(history)
            and
            moving_animation is None
        ),
        font=FONT_SMALL
    )

    draw_button(
        restart_rect,
        "YENİLE",
        font=FONT_SMALL
    )

    for i, rect in enumerate(
        positions
    ):

        x, y, w, h = rect

        if i == selected_tube:

            draw_selection(
                x,
                y,
                w,
                h
            )

        draw_tube(
            x,
            y,
            w,
            h,
            tube_bounce.get(i, 0)
        )

        draw_pieces(
            i,
            tubes[i],
            x,
            y,
            w,
            h
        )

    draw_moving_animation()


# =========================================================
# AYARLAR
# =========================================================

def draw_settings():

    draw_background()

    draw_header(
        "AYARLAR"
    )

    sound_rect = pygame.Rect(
        WIDTH // 2 - 150,
        180,
        300,
        65
    )

    music_rect = pygame.Rect(
        WIDTH // 2 - 150,
        270,
        300,
        65
    )

    back_rect = pygame.Rect(
        WIDTH // 2 - 100,
        400,
        200,
        55
    )

    sound_text = (
        "SES: AÇIK"
        if save_data.get(
            "sound",
            True
        )
        else
        "SES: KAPALI"
    )

    music_text = (
        "MÜZİK: AÇIK"
        if save_data.get(
            "music",
            True
        )
        else
        "MÜZİK: KAPALI"
    )

    draw_button(
        sound_rect,
        sound_text
    )

    draw_button(
        music_rect,
        music_text
    )

    draw_button(
        back_rect,
        "GERİ"
    )

    return (
        sound_rect,
        music_rect,
        back_rect
    )


# =========================================================
# TAMAMLAMA
# =========================================================

def draw_complete():

    draw_background()

    draw_confetti()

    pulse = (
        math.sin(
            completion_time * 4
        )
        + 1
    ) * 0.5

    radius = int(
        70 + pulse * 12
    )

    pygame.draw.circle(
        screen,
        (65, 150, 245),
        (
            WIDTH // 2,
            145
        ),
        radius
    )

    check = FONT_BIG.render(
        "✓",
        True,
        WHITE
    )

    screen.blit(
        check,
        (
            WIDTH // 2
            -
            check.get_width() // 2,
            105
        )
    )

    title = FONT_BIG.render(
        "BÖLÜM TAMAMLANDI!",
        True,
        WHITE
    )

    screen.blit(
        title,
        (
            WIDTH // 2
            -
            title.get_width() // 2,
            235
        )
    )

    move_text = FONT_MED.render(
        f"Hamle sayısı: {moves}",
        True,
        (200, 220, 245)
    )

    screen.blit(
        move_text,
        (
            WIDTH // 2
            -
            move_text.get_width() // 2,
            305
        )
    )

    best = save_data[
        "best_moves"
    ].get(
        str(current_level)
    )

    if best is not None:

        best_text = FONT_SMALL.render(
            f"En iyi: {best}",
            True,
            YELLOW
        )

        screen.blit(
            best_text,
            (
                WIDTH // 2
                -
                best_text.get_width() // 2,
                345
            )
        )

    again_rect = pygame.Rect(
        WIDTH // 2 - 145,
        410,
        290,
        55
    )

    next_rect = pygame.Rect(
        WIDTH // 2 - 145,
        480,
        290,
        55
    )

    menu_rect = pygame.Rect(
        WIDTH // 2 - 145,
        550,
        290,
        50
    )

    draw_button(
        again_rect,
        "TEKRAR"
    )

    draw_button(
        next_rect,
        "SONRAKİ BÖLÜM",
        enabled=(
            current_level < 100
        )
    )

    draw_button(
        menu_rect,
        "MENÜ"
    )

    return (
        again_rect,
        next_rect,
        menu_rect
    )


# =========================================================
# GEÇİŞ
# =========================================================

def update_transition(dt):

    global transition_alpha
    global transition_active

    if not transition_active:
        return

    transition_alpha -= (
        transition_speed * dt
    )

    if transition_alpha <= 0:

        transition_alpha = 0
        transition_active = False


def draw_transition():

    if not transition_active:
        return

    overlay = pygame.Surface(
        (
            WIDTH,
            HEIGHT
        ),
        pygame.SRCALPHA
    )

    overlay.fill(
        (
            3,
            7,
            15,
            int(transition_alpha)
        )
    )

    screen.blit(
        overlay,
        (0, 0)
    )


# =========================================================
# MENÜ
# =========================================================

def go_to_menu():

    global selected_tube
    global moving_animation

    selected_tube = None
    moving_animation = None

    state_change(
        STATE_MENU
    )


# =========================================================
# MENÜ TIKLAMA
# =========================================================

def handle_menu_click(pos):

    play_rect, level_rect, settings_rect = draw_menu()

    if play_rect.collidepoint(pos):

        start_level(
            save_data.get(
                "unlocked",
                1
            ),
            True
        )

    elif level_rect.collidepoint(pos):

        state_change(
            STATE_SELECT
        )

    elif settings_rect.collidepoint(pos):

        state_change(
            STATE_SETTINGS
        )


# =========================================================
# SEÇİM TIKLAMA
# =========================================================

def handle_level_click(pos):

    global level_page

    buttons, back_rect, page_rect = draw_level_select(
        level_page
    )

    for rect, level, available in buttons:

        if (
            rect.collidepoint(pos)
            and
            available
        ):

            start_level(
                level,
                True
            )

            return

    if back_rect.collidepoint(pos):

        state_change(
            STATE_MENU
        )

    elif page_rect.collidepoint(pos):

        level_page = 1 - level_page


# =========================================================
# AYAR TIKLAMA
# =========================================================

def handle_settings_click(pos):

    sound_rect, music_rect, back_rect = draw_settings()

    if sound_rect.collidepoint(pos):

        save_data["sound"] = not save_data.get(
            "sound",
            True
        )

        save_game()

    elif music_rect.collidepoint(pos):

        save_data["music"] = not save_data.get(
            "music",
            True
        )

        save_game()

        update_audio()

    elif back_rect.collidepoint(pos):

        state_change(
            STATE_MENU
        )


# =========================================================
# OYUN TIKLAMA
# =========================================================

def handle_game_click(pos):

    global selected_tube

    if moving_animation is not None:
        return

    positions = get_tube_positions(
        len(tubes)
    )

    menu_rect = pygame.Rect(
        WIDTH - 150,
        22,
        120,
        44
    )

    if menu_rect.collidepoint(pos):

        go_to_menu()
        return

    undo_rect = pygame.Rect(
        30,
        HEIGHT - 70,
        120,
        45
    )

    if undo_rect.collidepoint(pos):

        undo_move()
        return

    restart_rect = pygame.Rect(
        WIDTH - 150,
        HEIGHT - 70,
        120,
        45
    )

    if restart_rect.collidepoint(pos):

        start_level(
            current_level,
            True
        )

        return

    clicked = None

    for i, rect in enumerate(
        positions
    ):

        x, y, w, h = rect

        if pygame.Rect(
            x,
            y,
            w,
            h
        ).collidepoint(pos):

            clicked = i
            break

    if clicked is None:
        return

    if selected_tube is None:

        if tubes[clicked]:

            selected_tube = clicked

        return

    if clicked == selected_tube:

        selected_tube = None
        return

    if can_move(
        selected_tube,
        clicked
    ):

        move_group(
            selected_tube,
            clicked
        )

    else:

        if tubes[clicked]:

            selected_tube = clicked

        else:

            selected_tube = None


# =========================================================
# TAMAMLAMA TIKLAMA
# =========================================================

def handle_complete_click(pos):

    again_rect, next_rect, menu_rect = draw_complete()

    if again_rect.collidepoint(pos):

        start_level(
            current_level,
            True
        )

    elif (
        next_rect.collidepoint(pos)
        and
        current_level < 100
    ):

        start_level(
            current_level + 1,
            True
        )

    elif menu_rect.collidepoint(pos):

        go_to_menu()


# =========================================================
# ANA DÖNGÜ
# =========================================================

running = True

while running:

    dt = clock.tick(FPS) / 1000.0

    # -----------------------------------------------------
    # EVENT
    # -----------------------------------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            save_game()
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:

            pos = event.pos

            if state == STATE_MENU:

                handle_menu_click(pos)

            elif state == STATE_SELECT:

                handle_level_click(pos)

            elif state == STATE_SETTINGS:

                handle_settings_click(pos)

            elif state == STATE_GAME:

                handle_game_click(pos)

            elif state == STATE_COMPLETE:

                handle_complete_click(pos)

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                if state == STATE_GAME:

                    go_to_menu()

                elif state in (
                    STATE_SELECT,
                    STATE_SETTINGS
                ):

                    state_change(
                        STATE_MENU
                    )

                elif state == STATE_COMPLETE:

                    go_to_menu()

            elif (
                event.key == pygame.K_z
                and
                pygame.key.get_mods()
                &
                pygame.KMOD_CTRL
            ):

                if state == STATE_GAME:

                    undo_move()

            elif event.key == pygame.K_r:

                if state == STATE_GAME:

                    start_level(
                        current_level,
                        True
                    )

    # -----------------------------------------------------
    # UPDATE
    # -----------------------------------------------------

    if state == STATE_MENU:

        update_menu_animation(dt)

    elif state == STATE_GAME:

        game_time += dt

        update_animation(dt)

        update_tube_physics(dt)

    elif state == STATE_COMPLETE:

        completion_time += dt

        update_confetti(dt)

    update_transition(dt)

    # -----------------------------------------------------
    # DRAW
    # -----------------------------------------------------

    if state == STATE_MENU:

        draw_menu()

    elif state == STATE_SELECT:

        draw_level_select(
            level_page
        )

    elif state == STATE_SETTINGS:

        draw_settings()

    elif state == STATE_GAME:

        draw_game()

    elif state == STATE_COMPLETE:

        draw_complete()

    draw_transition()

    pygame.display.flip()


pygame.quit()
