import pygame
import random
import math
import json
import sys
from collections import deque

pygame.init()

# ==================================================
# SETTINGS
# ==================================================

TILE = 40
COLS = 22
ROWS = 16
HUD_H = 100

WIDTH = COLS * TILE
HEIGHT = ROWS * TILE + HUD_H

FPS = 60
SAVE_FILE = "savegame.json"

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dungeon Escape - Ultimate")
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("segoeui", 22, bold=True)
SMALL = pygame.font.SysFont("segoeui", 16, bold=True)
BIG = pygame.font.SysFont("segoeui", 44, bold=True)

# ==================================================
# COLORS
# ==================================================

WHITE = (240, 245, 255)
BLACK = (10, 10, 15)

GOLD = (255, 204, 55)
GREEN = (70, 225, 145)
RED = (240, 70, 100)
BLUE = (65, 165, 255)
CYAN = (130, 220, 255)
ORANGE = (255, 120, 30)

# ==================================================
# MAP THEMES
# ==================================================

THEMES = {
    "DESERT": {
        "floor1": (190, 145, 75),
        "floor2": (210, 165, 95),
        "wall": (110, 72, 38),
        "edge": (160, 110, 60),
        "obstacles": ["C", "R", "R", "B"]
    },

    "FOREST": {
        "floor1": (35, 85, 48),
        "floor2": (45, 105, 58),
        "wall": (55, 45, 30),
        "edge": (100, 75, 45),
        "obstacles": ["T", "T", "B", "R"]
    },

    "CAVE": {
        "floor1": (45, 48, 62),
        "floor2": (55, 58, 75),
        "wall": (30, 32, 42),
        "edge": (95, 100, 125),
        "obstacles": ["R", "R", "W"]
    },

    "ICE": {
        "floor1": (115, 170, 205),
        "floor2": (140, 195, 225),
        "wall": (55, 95, 140),
        "edge": (180, 225, 255),
        "obstacles": ["I", "I", "R", "W"]
    },

    "RUINS": {
        "floor1": (90, 85, 70),
        "floor2": (110, 105, 85),
        "wall": (50, 48, 42),
        "edge": (145, 135, 110),
        "obstacles": ["R", "P", "B", "R"]
    }
}

THEME_NAMES = list(THEMES.keys())

# ==================================================
# SAVE SYSTEM
# ==================================================

def load_save():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        checkpoint = int(data.get("checkpoint", 1))
        best_level = int(data.get("best_level", 1))
        best_score = int(data.get("best_score", 0))

        checkpoint = max(1, min(20, checkpoint))

        return checkpoint, best_level, best_score

    except (FileNotFoundError, json.JSONDecodeError,
            ValueError, TypeError):
        return 1, 1, 0


def save_game():
    data = {
        "checkpoint": checkpoint,
        "best_level": best_level,
        "best_score": best_score
    }

    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    except OSError:
        pass


saved_checkpoint, best_level, best_score = load_save()

# ==================================================
# GLOBAL GAME VARIABLES
# ==================================================

world = []
current_theme = "DESERT"

player = pygame.Rect(
    2 * TILE + 8,
    2 * TILE + 8,
    25,
    30
)

facing = 1

level = saved_checkpoint
checkpoint = saved_checkpoint

score = 0
lives = 3
has_key = False

game_state = "playing"

shoot_timer = 0
damage_timer = 0

enemies = []
bullets = []
coins = []

enemy_projectiles = []
warning_zones = []

key_rect = pygame.Rect(0, 0, 20, 20)
exit_rect = pygame.Rect(0, 0, TILE, TILE)

# ==================================================
# TEXT
# ==================================================

def draw_text(text, font, color, x, y, center=False):
    image = font.render(str(text), True, color)
    rect = image.get_rect()

    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    screen.blit(image, rect)


# ==================================================
# COLLISION
# ==================================================

