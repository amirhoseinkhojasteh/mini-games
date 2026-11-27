import pygame
import random
import math
import json
import os
import sys
from dataclasses import dataclass

pygame.init()

WIDTH = 1000
HEIGHT = 700
FPS = 60
TILE = 32
GRAVITY = 0.65
SAVE_PATH = "savegame.json"
RECORD_PATH = "leaderboard.json"
ASSET_PATH = "assets"

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dungeon Escape")
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("consolas", 20)
SMALL = pygame.font.SysFont("consolas", 15)
BIG = pygame.font.SysFont("consolas", 48, bold=True)

WHITE = (240, 240, 240)
BLACK = (15, 18, 25)
GREEN = (80, 220, 100)
RED = (240, 75, 75)
BLUE = (80, 160, 255)
YELLOW = (255, 220, 80)
PURPLE = (190, 90, 255)
ORANGE = (255, 145, 55)
CYAN = (70, 220, 230)


def clamp(value, low, high):
    return max(low, min(value, high))


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return default


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
    except OSError:
        pass


def text(surface, value, x, y, color=WHITE, font=FONT):
    image = font.render(str(value), True, color)
    surface.blit(image, (int(x), int(y)))


def centered_text(surface, value, y, color=WHITE, font=FONT):
    image = font.render(str(value), True, color)
    surface.blit(image, (WIDTH // 2 - image.get_width() // 2, y))


def image_load(name, size=None):
    path = os.path.join(ASSET_PATH, name)
    if not os.path.isfile(path):
        return None
    try:
        image = pygame.image.load(path).convert_alpha()
        if size:
            image = pygame.transform.scale(image, size)
        return image
    except pygame.error:
        return None


class Assets:
    def __init__(self):
        self.player = image_load("player.png", (32, 42))
        self.slime = image_load("slime.png", (32, 30))
        self.archer = image_load("archer.png", (32, 42))
        self.mage = image_load("mage.png", (32, 42))
        self.poison = image_load("poison.png", (32, 42))
        self.jumper = image_load("jumper.png", (32, 38))
        self.brute = image_load("brute.png", (44, 48))
        self.tileset = image_load("tileset.png")
        self.background = image_load("background.png")
        self.coin = image_load("coin.png", (20, 20))
        self.heart = image_load("heart.png", (22, 22))
        self.key = image_load("key.png", (24, 24))
        self.exit = image_load("exit.png", (48, 64))

        self.tiles = {}

        if self.tileset:
            width, height = self.tileset.get_size()
            columns = width // TILE
            rows = height // TILE

            for row in range(rows):
                for column in range(columns):
                    rect = pygame.Rect(
                        column * TILE,
                        row * TILE,
                        TILE,
                        TILE
                    )
                    self.tiles[(column, row)] = self.tileset.subsurface(rect)


ASSETS = Assets()


@dataclass
class Camera:
    x: float = 0
    y: float = 0

    def follow(self, target, level_width, level_height):
        self.x = clamp(
            target.centerx - WIDTH // 2,
            0,
            max(0, level_width - WIDTH)
        )

        self.y = clamp(
            target.centery - HEIGHT // 2,
            0,
            max(0, level_height - HEIGHT)
        )

    def apply(self, rect):
        return pygame.Rect(
            rect.x - int(self.x),
            rect.y - int(self.y),
            rect.width,
            rect.height
        )


class Particle:
    def __init__(self, x, y, color, count=8):
        self.particles = []

        for _ in range(count):
            angle = random.random() * math.tau
            speed = random.uniform(1, 4)

            self.particles.append({
                "x": float(x),
                "y": float(y),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": random.randint(15, 35),
                "color": color,
                "size": random.randint(2, 5)
            })

    def update(self):
        for particle in self.particles:
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            particle["vy"] += 0.1
            particle["life"] -= 1

        self.particles = [
            particle for particle in self.particles
            if particle["life"] > 0
        ]

    def draw(self, camera):
        for particle in self.particles:
            pygame.draw.rect(
                screen,
                particle["color"],
                (
                    int(particle["x"] - camera.x),
                    int(particle["y"] - camera.y),
                    particle["size"],
                    particle["size"]
                )
            )


class Tile:
    def __init__(self, x, y, kind="ground"):
        self.rect = pygame.Rect(x, y, TILE, TILE)
        self.kind = kind

    @property
    def solid(self):
        return self.kind in ("ground", "stone", "platform")

    def draw(self, camera):
        rect = camera.apply(self.rect)

        if self.kind == "ground":
            pygame.draw.rect(screen, (75, 110, 50), rect)
            pygame.draw.rect(
                screen,
                (125, 185, 75),
                (rect.x, rect.y, rect.width, 8)
            )
            pygame.draw.rect(
                screen,
                (75, 65, 45),
                (rect.x, rect.y + 8, rect.width, rect.height - 8)
            )

        elif self.kind == "stone":
            pygame.draw.rect(screen, (80, 85, 100), rect)
            pygame.draw.rect(
                screen,
                (115, 120, 135),
                (rect.x + 3, rect.y + 3, 12, 5)
            )
            pygame.draw.rect(
                screen,
                (55, 60, 75),
                (rect.x + 18, rect.y + 18, 10, 5)
            )

        elif self.kind == "platform":
            pygame.draw.rect(
                screen,
                (105, 75, 45),
                (rect.x, rect.y + 5, rect.width, rect.height - 5)
            )
            pygame.draw.rect(
                screen,
                (135, 195, 80),
                (rect.x, rect.y, rect.width, 7)
            )

        elif self.kind == "tree":
            pygame.draw.rect(
                screen,
                (95, 60, 35),
                (rect.x + 13, rect.y + 15, 8, 25)
            )
            pygame.draw.circle(
                screen,
                (30, 105, 45),
                (rect.centerx, rect.y + 8),
                20
            )
            pygame.draw.circle(
                screen,
                (45, 145, 55),
                (rect.x + 8, rect.y + 10),
                13
            )

        elif self.kind == "decoration":
            pygame.draw.circle(
                screen,
                (60, 125, 60),
                rect.center,
                10
            )


class Coin:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.phase = random.random() * math.tau

    def draw(self, camera):
        rect = camera.apply(self.rect)
        bob = math.sin(pygame.time.get_ticks() / 180 + self.phase) * 3

        if ASSETS.coin:
            screen.blit(ASSETS.coin, (rect.x, rect.y + bob))
        else:
            pygame.draw.circle(
                screen,
                YELLOW,
                (rect.centerx, int(rect.centery + bob)),
                9
            )
            pygame.draw.circle(
                screen,
                ORANGE,
                (rect.centerx, int(rect.centery + bob)),
                5,
                2
            )


class Player:
    def __init__(self):
        self.rect = pygame.Rect(80, 450, 30, 42)
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

        self.vx = 0
        self.vy = 0

        self.speed = 5
        self.jump_power = 13

        self.facing = 1
        self.facing_y = 0

        self.health = 5
        self.max_health = 5

        self.invincible = 0
        self.on_ground = False
        self.crouching = False

        self.damage = 1
        self.jump_bonus = 0
        self.coins = 0

        self.animation_time = 0
        self.attack_cooldown = 0

    def move_horizontal(self, tiles):
        self.x += self.vx
        self.rect.x = int(self.x)

        for tile in tiles:
            if not tile.solid:
                continue

            if self.rect.colliderect(tile.rect):
                if self.vx > 0:
                    self.rect.right = tile.rect.left
                elif self.vx < 0:
                    self.rect.left = tile.rect.right

                self.x = float(self.rect.x)

    def move_vertical(self, tiles):
        self.y += self.vy
        self.rect.y = int(self.y)

        self.on_ground = False

        for tile in tiles:
            if not tile.solid:
                continue

            if self.rect.colliderect(tile.rect):
                if self.vy > 0:
                    self.rect.bottom = tile.rect.top
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = tile.rect.bottom

                self.vy = 0
                self.y = float(self.rect.y)

    def update(self, keys, tiles):
        self.vx = 0
        self.crouching = False

        if keys[pygame.K_LEFT]:
            self.vx = -self.speed
            self.facing = -1
            self.facing_y = 0

        if keys[pygame.K_RIGHT]:
            self.vx = self.speed
            self.facing = 1
            self.facing_y = 0

        if keys[pygame.K_UP]:
            self.facing_y = -1

        if keys[pygame.K_DOWN]:
            self.facing_y = 1
            self.crouching = True

        if self.crouching and self.on_ground:
            self.rect.height = 28
        else:
            self.rect.height = 42

        self.vy += GRAVITY
        self.vy = min(self.vy, 15)

        self.move_horizontal(tiles)
        self.move_vertical(tiles)

        if self.invincible > 0:
            self.invincible -= 1

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        self.animation_time += 1

    def jump(self):
        if self.on_ground and not self.crouching:
            self.vy = -self.jump_power - self.jump_bonus
            self.on_ground = False

    def damage_player(self, amount=1):
        if self.invincible <= 0:
            self.health -= amount
            self.invincible = 90

    def draw(self, camera):
        rect = camera.apply(self.rect)

        if self.invincible and self.invincible % 10 < 5:
            return

        if ASSETS.player:
            image = ASSETS.player

            if self.facing < 0:
                image = pygame.transform.flip(image, True, False)

            if self.crouching:
                image = pygame.transform.scale(
                    image,
                    (32, 28)
                )

            screen.blit(image, rect)

        else:
            color = (60, 145, 255)

            pygame.draw.rect(screen, color, rect)

            pygame.draw.rect(
                screen,
                (230, 240, 255),
                (rect.x + 5, rect.y + 6, 22, 12)
            )

            eye_x = rect.x + 7 if self.facing < 0 else rect.x + 20

            pygame.draw.rect(
                screen,
                BLACK,
                (eye_x, rect.y + 9, 5, 5)
            )

            pygame.draw.rect(
                screen,
                (30, 60, 130),
                (rect.x + 4, rect.bottom - 8, 8, 8)
            )

            pygame.draw.rect(
                screen,
                (30, 60, 130),
                (rect.right - 12, rect.bottom - 8, 8, 8)
            )


class Projectile:
    def __init__(self, x, y, vx, vy, kind, damage=1):
        self.x = float(x)
        self.y = float(y)

        self.vx = vx
        self.vy = vy

        self.kind = kind
        self.damage = damage

        self.rect = pygame.Rect(x, y, 16, 16)
        self.life = 180

    def update(self):
        self.x += self.vx
        self.y += self.vy

        self.rect.center = (int(self.x), int(self.y))
        self.life -= 1

    def draw(self, camera):
        rect = camera.apply(self.rect)

        colors = {
            "arrow": (220, 190, 120),
            "fire": (255, 100, 20),
            "poison": (100, 255, 70),
            "magic": (180, 80, 255)
        }

        color = colors.get(self.kind, WHITE)

        pygame.draw.circle(screen, color, rect.center, 8)

        if self.kind == "fire":
            pygame.draw.circle(screen, YELLOW, rect.center, 4)

        elif self.kind == "poison":
            pygame.draw.circle(screen, (50, 160, 20), rect.center, 3)


class PoisonCloud:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 70, 24)
        self.timer = 240

    def update(self):
        self.timer -= 1

    def draw(self, camera):
        rect = camera.apply(self.rect)

        pygame.draw.ellipse(
            screen,
            (75, 180, 35),
            rect
        )

        pygame.draw.ellipse(
            screen,
            (130, 255, 60),
            (
                rect.x + 12,
                rect.y + 5,
                25,
                12
            )
        )


class Enemy:
    TYPES = (
        "slime",
        "archer",
        "mage",
        "poison",
        "jumper",
        "brute"
    )

    COLORS = {
        "slime": (70, 220, 90),
        "archer": (175, 135, 90),
        "mage": (170, 70, 240),
        "poison": (100, 220, 35),
        "jumper": (255, 145, 40),
        "brute": (150, 55, 55)
    }

    def __init__(self, x, y, kind, level):
        self.kind = kind

        sizes = {
            "slime": (32, 28),
            "archer": (30, 42),
            "mage": (32, 42),
            "poison": (32, 42),
            "jumper": (32, 38),
            "brute": (46, 50)
        }

        self.rect = pygame.Rect(
            x,
            y,
            *sizes.get(kind, (32, 32))
        )

        self.x = float(x)
        self.y = float(y)

        self.level = level
        self.health = 2 + level // 3
        self.max_health = self.health

        self.speed = 1.2 + level * 0.04
        self.direction = random.choice((-1, 1))

        self.timer = random.randint(60, 130)
        self.vy = 0

        self.points = 50 + level * 5
        self.dead = False

    def attack(self, player, projectiles, clouds):
        distance = player.rect.centerx - self.rect.centerx
        vertical_distance = player.rect.centery - self.rect.centery

        self.timer -= 1

        if self.kind == "slime":
            if abs(distance) < 450:
                self.direction = 1 if distance > 0 else -1
                self.x += self.direction * self.speed

        elif self.kind == "archer":
            if abs(distance) < 600 and self.timer <= 0:
                direction = 1 if distance > 0 else -1

                projectiles.append(
                    Projectile(
                        self.rect.centerx,
                        self.rect.centery,
                        direction * 5,
                        0,
                        "arrow"
                    )
                )

                self.timer = 120

        elif self.kind == "mage":
            if abs(distance) < 650 and self.timer <= 0:
                direction = 1 if distance > 0 else -1

                projectiles.append(
                    Projectile(
                        self.rect.centerx,
                        self.rect.centery,
                        direction * 4,
                        random.choice((-1, 0, 1)),
                        "fire",
                        2
                    )
                )

                self.timer = 150

        elif self.kind == "poison":
            if abs(distance) < 420 and self.timer <= 0:
                clouds.append(
                    PoisonCloud(
                        self.rect.centerx - 35,
                        self.rect.bottom - 15
                    )
                )

                self.timer = 180

        elif self.kind == "jumper":
            if abs(distance) < 500:
                self.direction = 1 if distance > 0 else -1

                if self.rect.bottom >= 620:
                    self.vy = -12

                self.x += self.direction * self.speed * 1.5

                self.vy += GRAVITY
                self.y += self.vy

                if self.y + self.rect.height >= 620:
                    self.y = 620 - self.rect.height
                    self.vy = 0

        elif self.kind == "brute":
            if abs(distance) < 350:
                self.direction = 1 if distance > 0 else -1
                self.x += self.direction * self.speed * 0.5

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def draw(self, camera):
        rect = camera.apply(self.rect)

        image = getattr(ASSETS, self.kind, None)

        if image:
            if self.direction < 0:
                image = pygame.transform.flip(image, True, False)

            screen.blit(image, rect)

        else:
            pygame.draw.rect(
                screen,
                self.COLORS[self.kind],
                rect
            )

            pygame.draw.rect(
                screen,
                WHITE,
                (rect.x + 5, rect.y + 6, 7, 7)
            )

            pygame.draw.rect(
                screen,
                WHITE,
                (rect.right - 12, rect.y + 6, 7, 7)
            )

        pygame.draw.rect(
            screen,
            RED,
            (rect.x, rect.y - 8, rect.width, 5)
        )

        health_width = int(
            rect.width * self.health / max(1, self.max_health)
        )

        pygame.draw.rect(
            screen,
            GREEN,
            (rect.x, rect.y - 8, health_width, 5)
        )


class Ability:
    DATA = [
        ("Strong Attack", "Increase damage", 100, "damage"),
        ("Fast Movement", "Increase speed", 80, "speed"),
        ("Extra Health", "Increase maximum health", 120, "health"),
        ("High Jump", "Jump higher", 90, "jump"),
        ("Quick Attack", "Attack faster", 110, "attack"),
        ("Coin Bonus", "Gain extra coins", 70, "coins"),
        ("Shield", "Increase protection", 130, "shield")
    ]

    @classmethod
    def choices(cls):
        return random.sample(cls.DATA, 3)

    @staticmethod
    def apply(player, ability):
        name, description, cost, kind = ability

        if kind == "damage":
            player.damage += 1

        elif kind == "speed":
            player.speed += 1

        elif kind == "health":
            player.max_health += 1
            player.health += 1

        elif kind == "jump":
            player.jump_bonus += 2

        elif kind == "attack":
            player.attack_cooldown = max(
                0,
                player.attack_cooldown - 5
            )

        elif kind == "coins":
            player.coins += 10

        elif kind == "shield":
            player.invincible = max(
                player.invincible,
                120
            )


class Level:
    def __init__(self, number):
        self.number = number
        self.width = 4200 + number * 350
        self.height = 900

        self.tiles = []
        self.enemies = []
        self.coins = []
        self.projectiles = []
        self.clouds = []
        self.particles = []

        self.key = pygame.Rect(
            self.width - 450,
            560,
            28,
            28
        )

        self.exit = pygame.Rect(
            self.width - 120,
            520,
            60,
            100
        )

        self.generate()

    def generate(self):
        for x in range(0, self.width, TILE):
            self.tiles.append(
                Tile(x, 620, "ground")
            )

        for index in range(20 + self.number):
            x = random.randint(250, self.width - 350)
            y = random.randint(330, 520)
            length = random.randint(3, 6)

            for part in range(length):
                self.tiles.append(
                    Tile(
                        x + part * TILE,
                        y,
                        "platform"
                    )
                )

        for index in range(self.width // 250):
            x = random.randint(0, self.width - TILE)

            self.tiles.append(
                Tile(x, 580, "tree")
            )

        for index in range(12 + self.number * 2):
            x = random.randint(400, self.width - 250)

            kind = random.choice(Enemy.TYPES)

            self.enemies.append(
                Enemy(x, 580, kind, self.number)
            )

        for index in range(25):
            x = random.randint(150, self.width - 200)
            y = random.choice((430, 480, 540, 570))

            self.coins.append(Coin(x, y))


class HUD:
    def __init__(self):
        self.font = FONT

    def draw(self, game):
        pygame.draw.rect(
            screen,
            (18, 24, 35),
            (0, 0, WIDTH, 80)
        )

        text(
            screen,
            f"LEVEL {game.level.number}",
            20,
            12,
            YELLOW
        )

        text(
            screen,
            f"SCORE {game.score}",
            210,
            12,
            GREEN
        )

        text(
            screen,
            f"COINS {game.player.coins}",
            410,
            12,
            YELLOW
        )

        text(
            screen,
            f"HP {game.player.health}/{game.player.max_health}",
            620,
            12,
            RED
        )

        text(
            screen,
            "ARROWS: MOVE | UP: JUMP | DOWN: CROUCH | X: ATTACK",
            20,
            48,
            WHITE,
            SMALL
        )


class Menu:
    def draw(self):
        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill((5, 10, 20, 220))
        screen.blit(overlay, (0, 0))

        centered_text(
            screen,
            "DUNGEON ESCAPE",
            190,
            YELLOW,
            BIG
        )

        centered_text(
            screen,
            "ENTER  -  START",
            320,
            WHITE
        )

        centered_text(
            screen,
            "ESC  -  EXIT",
            370,
            WHITE
        )


class AbilityMenu:
    def draw(self, game):
        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill((5, 10, 20, 230))
        screen.blit(overlay, (0, 0))

        centered_text(
            screen,
            "CHOOSE YOUR ABILITY",
            110,
            PURPLE,
            BIG
        )

        centered_text(
            screen,
            f"AVAILABLE SCORE: {game.score}",
            190,
            YELLOW
        )

        for index, ability in enumerate(game.abilities):
            name, description, cost, kind = ability
            y = 250 + index * 105

            pygame.draw.rect(
                screen,
                (35, 45, 65),
                (170, y, 660, 80),
                border_radius=12
            )

            pygame.draw.rect(
                screen,
                PURPLE,
                (170, y, 6, 80)
            )

            text(
                screen,
                f"{index + 1}. {name}",
                200,
                y + 10,
                WHITE
            )

            text(
                screen,
                description,
                200,
                y + 42,
                BLUE,
                SMALL
            )

            text(
                screen,
                f"{cost} POINTS",
                680,
                y + 25,
                YELLOW
            )

        centered_text(
            screen,
            "0 - SKIP",
            610,
            WHITE
        )


class GameOver:
    def draw(self, game):
        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))

        centered_text(
            screen,
            "GAME OVER",
            210,
            RED,
            BIG
        )

        centered_text(
            screen,
            f"FINAL SCORE: {game.score}",
            320,
            YELLOW
        )

        centered_text(
            screen,
            "ENTER - RESTART",
            400,
            WHITE
        )

        centered_text(
            screen,
            "ESC - EXIT",
            450,
            WHITE
        )


