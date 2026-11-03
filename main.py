import pygame
import random
import json
import os
import math
import struct
import time

pygame.init()

# ---------------- SETTINGS ----------------

WIDTH = 900
HEIGHT = 800

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Memory Match")

clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (20, 20, 30)
GRAY = (80, 80, 100)
BLUE = (50, 120, 220)
GREEN = (50, 180, 100)
RED = (220, 60, 60)
YELLOW = (240, 190, 50)
PURPLE = (130, 80, 200)

font = pygame.font.SysFont("segoeuiemoji", 30)
small_font = pygame.font.SysFont("segoeuiemoji", 20)
title_font = pygame.font.SysFont("segoeuiemoji", 55)

LEADERBOARD_FILE = "leaderboard.json"

# ---------------- DIFFICULTY ----------------

DIFFICULTIES = {
    4: {"name": "Easy", "time": 90},
    6: {"name": "Medium", "time": 150},
    8: {"name": "Hard", "time": 240},
    10: {"name": "Expert", "time": 360}
}

# ---------------- SOUND ----------------

try:
    pygame.mixer.init()

    def create_sound(frequency, duration=0.15):
        sample_rate = 22050
        samples = int(sample_rate * duration)
        buffer = bytearray()

        for i in range(samples):
            value = int(
                10000 * math.sin(
                    2 * math.pi * frequency * i / sample_rate
                )
            )
            buffer.extend(struct.pack("<h", value))

        return pygame.mixer.Sound(buffer=bytes(buffer))

    click_sound = create_sound(500)
    match_sound = create_sound(800)
    win_sound = create_sound(1000, 0.4)
    lose_sound = create_sound(200, 0.4)

    sound_enabled = True

except:
    sound_enabled = False


def play_sound(sound):
    if sound_enabled:
        sound.play()


# ---------------- LEADERBOARD ----------------

def load_leaderboard():
    if not os.path.exists(LEADERBOARD_FILE):
        return []

    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, list) else []

    except (json.JSONDecodeError, OSError):
        return []


def save_leaderboard(records):
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=4)


def add_record(name, elapsed, moves, size):
    records = load_leaderboard()

    records.append({
        "name": name,
        "time": elapsed,
        "moves": moves,
        "size": size
    })

    records.sort(
        key=lambda record: (record["size"], record["time"], record["moves"])
    )

    save_leaderboard(records)


# ---------------- HELPERS ----------------

def draw_text(text, font_obj, color, x, y, center=True):
    image = font_obj.render(str(text), True, color)

    if center:
        rect = image.get_rect(center=(x, y))
    else:
        rect = image.get_rect(topleft=(x, y))

    screen.blit(image, rect)


def draw_button(text, rect, color=BLUE):
    pygame.draw.rect(screen, color, rect, border_radius=12)
    pygame.draw.rect(screen, WHITE, rect, 2, border_radius=12)

    draw_text(
        text,
        small_font,
        WHITE,
        rect.centerx,
        rect.centery
    )