def tile_blocked(rect):
    left = max(0, rect.left // TILE)
    right = min(COLS - 1, (rect.right - 1) // TILE)

    top = max(0, rect.top // TILE)
    bottom = min(ROWS - 1, (rect.bottom - 1) // TILE)

    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            if world[y][x] != ".":
                return True

    return False


def move_solid(rect, dx, dy):
    mx = round(dx)
    my = round(dy)

    if mx == 0 and dx != 0:
        mx = 1 if dx > 0 else -1

    if my == 0 and dy != 0:
        my = 1 if dy > 0 else -1

    rect.x += mx

    if tile_blocked(rect):
        rect.x -= mx

    rect.y += my

    if tile_blocked(rect):
        rect.y -= my


# ==================================================
# PATHFINDING
# ==================================================

def get_reachable_tiles(start):
    queue = deque([start])
    visited = {start}

    directions = [
        (1, 0),
        (-1, 0),
        (0, 1),
        (0, -1)
    ]

    while queue:
        x, y = queue.popleft()

        for dx, dy in directions:
            nx = x + dx
            ny = y + dy

            if not (0 <= nx < COLS and 0 <= ny < ROWS):
                continue

            if world[ny][nx] != ".":
                continue

            if (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny))

    return visited


def find_path(start, goal):
    if start == goal:
        return []

    queue = deque([start])
    came_from = {start: None}

    directions = [
        (1, 0),
        (-1, 0),
        (0, 1),
        (0, -1)
    ]

    while queue:
        current = queue.popleft()

        if current == goal:
            break

        for dx, dy in directions:
            nxt = (
                current[0] + dx,
                current[1] + dy
            )

            if not (
                0 <= nxt[0] < COLS
                and 0 <= nxt[1] < ROWS
            ):
                continue

            if world[nxt[1]][nxt[0]] != ".":
                continue

            if nxt not in came_from:
                came_from[nxt] = current
                queue.append(nxt)

    if goal not in came_from:
        return []

    path = []
    current = goal

    while current != start:
        path.append(current)
        current = came_from[current]

    path.reverse()
    return path


# ==================================================
# MAP GENERATION
# ==================================================

def make_map(stage):
    global world, current_theme

    current_theme = THEME_NAMES[
        (stage - 1) % len(THEME_NAMES)
    ]

    theme = THEMES[current_theme]

    world = [
        ["." for _ in range(COLS)]
        for _ in range(ROWS)
    ]

    # Border
    for y in range(ROWS):
        for x in range(COLS):
            if (
                x == 0
                or y == 0
                or x == COLS - 1
                or y == ROWS - 1
            ):
                world[y][x] = "#"

    spawn = (2, 2)
    exit_tile = (COLS - 3, ROWS - 3)

    # Random obstacles
    obstacle_count = min(15 + stage * 2, 60)

    for _ in range(obstacle_count):
        x = random.randint(2, COLS - 3)
        y = random.randint(2, ROWS - 3)

        if abs(x - spawn[0]) <= 2 and abs(y - spawn[1]) <= 2:
            continue

        if abs(x - exit_tile[0]) <= 2 and abs(y - exit_tile[1]) <= 2:
            continue

        world[y][x] = random.choice(theme["obstacles"])

    # Clear spawn area
    for y in range(1, 5):
        for x in range(1, 5):
            world[y][x] = "."

    # Clear exit area
    for y in range(ROWS - 5, ROWS - 1):
        for x in range(COLS - 5, COLS - 1):
            world[y][x] = "."

    # Create a guaranteed path
    x, y = spawn

    while x != exit_tile[0]:
        x += 1 if x < exit_tile[0] else -1
        world[y][x] = "."

    while y != exit_tile[1]:
        y += 1 if y < exit_tile[1] else -1
        world[y][x] = "."

    return get_reachable_tiles(spawn)


# ==================================================
# MAP DRAWING
# ==================================================

def draw_map():
    theme = THEMES[current_theme]

    screen.fill((12, 14, 25))

    for y in range(ROWS):
        for x in range(COLS):
            tile = pygame.Rect(
                x * TILE,
                y * TILE,
                TILE,
                TILE
            )

            kind = world[y][x]

            if kind == ".":
                color = (
                    theme["floor1"]
                    if (x + y) % 2 == 0
                    else theme["floor2"]
                )

                pygame.draw.rect(screen, color, tile)

                if current_theme == "DESERT":
                    if (x * 3 + y) % 7 == 0:
                        pygame.draw.circle(
                            screen,
                            (225, 185, 115),
                            tile.center,
                            2
                        )

                elif current_theme == "FOREST":
                    if (x + y * 2) % 8 == 0:
                        pygame.draw.circle(
                            screen,
                            (65, 130, 70),
                            tile.center,
                            3
                        )

                elif current_theme == "ICE":
                    if (x + y) % 6 == 0:
                        pygame.draw.line(
                            screen,
                            (190, 230, 255),
                            tile.topleft,
                            tile.bottomright,
                            2
                        )

            else:
                pygame.draw.rect(
                    screen,
                    theme["wall"],
                    tile
                )

                pygame.draw.rect(
                    screen,
                    theme["edge"],
                    tile,
                    2
                )

                # Trees
                if kind == "T":
                    pygame.draw.rect(
                        screen,
                        (75, 45, 25),
                        (
                            tile.centerx - 5,
                            tile.y + 20,
                            10,
                            18
                        )
                    )

                    pygame.draw.circle(
                        screen,
                        (25, 100, 45),
                        (tile.centerx, tile.y + 15),
                        17
                    )

                    pygame.draw.circle(
                        screen,
                        (40, 135, 55),
                        (tile.centerx - 5, tile.y + 10),
                        11
                    )

                # Cactus
                elif kind == "C":
                    pygame.draw.rect(
                        screen,
                        (35, 125, 65),
                        (
                            tile.centerx - 5,
                            tile.y + 8,
                            10,
                            28
                        ),
                        border_radius=4
                    )

                    pygame.draw.rect(
                        screen,
                        (35, 125, 65),
                        (
                            tile.centerx - 15,
                            tile.y + 15,
                            10,
                            5
                        ),
                        border_radius=3
                    )

                # Rock
                elif kind == "R":
                    pygame.draw.ellipse(
                        screen,
                        (100, 105, 115),
                        (
                            tile.x + 5,
                            tile.y + 7,
                            30,
                            28
                        )
                    )

                    pygame.draw.ellipse(
                        screen,
                        (140, 145, 155),
                        (
                            tile.x + 9,
                            tile.y + 9,
                            16,
                            9
                        )
                    )

                # Bush
                elif kind == "B":
                    pygame.draw.circle(
                        screen,
                        (35, 115, 55),
                        tile.center,
                        14
                    )

                    pygame.draw.circle(
                        screen,
                        (55, 145, 65),
                        (
                            tile.centerx - 7,
                            tile.centery - 5
                        ),
                        8
                    )

                # Water
                elif kind == "W":
                    pygame.draw.rect(
                        screen,
                        (35, 115, 190),
                        (
                            tile.x + 3,
                            tile.y + 5,
                            34,
                            30
                        ),
                        border_radius=8
                    )

                    pygame.draw.line(
                        screen,
                        (125, 210, 255),
                        (
                            tile.x + 8,
                            tile.y + 14
                        ),
                        (
                            tile.x + 28,
                            tile.y + 14
                        ),
                        2
                    )

                # Ice
                elif kind == "I":
                    pygame.draw.polygon(
                        screen,
                        (175, 230, 255),
                        [
                            (tile.centerx, tile.y + 3),
                            (tile.x + 8, tile.y + 30),
                            (tile.centerx, tile.y + 25),
                            (tile.right - 8, tile.y + 30)
                        ]
                    )

                # Pillar
                elif kind == "P":
                    pygame.draw.rect(
                        screen,
                        (155, 145, 120),
                        (
                            tile.x + 8,
                            tile.y + 5,
                            24,
                            30
                        )
                    )

                    pygame.draw.rect(
                        screen,
                        (190, 180, 150),
                        (
                            tile.x + 5,
                            tile.y + 5,
                            30,
                            6
                        )
                    )


# ==================================================
# PLAYER DRAWING
# ==================================================

def draw_player(rect, direction):
    pygame.draw.ellipse(
        screen,
        (8, 10, 18),
        (
            rect.x - 3,
            rect.bottom - 4,
            rect.w + 6,
            9
        )
    )

    # Legs
    pygame.draw.rect(
        screen,
        (29, 38, 64),
        (
            rect.x + 5,
            rect.bottom - 9,
            8,
            10
        ),
        border_radius=3
    )

    pygame.draw.rect(
        screen,
        (29, 38, 64),
        (
            rect.right - 13,
            rect.bottom - 9,
            8,
            10
        ),
        border_radius=3
    )

    # Armor
    pygame.draw.rect(
        screen,
        BLUE,
        (
            rect.x + 3,
            rect.y + 11,
            rect.w - 6,
            rect.h - 12
        ),
        border_radius=6
    )

    pygame.draw.rect(
        screen,
        (145, 210, 255),
        (
            rect.x + 6,
            rect.y + 14,
            rect.w - 12,
            6
        ),
        border_radius=2
    )

    # Helmet
    pygame.draw.rect(
        screen,
        (194, 207, 230),
        (
            rect.x + 5,
            rect.y + 1,
            rect.w - 10,
            15
        ),
        border_radius=5
    )

    pygame.draw.rect(
        screen,
        (76, 94, 134),
        (
            rect.x + 4,
            rect.y + 8,
            rect.w - 8,
            5
        )
    )

    eye_x = rect.centerx + (
        5 if direction > 0 else -7
    )

    pygame.draw.rect(
        screen,
        (20, 28, 45),
        (eye_x, rect.y + 7, 4, 3)
    )

    # Sword
    if direction > 0:
        pygame.draw.rect(
            screen,
            CYAN,
            (
                rect.right - 1,
                rect.y + 17,
                14,
                4
            ),
            border_radius=2
        )

        pygame.draw.rect(
            screen,
            GOLD,
            (
                rect.right - 3,
                rect.y + 14,
                4,
                10
            )
        )

    else:
        pygame.draw.rect(
            screen,
            CYAN,
            (
                rect.left - 13,
                rect.y + 17,
                14,
                4
            ),
            border_radius=2
        )

        pygame.draw.rect(
            screen,
            GOLD,
            (
                rect.left - 1,
                rect.y + 14,
                4,
                10
            )
        )


# ==================================================
# ENEMY DRAWING
# ==================================================

def draw_monster(enemy):
    rect = enemy["rect"]
    kind = enemy["kind"]

    pygame.draw.ellipse(
        screen,
        (8, 10, 18),
        (
            rect.x - 3,
            rect.bottom - 4,
            rect.w + 6,
            9
        )
    )

    # Slime
    if kind == "slime":
        pygame.draw.ellipse(
            screen,
            (45, 190, 100),
            rect
        )

        pygame.draw.circle(
            screen,
            (180, 255, 210),
            (rect.x + 9, rect.y + 12),
            4
        )

        pygame.draw.circle(
            screen,
            (180, 255, 210),
            (rect.right - 9, rect.y + 12),
            4
        )

    # Skeleton
    elif kind == "skeleton":
        pygame.draw.rect(
            screen,
            (210, 210, 220),
            (
                rect.x + 4,
                rect.y + 8,
                rect.w - 8,
                rect.h - 8
            ),
            border_radius=5
        )

        pygame.draw.rect(
            screen,
            (45, 45, 60),
            (
                rect.x + 5,
                rect.y + 8,
                rect.w - 10,
                12
            )
        )

        pygame.draw.rect(
            screen,
            RED,
            (rect.x + 7, rect.y + 11, 5, 4)
        )

        pygame.draw.rect(
            screen,
            RED,
            (rect.right - 12, rect.y + 11, 5, 4)
        )

    # Demon
    elif kind == "demon":
        pygame.draw.rect(
            screen,
            (130, 30, 55),
            (
                rect.x + 2,
                rect.y + 8,
                rect.w - 4,
                rect.h - 8
            ),
            border_radius=8
        )

        pygame.draw.polygon(
            screen,
            (220, 50, 65),
            [
                (rect.x + 5, rect.y + 10),
                (rect.x + 1, rect.y - 3),
                (rect.x + 15, rect.y + 8)
            ]
        )

        pygame.draw.polygon(
            screen,
            (220, 50, 65),
            [
                (rect.right - 5, rect.y + 10),
                (rect.right - 1, rect.y - 3),
                (rect.right - 15, rect.y + 8)
            ]
        )

        pygame.draw.circle(
            screen,
            GOLD,
            (rect.x + 9, rect.y + 14),
            3
        )

        pygame.draw.circle(
            screen,
            GOLD,
            (rect.right - 9, rect.y + 14),
            3
        )

    # Ghost
    elif kind == "ghost":
        pygame.draw.ellipse(
            screen,
            (175, 210, 255),
            rect
        )

        pygame.draw.circle(
            screen,
            (30, 45, 90),
            (rect.x + 9, rect.y + 13),
            4
        )

        pygame.draw.circle(
            screen,
            (30, 45, 90),
            (rect.right - 9, rect.y + 13),
            4
        )

    # Orc
    elif kind == "orc":
        pygame.draw.rect(
            screen,
            (90, 130, 45),
            (
                rect.x + 2,
                rect.y + 7,
                rect.w - 4,
                rect.h - 7
            ),
            border_radius=7
        )

        pygame.draw.circle(
            screen,
            RED,
            (rect.x + 9, rect.y + 12),
            3
        )

        pygame.draw.circle(
            screen,
            RED,
            (rect.right - 9, rect.y + 12),
            3
        )

    # Archer
    elif kind == "archer":
        pygame.draw.rect(
            screen,
            (70, 100, 160),
            (
                rect.x + 2,
                rect.y + 8,
                rect.w - 4,
                rect.h - 8
            ),
            border_radius=6
        )

        pygame.draw.circle(
            screen,
            (230, 230, 245),
            (rect.centerx, rect.y + 8),
            10
        )

        pygame.draw.line(
            screen,
            (210, 180, 120),
            (rect.right, rect.centery),
            (rect.right + 12, rect.centery),
            3
        )

    # Fire Mage
    elif kind == "fire_mage":
        pygame.draw.rect(
            screen,
            (110, 35, 150),
            (
                rect.x + 2,
                rect.y + 8,
                rect.w - 4,
                rect.h - 8
            ),
            border_radius=8
        )

        pygame.draw.circle(
            screen,
            ORANGE,
            rect.center,
            8
        )

    # Jumper
    elif kind == "jumper":
        pygame.draw.rect(
            screen,
            (190, 90, 35),
            (
                rect.x + 2,
                rect.y + 8,
                rect.w - 4,
                rect.h - 8
            ),
            border_radius=8
        )

        pygame.draw.polygon(
            screen,
            (255, 170, 60),
            [
                (rect.x + 5, rect.y + 8),
                (rect.centerx, rect.y - 8),
                (rect.right - 5, rect.y + 8)
            ]
        )

    # Brute
    elif kind == "brute":
        pygame.draw.rect(
            screen,
            (80, 80, 90),
            (
                rect.x - 4,
                rect.y + 5,
                rect.w + 8,
                rect.h - 5
            ),
            border_radius=6
        )

        pygame.draw.circle(
            screen,
            RED,
            (rect.x + 9, rect.y + 12),
            4
        )

        pygame.draw.circle(
            screen,
            RED,
            (rect.right - 9, rect.y + 12),
            4
        )

    # Health bar
    bar_w = rect.w

    pygame.draw.rect(
        screen,
        (50, 20, 30),
        (rect.x, rect.y - 7, bar_w, 4)
    )

    current_w = int(
        bar_w * enemy["hp"] / enemy["max_hp"]
    )

    pygame.draw.rect(
        screen,
        GREEN,
        (rect.x, rect.y - 7, current_w, 4)
    )


# ==================================================
# LEVEL CREATION
# ==================================================

def random_open_tile(occupied, reachable):
    tiles = list(reachable)
    random.shuffle(tiles)

    for x, y in tiles:
        rect = pygame.Rect(
            x * TILE + 7,
            y * TILE + 7,
            26,
            28
        )

        if any(rect.colliderect(other) for other in occupied):
            continue

        return rect

    return pygame.Rect(
        12 * TILE,
        7 * TILE,
        26,
        28
    )


def create_level(stage):
    global enemies, coins, bullets
    global enemy_projectiles, warning_zones
    global key_rect, exit_rect

    bullets = []
    enemies = []
    coins = []

    enemy_projectiles = []
    warning_zones = []

    reachable = make_map(stage)

    exit_rect = pygame.Rect(
        (COLS - 3) * TILE,
        (ROWS - 3) * TILE,
        TILE,
        TILE
    )

    possible_keys = list(
        reachable - {
            (2, 2),
            (COLS - 3, ROWS - 3)
        }
    )

    key_tile = random.choice(possible_keys)

    key_rect = pygame.Rect(
        key_tile[0] * TILE + 10,
        key_tile[1] * TILE + 10,
        20,
        20
    )

    occupied = [
        pygame.Rect(
            2 * TILE,
            2 * TILE,
            55,
            60
        ),
        exit_rect,
        key_rect
    ]

    # Enemy types unlock gradually
    if stage <= 3:
        available = [
            "slime",
            "skeleton"
        ]

    elif stage <= 6:
        available = [
            "slime",
            "skeleton",
            "orc"
        ]

    elif stage <= 10:
        available = [
            "skeleton",
            "orc",
            "archer"
        ]

    elif stage <= 14:
        available = [
            "archer",
            "fire_mage",
            "jumper",
            "ghost"
        ]

    else:
        available = [
            "archer",
            "fire_mage",
            "jumper",
            "brute",
            "demon",
            "orc"
        ]

    enemy_count = min(3 + stage, 15)

    enemy_speed = 55 + stage * 3
    enemy_hp = 1 + (stage - 1) // 4

    for _ in range(enemy_count):
        er = random_open_tile(occupied, reachable)
        occupied.append(er)

        kind = random.choice(available)

        enemies.append({
            "rect": er,
            "hp": enemy_hp,
            "max_hp": enemy_hp,
            "speed": enemy_speed + random.randint(-8, 12),
            "kind": kind,
            "path_timer": random.random(),
            "path": [],
            "attack_cd": random.uniform(1.5, 3.5),
            "attack": 0
        })

    # Coins
    for _ in range(5 + stage // 2):
        coin_rect = random_open_tile(occupied, reachable)

        coin_rect = pygame.Rect(
            coin_rect.x + 6,
            coin_rect.y + 6,
            14,
            14
        )

        occupied.append(coin_rect)
        coins.append(coin_rect)


# ==================================================
# ENEMY MOVEMENT
# ==================================================

def update_enemy_path(enemy, dt):
    enemy["path_timer"] -= dt

    if enemy["path_timer"] <= 0:
        enemy["path_timer"] = 0.30

        start = (
            enemy["rect"].centerx // TILE,
            enemy["rect"].centery // TILE
        )

        goal = (
            player.centerx // TILE,
            player.centery // TILE
        )

        enemy["path"] = find_path(start, goal)

    path = enemy.get("path", [])

    if not path:
        return

    target_x = path[0][0] * TILE + TILE // 2
    target_y = path[0][1] * TILE + TILE // 2

    vx = target_x - enemy["rect"].centerx
    vy = target_y - enemy["rect"].centery

    distance = math.hypot(vx, vy)

    if distance < 4:
        enemy["path"] = path[1:]
        return

    speed = enemy["speed"]

    move_solid(
        enemy["rect"],
        vx / distance * speed * dt,
        vy / distance * speed * dt
    )


# ==================================================
# DAMAGE SYSTEM
# ==================================================

def damage_player(amount=1):
    global lives, damage_timer, game_state

    if damage_timer > 0:
        return

    lives -= amount
    damage_timer = 1.2

    if lives <= 0:
        lives = 0
        game_state = "lost"


# ==================================================
# ENEMY ATTACKS
# ==================================================

def enemy_attack(enemy):
    kind = enemy["kind"]
    rect = enemy["rect"]

    # ARCHER: arrow
    if kind == "archer":
        dx = player.centerx - rect.centerx
        dy = player.centery - rect.centery

        distance = max(1, math.hypot(dx, dy))

        enemy_projectiles.append({
            "x": rect.centerx,
            "y": rect.centery,
            "dx": dx / distance * 230,
            "dy": dy / distance * 230,
            "type": "arrow"
        })

    # FIRE MAGE: fire on player's tile
    elif kind == "fire_mage":
        target = pygame.Rect(
            (player.centerx // TILE) * TILE,
            (player.centery // TILE) * TILE,
            TILE,
            TILE
        )

        warning_zones.append({
            "rect": target,
            "timer": 0.75,
            "type": "fire"
        })

    # JUMPER: jump attack
    elif kind == "jumper":
        target = pygame.Rect(
            (player.centerx // TILE) * TILE,
            (player.centery // TILE) * TILE,
            TILE,
            TILE
        )

        warning_zones.append({
            "rect": target,
            "timer": 0.85,
            "type": "jump"
        })

    # BRUTE: heavy nearby attack
    elif kind == "brute":
        if rect.inflate(35, 35).colliderect(player):
            damage_player(1)

    # DEMON: fireball
    elif kind == "demon":
        dx = player.centerx - rect.centerx
        dy = player.centery - rect.centery

        distance = max(1, math.hypot(dx, dy))

        enemy_projectiles.append({
            "x": rect.centerx,
            "y": rect.centery,
            "dx": dx / distance * 180,
            "dy": dy / distance * 180,
            "type": "fireball"
        })


def update_enemy_attacks(dt):
    # Attack cooldowns
    for enemy in enemies:
        enemy["attack_cd"] -= dt

        if enemy["attack_cd"] <= 0:
            enemy_attack(enemy)

            # Higher levels attack faster
            cooldown = max(
                0.65,
                3.0 - level * 0.09
            )

            enemy["attack_cd"] = random.uniform(
                cooldown,
                cooldown + 1.0
            )

    # Update projectiles
    for projectile in enemy_projectiles[:]:
        projectile["x"] += projectile["dx"] * dt
        projectile["y"] += projectile["dy"] * dt

        projectile_rect = pygame.Rect(
            int(projectile["x"] - 6),
            int(projectile["y"] - 6),
            12,
            12
        )

        if projectile_rect.colliderect(player):
            damage_player()

            enemy_projectiles.remove(projectile)
            continue

        if (
            projectile["x"] < 0
            or projectile["x"] > WIDTH
            or projectile["y"] < 0
            or projectile["y"] > ROWS * TILE
        ):
            enemy_projectiles.remove(projectile)

    # Warning zones
    for warning in warning_zones[:]:
        warning["timer"] -= dt

        if warning["timer"] <= 0:
            if warning["rect"].colliderect(player):
                damage_player()

            warning_zones.remove(warning)


# ==================================================
# GAME STATE FUNCTIONS
# ==================================================

def restart_at_checkpoint():
    global level, lives, has_key, game_state
    global shoot_timer, damage_timer

    level = checkpoint
    lives = 3
    has_key = False
    game_state = "playing"

    player.x = 2 * TILE + 8
    player.y = 2 * TILE + 8

    shoot_timer = 0
    damage_timer = 0

    create_level(level)


def start_new_run():
    global level, checkpoint, lives, score
    global has_key, game_state

    level = 1
    checkpoint = 1
    lives = 3
    score = 0
    has_key = False
    game_state = "playing"

    save_game()
    restart_at_checkpoint()


def save_checkpoint_if_needed():
    global checkpoint

    if level in (6, 11, 16):
        checkpoint = level
        save_game()


# ==================================================
# CREATE FIRST LEVEL
# ==================================================

create_level(level)

# ==================================================
# MAIN LOOP
# ==================================================

while True:
    dt = clock.tick(FPS) / 1000

    # ------------------------------------------------
    # EVENTS
    # ------------------------------------------------

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            if (
                event.key == pygame.K_r
                and game_state in ("lost", "won_all")
            ):
                start_new_run()

            if (
                event.key == pygame.K_c
                and game_state == "lost"
            ):
                restart_at_checkpoint()

            if (
                event.key == pygame.K_SPACE
                and game_state == "playing"
                and shoot_timer <= 0
            ):
                bullet = pygame.Rect(
                    player.centerx + facing * 17,
                    player.centery - 4,
                    16,
                    8
                )

                bullets.append({
                    "rect": bullet,
                    "dx": facing * 9
                })

                shoot_timer = 0.20

    # ------------------------------------------------
    # UPDATE
    # ------------------------------------------------

    if game_state == "playing":
        shoot_timer = max(0, shoot_timer - dt)
        damage_timer = max(0, damage_timer - dt)

        keys = pygame.key.get_pressed()

        dx = int(
            keys[pygame.K_d] or keys[pygame.K_RIGHT]
        ) - int(
            keys[pygame.K_a] or keys[pygame.K_LEFT]
        )

        dy = int(
            keys[pygame.K_s] or keys[pygame.K_DOWN]
        ) - int(
            keys[pygame.K_w] or keys[pygame.K_UP]
        )

        if dx:
            facing = 1 if dx > 0 else -1

        if dx or dy:
            length = math.hypot(dx, dy)

            move_solid(
                player,
                dx / length * 235 * dt,
                dy / length * 235 * dt
            )

        # --------------------------------------------
        # PLAYER BULLETS
        # --------------------------------------------

        for bullet in bullets[:]:
            bullet["rect"].x += bullet["dx"]

            if (
                bullet["rect"].right < 0
                or bullet["rect"].left > WIDTH
                or tile_blocked(bullet["rect"])
            ):
                bullets.remove(bullet)
                continue

            hit = False

            for enemy in enemies[:]:
                if bullet["rect"].colliderect(enemy["rect"]):
                    enemy["hp"] -= 1
                    hit = True

                    if enemy["hp"] <= 0:
                        enemies.remove(enemy)

                        score += 50 + level * 5
                        best_score = max(best_score, score)

                        if random.random() < 0.6:
                            coins.append(pygame.Rect(
                                enemy["rect"].centerx - 7,
                                enemy["rect"].centery - 7,
                                14,
                                14
                            ))

                    break

            if hit and bullet in bullets:
                bullets.remove(bullet)

        # --------------------------------------------
        # ENEMY MOVEMENT
        # --------------------------------------------

        for enemy in enemies:
            update_enemy_path(enemy, dt)

        # --------------------------------------------
        # ENEMY ATTACKS
        # --------------------------------------------

        update_enemy_attacks(dt)

        # --------------------------------------------
        # CONTACT DAMAGE
        # --------------------------------------------

        for enemy in enemies:
            if player.colliderect(enemy["rect"]):
                if damage_timer <= 0:
                    damage_player()

                    vx = player.centerx - enemy["rect"].centerx
                    vy = player.centery - enemy["rect"].centery

                    distance = max(
                        1,
                        math.hypot(vx, vy)
                    )

                    player.x += int(vx / distance * 30)
                    player.y += int(vy / distance * 30)

                    player.clamp_ip(pygame.Rect(
                        TILE,
                        TILE,
                        WIDTH - TILE * 2,
                        ROWS * TILE - TILE * 2
                    ))

        # --------------------------------------------
        # KEY
        # --------------------------------------------

        if not has_key and player.colliderect(key_rect):
            has_key = True
            score += 100

        # --------------------------------------------
        # COINS
        # --------------------------------------------

        for coin in coins[:]:
            if player.colliderect(coin):
                coins.remove(coin)
                score += 10

        # --------------------------------------------
        # EXIT
        # --------------------------------------------

        if (
            player.colliderect(exit_rect)
            and has_key
            and not enemies
        ):
            if level >= 20:
                game_state = "won_all"

                best_level = 20
                best_score = max(best_score, score)

                save_game()

            else:
                level += 1

                best_level = max(best_level, level)

                has_key = False
                lives = min(3, lives + 1)

                player.x = 2 * TILE + 8
                player.y = 2 * TILE + 8

                create_level(level)

                save_checkpoint_if_needed()
                save_game()

    # ------------------------------------------------
    # DRAW
    # ------------------------------------------------

    draw_map()

    # --------------------------------------------
    # EXIT
    # --------------------------------------------

    pygame.draw.rect(
        screen,
        (75, 45, 35),
        exit_rect,
        border_radius=5
    )

    exit_color = (
        GREEN
        if has_key and not enemies
        else RED
    )

    pygame.draw.rect(
        screen,
        exit_color,
        (
            exit_rect.x + 7,
            exit_rect.y + 5,
            26,
            30
        ),
        border_radius=4
    )

    pygame.draw.circle(
        screen,
        GOLD,
        (
            exit_rect.right - 10,
            exit_rect.centery
        ),
        3
    )

    # --------------------------------------------
    # KEY
    # --------------------------------------------

    if not has_key:
        pygame.draw.circle(
            screen,
            GOLD,
            key_rect.center,
            10
        )

        pygame.draw.circle(
            screen,
            (255, 240, 160),
            key_rect.center,
            4
        )

        pygame.draw.rect(
            screen,
            GOLD,
            (
                key_rect.centerx + 6,
                key_rect.centery - 2,
                10,
                4
            )
        )

        pygame.draw.rect(
            screen,
            GOLD,
            (
                key_rect.centerx + 12,
                key_rect.centery - 2,
                3,
                7
            )
        )

    # --------------------------------------------
    # COINS
    # --------------------------------------------

    for coin in coins:
        pygame.draw.circle(
            screen,
            GOLD,
            coin.center,
            8
        )

        pygame.draw.circle(
            screen,
            (255, 240, 160),
            coin.center,
            3
        )

    # --------------------------------------------
    # PLAYER BULLETS
    # --------------------------------------------

    for bullet in bullets:
        pygame.draw.rect(
            screen,
            CYAN,
            bullet["rect"],
            border_radius=4
        )

        pygame.draw.rect(
            screen,
            WHITE,
            (
                bullet["rect"].x + 3,
                bullet["rect"].y + 2,
                5,
                3
            ),
            border_radius=2
        )

    # --------------------------------------------
    # ENEMY PROJECTILES
    # --------------------------------------------

    for projectile in enemy_projectiles:
        if projectile["type"] == "arrow":
            color = (220, 220, 230)
        else:
            color = ORANGE

        pygame.draw.circle(
            screen,
            color,
            (
                int(projectile["x"]),
                int(projectile["y"])
            ),
            7
        )

    # --------------------------------------------
    # WARNING ZONES
    # --------------------------------------------

    for warning in warning_zones:
        rect = warning["rect"]

        # Red warning tile
        pygame.draw.rect(
            screen,
            (210, 30, 40),
            rect
        )

        pygame.draw.rect(
            screen,
            (255, 100, 100),
            rect,
            3
        )

        # Countdown bar
        bar_width = int(
            TILE * warning["timer"] / 0.85
        )

        pygame.draw.rect(
            screen,
            WHITE,
            (
                rect.x,
                rect.y,
                bar_width,
                5
            )
        )

    # --------------------------------------------
    # ENEMIES
    # --------------------------------------------

    for enemy in enemies:
        draw_monster(enemy)

    # --------------------------------------------
    # PLAYER
    # --------------------------------------------

    if (
        damage_timer <= 0
        or int(damage_timer * 12) % 2 == 0
    ):
        draw_player(player, facing)

    # ------------------------------------------------
    # HUD
    # ------------------------------------------------

    hud_y = ROWS * TILE

    pygame.draw.rect(
        screen,
        (17, 20, 34),
        (0, hud_y, WIDTH, HUD_H)
    )

    pygame.draw.line(
        screen,
        (100, 110, 160),
        (0, hud_y),
        (WIDTH, hud_y),
        3
    )

    draw_text(
        f"LEVEL {level}/20",
        FONT,
        CYAN,
        18,
        hud_y + 12
    )

    draw_text(
        f"SCORE {score}",
        FONT,
        GOLD,
        190,
        hud_y + 12
    )

    draw_text(
        f"LIVES {lives}",
        FONT,
        RED,
        370,
        hud_y + 12
    )

    draw_text(
        f"KEY {'YES' if has_key else 'NO'}",
        FONT,
        GREEN if has_key else WHITE,
        530,
        hud_y + 12
    )

    draw_text(
        f"MAP: {current_theme}",
        SMALL,
        GOLD,
        18,
        hud_y + 52
    )

    draw_text(
        "WASD/ARROWS MOVE | SPACE SHOOT",
        SMALL,
        WHITE,
        190,
        hud_y + 52
    )

    draw_text(
        f"CHECKPOINT: {checkpoint}",
        SMALL,
        GREEN,
        600,
        hud_y + 52
    )

    # ------------------------------------------------
    # END SCREENS
    # ------------------------------------------------

    if game_state in ("lost", "won_all"):
        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill((5, 7, 15, 215))
        screen.blit(overlay, (0, 0))

        if game_state == "lost":
            draw_text(
                "RUN OVER",
                BIG,
                RED,
                WIDTH // 2,
                HEIGHT // 2 - 60,
                center=True
            )

            draw_text(
                f"You reached level {level}",
                FONT,
                WHITE,
                WIDTH // 2,
                HEIGHT // 2 - 12,
                center=True
            )

            draw_text(
                f"Checkpoint: level {checkpoint}",
                FONT,
                GREEN,
                WIDTH // 2,
                HEIGHT // 2 + 24,
                center=True
            )

            draw_text(
                "R: New run   C: Continue checkpoint",
                SMALL,
                WHITE,
                WIDTH // 2,
                HEIGHT // 2 + 65,
                center=True
            )

        else:
            draw_text(
                "DUNGEON MASTER!",
                BIG,
                GOLD,
                WIDTH // 2,
                HEIGHT // 2 - 50,
                center=True
            )

            draw_text(
                "You completed all 20 levels!",
                FONT,
                GREEN,
                WIDTH // 2,
                HEIGHT // 2 + 10,
                center=True
            )

            draw_text(
                "Press R to start a new run",
                SMALL,
                WHITE,
                WIDTH // 2,
                HEIGHT // 2 + 55,
                center=True
            )

    pygame.display.flip()