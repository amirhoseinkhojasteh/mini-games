import pygame
import random
import math
import json
import os
import sys

pygame.init()

# ==================== SETTINGS ====================
TILE = 40
COLS = 22
ROWS = 16
HUD_H = 100
WIDTH = COLS * TILE
HEIGHT = ROWS * TILE + HUD_H
FPS = 60
SAVE_FILE = "savegame.json"

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dungeon Escape")
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("segoeui", 22, bold=True)
SMALL = pygame.font.SysFont("segoeui", 16, bold=True)
BIG = pygame.font.SysFont("segoeui", 44, bold=True)

# ==================== COLORS ====================
BG = (12, 14, 25)
FLOOR_A = (29, 34, 54)
FLOOR_B = (34, 39, 63)
WALL = (52, 62, 96)
WALL_EDGE = (91, 111, 165)
WHITE = (240, 245, 255)
GOLD = (255, 204, 55)
GREEN = (70, 225, 145)
RED = (240, 70, 100)
BLUE = (65, 165, 255)
CYAN = (130, 220, 255)

# ==================== SAVE SYSTEM ====================
def load_save():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            checkpoint = int(data.get("checkpoint", 1))
            best_level = int(data.get("best_level", 1))
            best_score = int(data.get("best_score", 0))
            checkpoint = max(1, min(20, checkpoint))
            return checkpoint, best_level, best_score
    except (FileNotFoundError, json.JSONDecodeError, ValueError, TypeError):
        return 1, 1, 0

def save_game(checkpoint, best_level, best_score):
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

# ==================== MAP ====================
def make_map():
    grid = [["." for _ in range(COLS)] for _ in range(ROWS)]

    for y in range(ROWS):
        for x in range(COLS):
            if x == 0 or y == 0 or x == COLS - 1 or y == ROWS - 1:
                grid[y][x] = "#"

    # Interior obstacles
    blocks = [
        (4, 2, 1, 4), (8, 2, 4, 1), (13, 3, 1, 3),
        (17, 2, 1, 4), (5, 8, 4, 1), (10, 10, 1, 3),
        (14, 8, 4, 1), (3, 12, 4, 1), (17, 11, 1, 2),
        (7, 5, 1, 2), (19, 7, 1, 2), (11, 6, 2, 1)
    ]

    for x, y, w, h in blocks:
        for yy in range(y, min(y + h, ROWS - 1)):
            for xx in range(x, min(x + w, COLS - 1)):
                grid[yy][xx] = "#"

    # Clear important areas
    for x, y in [(2, 2), (3, 2), (19, 2), (19, 13),
                  (18, 13), (2, 13), (2, 3), (3, 3)]:
        grid[y][x] = "."

    return grid

world = make_map()