class Game:
    def __init__(self):
        self.player = Player()
        self.level = Level(1)

        self.camera = Camera()
        self.hud = HUD()
        self.menu = Menu()
        self.ability_menu = AbilityMenu()
        self.game_over_menu = GameOver()

        self.state = "menu"

        self.score = 0
        self.has_key = False

        self.abilities = Ability.choices()

        self.records = load_json(
            RECORD_PATH,
            []
        )

        self.best = load_json(
            SAVE_PATH,
            {
                "best_score": 0,
                "best_level": 1
            }
        )

        self.message = ""
        self.message_timer = 0

    def restart(self):
        self.__init__()

    def start_level(self):
        self.level = Level(self.level.number + 1)

        self.player.rect.x = 80
        self.player.rect.y = 450

        self.player.x = float(self.player.rect.x)
        self.player.y = float(self.player.rect.y)

        self.player.vx = 0
        self.player.vy = 0

        self.has_key = False
        self.abilities = Ability.choices()

        self.state = "ability"

    def save_record(self):
        record = {
            "score": self.score,
            "level": self.level.number,
            "coins": self.player.coins
        }

        self.records.append(record)

        self.records.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        self.records = self.records[:20]

        save_json(
            RECORD_PATH,
            self.records
        )

        if self.score > self.best["best_score"]:
            self.best["best_score"] = self.score

        if self.level.number > self.best["best_level"]:
            self.best["best_level"] = self.level.number

        save_json(
            SAVE_PATH,
            self.best
        )

    def shoot(self):
        if self.player.attack_cooldown > 0:
            return

        self.player.attack_cooldown = 18

        if self.player.facing_y == -1:
            vx = 0
            vy = -7

        elif self.player.facing_y == 1:
            vx = 0
            vy = 7

        else:
            vx = self.player.facing * 7
            vy = 0

        self.level.projectiles.append(
            Projectile(
                self.player.rect.centerx,
                self.player.rect.centery,
                vx,
                vy,
                "magic",
                self.player.damage
            )
        )

    def update_projectiles(self):
        for projectile in self.level.projectiles:
            projectile.update()

            if projectile.kind != "magic":
                if projectile.rect.colliderect(
                    self.player.rect
                ):
                    self.player.damage_player()
                    projectile.life = 0

            else:
                for enemy in self.level.enemies:
                    if projectile.rect.colliderect(
                        enemy.rect
                    ):
                        enemy.health -= projectile.damage
                        projectile.life = 0

                        if enemy.health <= 0:
                            enemy.dead = True
                            self.score += enemy.points

                            self.level.particles.append(
                                Particle(
                                    enemy.rect.centerx,
                                    enemy.rect.centery,
                                    Enemy.COLORS[enemy.kind]
                                )
                            )

        self.level.projectiles = [
            projectile
            for projectile in self.level.projectiles
            if projectile.life > 0
        ]

    def update_clouds(self):
        for cloud in self.level.clouds:
            cloud.update()

            if cloud.rect.colliderect(
                self.player.rect
            ):
                self.player.damage_player()

        self.level.clouds = [
            cloud for cloud in self.level.clouds
            if cloud.timer > 0
        ]

    def update_particles(self):
        for particle in self.level.particles:
            particle.update()

        self.level.particles = [
            particle for particle in self.level.particles
            if particle.particles
        ]

    def update(self):
        keys = pygame.key.get_pressed()

        if self.state != "playing":
            return

        self.player.update(
            keys,
            self.level.tiles
        )

        if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
            if self.player.on_ground:
                self.player.jump()

        if keys[pygame.K_x]:
            self.shoot()

        for enemy in self.level.enemies:
            enemy.attack(
                self.player,
                self.level.projectiles,
                self.level.clouds
            )

            if enemy.rect.colliderect(
                self.player.rect
            ):
                self.player.damage_player()

        self.level.enemies = [
            enemy for enemy in self.level.enemies
            if not enemy.dead
        ]

        self.update_projectiles()
        self.update_clouds()
        self.update_particles()

        for coin in self.level.coins[:]:
            if coin.rect.colliderect(
                self.player.rect
            ):
                self.level.coins.remove(coin)

                self.score += 10
                self.player.coins += 1

        if self.level.key.colliderect(
            self.player.rect
        ):
            if not self.has_key:
                self.has_key = True
                self.score += 100

        if self.has_key:
            if self.level.exit.colliderect(
                self.player.rect
            ):
                self.start_level()

        self.camera.follow(
            self.player.rect,
            self.level.width,
            self.level.height
        )

        if self.player.health <= 0:
            self.save_record()
            self.state = "lost"

    def draw_background(self):
        screen.fill((105, 180, 230))

        if ASSETS.background:
            background = ASSETS.background

            for x in range(
                -int(self.camera.x * 0.25) % background.get_width(),
                WIDTH,
                background.get_width()
            ):
                screen.blit(
                    background,
                    (x, 80 - int(self.camera.y * 0.1))
                )

        else:
            for index in range(7):
                x = (
                    index * 220
                    - int(self.camera.x * 0.25)
                ) % (WIDTH + 300)

                pygame.draw.circle(
                    screen,
                    WHITE,
                    (x, 100),
                    35
                )

                pygame.draw.circle(
                    screen,
                    WHITE,
                    (x + 35, 100),
                    28
                )

            pygame.draw.polygon(
                screen,
                (75, 125, 100),
                [
                    (0, 580),
                    (180, 330),
                    (400, 580)
                ]
            )

            pygame.draw.polygon(
                screen,
                (65, 115, 90),
                [
                    (400, 580),
                    (700, 300),
                    (1000, 580)
                ]
            )

    def draw_world(self):
        self.draw_background()

        for tile in self.level.tiles:
            tile.draw(self.camera)

        for coin in self.level.coins:
            coin.draw(self.camera)

        if not self.has_key:
            key_rect = self.camera.apply(self.level.key)

            if ASSETS.key:
                screen.blit(ASSETS.key, key_rect)
            else:
                pygame.draw.rect(
                    screen,
                    YELLOW,
                    key_rect
                )

                pygame.draw.circle(
                    screen,
                    ORANGE,
                    key_rect.center,
                    6
                )

        exit_rect = self.camera.apply(self.level.exit)

        exit_color = GREEN if self.has_key else RED

        if ASSETS.exit:
            screen.blit(ASSETS.exit, exit_rect)
        else:
            pygame.draw.rect(
                screen,
                exit_color,
                exit_rect
            )

            pygame.draw.rect(
                screen,
                BLACK,
                (
                    exit_rect.x + 12,
                    exit_rect.y + 20,
                    30,
                    60
                )
            )

        for cloud in self.level.clouds:
            cloud.draw(self.camera)

        for projectile in self.level.projectiles:
            projectile.draw(self.camera)

        for enemy in self.level.enemies:
            enemy.draw(self.camera)

        for particle in self.level.particles:
            particle.draw(self.camera)

        self.player.draw(self.camera)

        self.hud.draw(self)

        if self.has_key:
            text(
                screen,
                "KEY FOUND - REACH THE EXIT",
                350,
                95,
                GREEN
            )

    def draw(self):
        self.draw_world()

        if self.state == "menu":
            self.menu.draw()

        elif self.state == "ability":
            self.ability_menu.draw(self)

        elif self.state == "lost":
            self.game_over_menu.draw(self)

        pygame.display.flip()

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.state == "menu":
            if event.key == pygame.K_RETURN:
                self.state = "ability"

            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

        elif self.state == "ability":
            if event.key in (
                pygame.K_1,
                pygame.K_2,
                pygame.K_3
            ):
                index = event.key - pygame.K_1
                ability = self.abilities[index]

                if self.score >= ability[2]:
                    self.score -= ability[2]
                    Ability.apply(
                        self.player,
                        ability
                    )

                self.state = "playing"

            elif event.key == pygame.K_0:
                self.state = "playing"

        elif self.state == "playing":
            if event.key == pygame.K_ESCAPE:
                self.state = "menu"

            elif event.key == pygame.K_r:
                self.level = Level(self.level.number)

                self.player.rect.x = 80
                self.player.rect.y = 450

                self.player.x = float(self.player.rect.x)
                self.player.y = float(self.player.rect.y)

                self.player.vx = 0
                self.player.vy = 0

                self.has_key = False

        elif self.state == "lost":
            if event.key == pygame.K_RETURN:
                self.restart()

            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

    def run(self):
        while True:
            clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                self.handle_event(event)

            self.update()
            self.draw()


if __name__ == "__main__":
    os.makedirs(ASSET_PATH, exist_ok=True)

    game = Game()
    game.run()