def get_input(prompt):
    name = ""

    while True:
        screen.fill(BLACK)

        draw_text(prompt, title_font, WHITE, WIDTH // 2, 250)
        draw_text(name + "|", font, YELLOW, WIDTH // 2, 370)
        draw_text("ENTER = Continue | ESC = Back",
                  small_font, WHITE, WIDTH // 2, 450)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return ""

                elif event.key == pygame.K_RETURN:
                    if name.strip():
                        return name.strip()

                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]

                elif len(name) < 18:
                    if event.unicode.isprintable():
                        name += event.unicode

        clock.tick(30)


# ---------------- MAIN MENU ----------------

def main_menu():
    buttons = [
        ("4 x 4  EASY", pygame.Rect(100, 300, 300, 65), 4),
        ("6 x 6  MEDIUM", pygame.Rect(500, 300, 300, 65), 6),
        ("8 x 8  HARD", pygame.Rect(100, 400, 300, 65), 8),
        ("10 x 10  EXPERT", pygame.Rect(500, 400, 300, 65), 10)
    ]

    leaderboard_button = pygame.Rect(250, 520, 180, 65)
    exit_button = pygame.Rect(470, 520, 180, 65)

    while True:
        screen.fill(BLACK)

        draw_text("MEMORY MATCH", title_font, YELLOW,
                  WIDTH // 2, 130)

        draw_text("Choose your difficulty",
                  font, WHITE, WIDTH // 2, 220)

        for text, rect, size in buttons:
            draw_button(text, rect)

        draw_button("LEADERBOARD", leaderboard_button, PURPLE)
        draw_button("EXIT", exit_button, RED)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "exit"

            if event.type == pygame.MOUSEBUTTONDOWN:
                for text, rect, size in buttons:
                    if rect.collidepoint(event.pos):
                        return size

                if leaderboard_button.collidepoint(event.pos):
                    show_leaderboard()

                if exit_button.collidepoint(event.pos):
                    return "exit"

        clock.tick(30)


# ---------------- LEADERBOARD SCREEN ----------------

def show_leaderboard():
    while True:
        screen.fill(BLACK)

        draw_text("LEADERBOARD", title_font, YELLOW,
                  WIDTH // 2, 65)

        records = load_leaderboard()

        y = 125

        for size, info in DIFFICULTIES.items():

            draw_text(
                f"{info['name']}  ({size}x{size})",
                font,
                YELLOW,
                40,
                y,
                False
            )

            y += 35

            category_records = [
                record for record in records
                if record.get("size") == size
            ]

            category_records.sort(
                key=lambda record: (
                    record.get("time", 999999),
                    record.get("moves", 999999)
                )
            )

            if not category_records:
                draw_text(
                    "No records yet!",
                    small_font,
                    GRAY,
                    55,
                    y,
                    False
                )
                y += 30

            else:
                draw_text(
                    "Rank     Player                 Time       Moves",
                    small_font,
                    WHITE,
                    55,
                    y,
                    False
                )
                y += 28

                for index, record in enumerate(category_records[:3]):

                    line = (
                        f"{index + 1}.          "
                        f"{record.get('name', 'Unknown')[:16]:16} "
                        f"{record.get('time', 0)}s          "
                        f"{record.get('moves', 0)}"
                    )

                    draw_text(
                        line,
                        small_font,
                        GREEN if index == 0 else WHITE,
                        55,
                        y,
                        False
                    )

                    y += 27

            y += 12

        back_button = pygame.Rect(330, 730, 240, 55)
        draw_button("BACK", back_button, RED)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    return

        clock.tick(30)


# ---------------- GAME ----------------

def start_game(size, player_name):

    emojis = [
        "😀", "😎", "🤖", "👻", "🐱",
        "🐶", "🦊", "🐼", "🐸", "🐵",
        "🦁", "🐯", "🐨", "🐮", "🐷",
        "🐙", "🦋", "🐢", "🐬", "🦄",
        "🍎", "🍕", "🍔", "🍩", "🍓",
        "⚽", "🏀", "🎮", "🎵", "🚀",
        "🌈", "⭐", "🔥", "💎", "🎁",
        "🌍", "🌙", "☀️", "🌸", "🍀",
        "🎃", "🎯", "🚗", "✈️", "🚲",
        "❤️", "💜", "💙", "💚", "🧡"
    ]

    total_pairs = (size * size) // 2

    cards = emojis[:total_pairs] * 2
    random.shuffle(cards)

    matched = []
    opened = []

    moves = 0
    start_time = time.time()

    time_limit = DIFFICULTIES[size]["time"]

    available_width = WIDTH - 40
    available_height = HEIGHT - 150

    card_size = min(
        available_width // size,
        available_height // size
    )

    grid_width = card_size * size
    grid_height = card_size * size

    start_x = (WIDTH - grid_width) // 2
    start_y = 130 + (available_height - grid_height) // 2

    last_open_time = 0

    while True:

        screen.fill(BLACK)

        elapsed = int(time.time() - start_time)
        remaining = max(0, time_limit - elapsed)

        draw_text(
            f"Player: {player_name}",
            small_font,
            WHITE,
            20,
            25,
            False
        )

        draw_text(
            f"Time: {remaining}s",
            font,
            YELLOW if remaining > 10 else RED,
            WIDTH // 2,
            45
        )

        draw_text(
            f"Moves: {moves}",
            small_font,
            WHITE,
            WIDTH - 150,
            25,
            False
        )

        for index, card in enumerate(cards):

            row = index // size
            col = index % size

            x = start_x + col * card_size
            y = start_y + row * card_size

            rect = pygame.Rect(
                x + 3,
                y + 3,
                card_size - 6,
                card_size - 6
            )

            if index in matched:
                color = GREEN
            elif index in opened:
                color = BLUE
            else:
                color = GRAY

            pygame.draw.rect(
                screen,
                color,
                rect,
                border_radius=8
            )

            pygame.draw.rect(
                screen,
                WHITE,
                rect,
                2,
                border_radius=8
            )

            if index in matched or index in opened:

                emoji_font = pygame.font.SysFont(
                    "segoeuiemoji",
                    max(12, min(45, card_size // 2))
                )

                draw_text(
                    card,
                    emoji_font,
                    WHITE,
                    rect.centerx,
                    rect.centery
                )

        pygame.display.flip()

        # WIN CHECK

        if len(matched) == len(cards):
            result = "win"
            break

        # TIME CHECK

        if remaining <= 0:
            result = "lose"
            break

        # HIDE WRONG CARDS

        if len(opened) == 2:
            if time.time() - last_open_time >= 0.8:
                opened.clear()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    return "menu"

                if event.key == pygame.K_r:
                    return "restart"

                if event.key == pygame.K_q:
                    return "exit"

            if event.type == pygame.MOUSEBUTTONDOWN:

                if len(opened) >= 2:
                    continue

                mouse_x, mouse_y = event.pos

                col = (mouse_x - start_x) // card_size
                row = (mouse_y - start_y) // card_size

                if 0 <= row < size and 0 <= col < size:

                    index = row * size + col

                    if index not in matched and index not in opened:

                        opened.append(index)
                        play_sound(click_sound)

                        if len(opened) == 2:

                            moves += 1

                            first = opened[0]
                            second = opened[1]

                            if cards[first] == cards[second]:

                                matched.extend(opened)
                                opened.clear()

                                play_sound(match_sound)

                            else:
                                last_open_time = time.time()

        clock.tick(60)

    # ---------------- SAVE RESULT ----------------

    if result == "win":

        elapsed = int(time.time() - start_time)

        add_record(
            player_name,
            elapsed,
            moves,
            size
        )

        play_sound(win_sound)

    else:
        play_sound(lose_sound)

    return result


# ---------------- RESULT SCREEN ----------------

def result_screen(result, player_name, size, moves, elapsed):

    while True:

        screen.fill(BLACK)

        if result == "win":

            draw_text(
                "YOU WIN!",
                title_font,
                GREEN,
                WIDTH // 2,
                180
            )

            draw_text(
                f"Congratulations {player_name}!",
                font,
                YELLOW,
                WIDTH // 2,
                270
            )

            draw_text(
                f"Time: {elapsed} seconds",
                small_font,
                WHITE,
                WIDTH // 2,
                340
            )

            draw_text(
                f"Moves: {moves}",
                small_font,
                WHITE,
                WIDTH // 2,
                380
            )

            draw_text(
                "Your record has been saved!",
                small_font,
                GREEN,
                WIDTH // 2,
                430
            )

        else:

            draw_text(
                "YOU LOST!",
                title_font,
                RED,
                WIDTH // 2,
                200
            )

            draw_text(
                "شما باختید!",
                font,
                WHITE,
                WIDTH // 2,
                300
            )

            draw_text(
                "Your record was not saved.",
                small_font,
                GRAY,
                WIDTH // 2,
                370
            )

        restart_button = pygame.Rect(180, 540, 220, 65)
        menu_button = pygame.Rect(500, 540, 220, 65)

        draw_button("PLAY AGAIN", restart_button, GREEN)
        draw_button("MAIN MENU", menu_button, BLUE)

        pygame.display.flip()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"

            if event.type == pygame.MOUSEBUTTONDOWN:

                if restart_button.collidepoint(event.pos):
                    return "restart"

                if menu_button.collidepoint(event.pos):
                    return "menu"

        clock.tick(30)


# ---------------- MAIN LOOP ----------------

def main():

    while True:

        size = main_menu()

        if size == "exit":
            break

        player_name = get_input("Enter your name")

        if player_name is None:
            break

        if player_name == "":
            continue

        while True:

            result = start_game(size, player_name)

            if result == "exit":
                pygame.quit()
                return

            if result == "menu":
                break

            if result == "restart":
                continue

            # Read final game statistics from the saved record
            records = load_leaderboard()
            latest = next(
                (
                    record for record in reversed(records)
                    if record.get("name") == player_name
                    and record.get("size") == size
                ),
                None
            )

            if result == "win" and latest:
                elapsed = latest["time"]
                moves = latest["moves"]
            else:
                elapsed = DIFFICULTIES[size]["time"]
                moves = 0

            next_action = result_screen(
                result,
                player_name,
                size,
                moves,
                elapsed
            )

            if next_action == "restart":
                continue

            break

    pygame.quit()


main()