def tile_blocked(rect):
    left = max(0, rect.left // TILE)
    right = min(COLS - 1, (rect.right - 1) // TILE)
    top = max(0, rect.top // TILE)
    bottom = min(ROWS - 1, (rect.bottom - 1) // TILE)

    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            if world[y][x] == "#":
                return True
    return False

def move_solid(rect, dx, dy):
    rect.x += int(dx)
    if tile_blocked(rect):
        rect.x -= int(dx)

    rect.y += int(dy)
    if tile_blocked(rect):
        rect.y -= int(dy)

def draw_text(text, font, color, x, y, center=False):
    image = font.render(str(text), True, color)
    rect = image.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(image, rect)

def draw_map():
    screen.fill(BG)
    for y in range(ROWS):
        for x in range(COLS):
            tile = pygame.Rect(x*TILE, y*TILE, TILE, TILE)
            if world[y][x] == "#":
                pygame.draw.rect(screen, WALL, tile)
                pygame.draw.rect(screen, WALL_EDGE, tile, 2)
                pygame.draw.line(screen, (67, 78, 119),
                                (tile.x+5, tile.y+6),
                                (tile.right-5, tile.y+6), 2)
            else:
                color = FLOOR_A if (x+y) % 2 == 0 else FLOOR_B
                pygame.draw.rect(screen, color, tile)
                pygame.draw.rect(screen, (39, 45, 69), tile, 1)

# ==================== CHARACTER ART ====================
def draw_player(rect, facing):
    pygame.draw.ellipse(screen, (8, 10, 18),
                        (rect.x-3, rect.bottom-4, rect.w+6, 9))
    # legs
    pygame.draw.rect(screen, (29, 38, 64),
                    (rect.x+5, rect.bottom-9, 8, 10), border_radius=3)
    pygame.draw.rect(screen, (29, 38, 64),
                    (rect.right-13, rect.bottom-9, 8, 10), border_radius=3)
    # armor
    pygame.draw.rect(screen, BLUE,
                    (rect.x+3, rect.y+11, rect.w-6, rect.h-12),
                    border_radius=6)
    pygame.draw.rect(screen, (145, 210, 255),
                    (rect.x+6, rect.y+14, rect.w-12, 6),
                    border_radius=2)
    # helmet
    pygame.draw.rect(screen, (194, 207, 230),
                    (rect.x+5, rect.y+1, rect.w-10, 15),
                    border_radius=5)
    pygame.draw.rect(screen, (76, 94, 134),
                    (rect.x+4, rect.y+8, rect.w-8, 5))
    eye_x = rect.centerx + (5 if facing > 0 else -7)
    pygame.draw.rect(screen, (20, 28, 45), (eye_x, rect.y+7, 4, 3))
    # sword
    if facing > 0:
        pygame.draw.rect(screen, CYAN,
                        (rect.right-1, rect.y+17, 14, 4), border_radius=2)
        pygame.draw.rect(screen, GOLD,
                        (rect.right-3, rect.y+14, 4, 10))
    else:
        pygame.draw.rect(screen, CYAN,
                        (rect.left-13, rect.y+17, 14, 4), border_radius=2)
        pygame.draw.rect(screen, GOLD,
                        (rect.left-1, rect.y+14, 4, 10))

def draw_monster(rect, hp):
    pygame.draw.ellipse(screen, (8, 10, 18),
                        (rect.x-3, rect.bottom-4, rect.w+6, 9))
    shade = (145, 40, 78) if hp > 1 else (195, 55, 85)
    pygame.draw.rect(screen, shade,
                    (rect.x+2, rect.y+8, rect.w-4, rect.h-8),
                    border_radius=9)
    pygame.draw.polygon(screen, (205, 55, 105),
                       [(rect.x+5, rect.y+10), (rect.x+2, rect.y),
                        (rect.x+13, rect.y+8)])
    pygame.draw.polygon(screen, (205, 55, 105),
                       [(rect.right-5, rect.y+10), (rect.right-2, rect.y),
                        (rect.right-13, rect.y+8)])
    pygame.draw.rect(screen, (255, 230, 235),
                    (rect.x+7, rect.y+12, 5, 5), border_radius=2)
    pygame.draw.rect(screen, (255, 230, 235),
                    (rect.right-12, rect.y+12, 5, 5), border_radius=2)
    pygame.draw.rect(screen, (55, 20, 45),
                    (rect.x+10, rect.y+21, rect.w-20, 3))

# ==================== LEVEL CREATION ====================
def random_open_tile(occupied):
    for _ in range(300):
        x = random.randint(2, COLS-3)
        y = random.randint(2, ROWS-3)
        if world[y][x] == "#":
            continue
        rect = pygame.Rect(x*TILE+7, y*TILE+7, 26, 28)
        if any(rect.colliderect(other) for other in occupied):
            continue
        return rect
    return pygame.Rect(12*TILE, 7*TILE, 26, 28)

def create_level(level):
    global enemies, coins, key_rect, exit_rect, bullets
    bullets = []
    enemies = []
    coins = []

    # Difficulty grows every stage
    enemy_count = min(3 + level, 15)
    enemy_speed = 1.0 + level * 0.10
    enemy_hp = 1 + (level - 1) // 4

    occupied = [
        pygame.Rect(2*TILE, 2*TILE, 50, 55),
        pygame.Rect(19*TILE, 2*TILE, TILE, TILE),
        pygame.Rect(19*TILE, 13*TILE, TILE, TILE)
    ]

    for _ in range(enemy_count):
        er = random_open_tile(occupied)
        occupied.append(er)
        enemies.append({
            "rect": er,
            "hp": enemy_hp,
            "max_hp": enemy_hp,
            "speed": enemy_speed
        })

    for _ in range(5 + level // 2):
        coin_rect = random_open_tile(occupied)
        coin_rect = pygame.Rect(coin_rect.x+6, coin_rect.y+6, 14, 14)
        occupied.append(coin_rect)
        coins.append(coin_rect)

    key_rect = pygame.Rect(19*TILE+10, 2*TILE+10, 20, 20)
    exit_rect = pygame.Rect(19*TILE, 13*TILE, TILE, TILE)

# ==================== GAME STATE ====================
player = pygame.Rect(2*TILE+8, 2*TILE+8, 25, 30)
facing = 1
bullets = []
enemies = []
coins = []
key_rect = pygame.Rect(0, 0, 20, 20)
exit_rect = pygame.Rect(0, 0, TILE, TILE)

level = saved_checkpoint
checkpoint = saved_checkpoint
score = 0
lives = 3
has_key = False
game_state = "playing"
shoot_timer = 0
damage_timer = 0

create_level(level)

def restart_at_checkpoint():
    global level, lives, has_key, game_state, score
    global player, shoot_timer, damage_timer
    level = checkpoint
    lives = 3
    has_key = False
    game_state = "playing"
    player.x = 2*TILE+8
    player.y = 2*TILE+8
    shoot_timer = 0
    damage_timer = 0
    create_level(level)

def start_new_run():
    global level, checkpoint, lives, score, has_key
    global game_state, best_level, best_score
    level = 1
    checkpoint = 1
    lives = 3
    score = 0
    has_key = False
    game_state = "playing"
    best_level = max(best_level, 1)
    save_game(checkpoint, best_level, best_score)
    restart_at_checkpoint()

def save_checkpoint_if_needed():
    global checkpoint
    # The next level becomes the checkpoint after clearing 5, 10, and 15.
    # So the saved resume levels are 6, 11, and 16.
    if level in (6, 11, 16):
        checkpoint = level
        save_game(checkpoint, best_level, best_score)

# ==================== MAIN LOOP ====================
while True:
    dt = clock.tick(FPS) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            if event.key == pygame.K_r and game_state in ("lost", "won_all"):
                start_new_run()

            if event.key == pygame.K_c and game_state == "lost":
                restart_at_checkpoint()

            if (event.key == pygame.K_SPACE and game_state == "playing"
                    and shoot_timer <= 0):
                bullet = pygame.Rect(
                    player.centerx + facing*17,
                    player.centery-4, 16, 8
                )
                bullets.append({"rect": bullet, "dx": facing*9})
                shoot_timer = 0.20

    # ---------------- Update ----------------
    if game_state == "playing":
        shoot_timer = max(0, shoot_timer-dt)
        damage_timer = max(0, damage_timer-dt)

        keys = pygame.key.get_pressed()
        dx = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(
            keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(
            keys[pygame.K_w] or keys[pygame.K_UP])

        if dx:
            facing = 1 if dx > 0 else -1

        if dx or dy:
            length = math.hypot(dx, dy)
            move_solid(player, dx/length*235*dt, dy/length*235*dt)

        # Bullets hit monsters
        for bullet in bullets[:]:
            bullet["rect"].x += bullet["dx"]

            if (bullet["rect"].right < 0 or bullet["rect"].left > WIDTH
                    or tile_blocked(bullet["rect"])):
                bullets.remove(bullet)
                continue

            hit = False
            for enemy in enemies[:]:
                if bullet["rect"].colliderect(enemy["rect"]):
                    enemy["hp"] -= 1
                    hit = True
                    if enemy["hp"] <= 0:
                        enemies.remove(enemy)
                        score += 50 + level*5
                        best_score = max(best_score, score)
                        if random.random() < 0.6:
                            coins.append(pygame.Rect(
                                enemy["rect"].centerx-7,
                                enemy["rect"].centery-7, 14, 14))
                    break

            if hit and bullet in bullets:
                bullets.remove(bullet)

        # Monsters chase the player
        for enemy in enemies:
            er = enemy["rect"]
            vx = player.centerx-er.centerx
            vy = player.centery-er.centery
            distance = max(1, math.hypot(vx, vy))
            if distance > 42:
                move_solid(
                    er,
                    vx/distance*enemy["speed"]*60*dt,
                    vy/distance*enemy["speed"]*60*dt
                )

        # Touching a monster costs one heart, with brief invulnerability
        for enemy in enemies:
            if player.colliderect(enemy["rect"]) and damage_timer <= 0:
                lives -= 1
                damage_timer = 1.0
                player.x = 2*TILE+8
                player.y = 2*TILE+8
                if lives <= 0:
                    game_state = "lost"
                    break

        # Collect key and coins
        if not has_key and player.colliderect(key_rect):
            has_key = True
            score += 100

        for coin in coins[:]:
            if player.colliderect(coin):
                coins.remove(coin)
                score += 10

        # Exit opens after the key and all monsters are defeated
        if player.colliderect(exit_rect) and has_key and not enemies:
            if level >= 20:
                game_state = "won_all"
                best_level = 20
                best_score = max(best_score, score)
                save_game(checkpoint, best_level, best_score)
            else:
                cleared_level = level
                level += 1
                best_level = max(best_level, level)
                has_key = False
                lives = min(3, lives + 1)  # small reward for clearing a stage
                player.x = 2*TILE+8
                player.y = 2*TILE+8
                create_level(level)
                save_checkpoint_if_needed()
                save_game(checkpoint, best_level, best_score)

    # ---------------- Draw ----------------
    draw_map()

    # Exit
    pygame.draw.rect(screen, (75, 45, 35), exit_rect, border_radius=5)
    exit_color = GREEN if has_key and not enemies else RED
    pygame.draw.rect(screen, exit_color,
                    (exit_rect.x+7, exit_rect.y+5, 26, 30),
                    border_radius=4)
    pygame.draw.circle(screen, GOLD,
                      (exit_rect.right-10, exit_rect.centery), 3)

    # Key
    if not has_key:
        pygame.draw.circle(screen, GOLD, key_rect.center, 10)
        pygame.draw.circle(screen, (255, 240, 160), key_rect.center, 4)
        pygame.draw.rect(screen, GOLD,
                        (key_rect.centerx+6, key_rect.centery-2, 10, 4))
        pygame.draw.rect(screen, GOLD,
                        (key_rect.centerx+12, key_rect.centery-2, 3, 7))

    # Coins
    for coin in coins:
        pygame.draw.circle(screen, GOLD, coin.center, 8)
        pygame.draw.circle(screen, (255, 240, 160), coin.center, 3)

    # Bullets
    for bullet in bullets:
        pygame.draw.rect(screen, CYAN, bullet["rect"], border_radius=4)
        pygame.draw.rect(screen, WHITE,
                        (bullet["rect"].x+3, bullet["rect"].y+2, 5, 3),
                        border_radius=2)

    # Monsters and small health bars
    for enemy in enemies:
        draw_monster(enemy["rect"], enemy["hp"])
        bar_w = enemy["rect"].w
        pygame.draw.rect(screen, (50, 20, 30),
                        (enemy["rect"].x, enemy["rect"].y-7, bar_w, 4))
        current_w = int(bar_w * enemy["hp"] / enemy["max_hp"])
        pygame.draw.rect(screen, GREEN,
                        (enemy["rect"].x, enemy["rect"].y-7, current_w, 4))

    # Player blink while damage cooldown is active
    if damage_timer <= 0 or int(damage_timer*12) % 2 == 0:
        draw_player(player, facing)

    # HUD
    hud_y = ROWS*TILE
    pygame.draw.rect(screen, (17, 20, 34), (0, hud_y, WIDTH, HUD_H))
    pygame.draw.line(screen, WALL_EDGE, (0, hud_y), (WIDTH, hud_y), 3)

    draw_text(f"LEVEL {level}/20", FONT, CYAN, 18, hud_y+12)
    draw_text(f"SCORE {score}", FONT, GOLD, 190, hud_y+12)
    draw_text(f"LIVES {lives}", FONT, RED, 370, hud_y+12)
    draw_text(f"KEY {'YES' if has_key else 'NO'}", FONT,
              GREEN if has_key else WHITE, 530, hud_y+12)

    draw_text("WASD/ARROWS MOVE  |  SPACE SHOOT",
              SMALL, WHITE, 18, hud_y+52)
    draw_text(f"CHECKPOINT: {checkpoint}",
              SMALL, GREEN, 500, hud_y+52)

    # ---------------- End screens ----------------
    if game_state in ("lost", "won_all"):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 7, 15, 215))
        screen.blit(overlay, (0, 0))

        if game_state == "lost":
            draw_text("RUN OVER", BIG, RED,
                      WIDTH//2, HEIGHT//2-60, center=True)
            draw_text(f"You reached level {level}",
                      FONT, WHITE, WIDTH//2, HEIGHT//2-12, center=True)
            draw_text(f"Checkpoint: level {checkpoint}",
                      FONT, GREEN, WIDTH//2, HEIGHT//2+24, center=True)
            draw_text("R: New run   C: Continue checkpoint",
                      SMALL, WHITE, WIDTH//2, HEIGHT//2+65, center=True)
        else:
            draw_text("DUNGEON MASTER!", BIG, GOLD,
                      WIDTH//2, HEIGHT//2-50, center=True)
            draw_text("You completed all 20 levels!",
                      FONT, GREEN, WIDTH//2, HEIGHT//2+10, center=True)
            draw_text("Press R to start a new run",
                      SMALL, WHITE, WIDTH//2, HEIGHT//2+55, center=True)

    pygame.display.flip()