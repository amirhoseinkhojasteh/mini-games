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
small_font = pygame.font.SysFont("segoeuiemoji", 22)
title_font = pygame.font.SysFont("segoeuiemoji", 55)

LEADERBOARD_FILE = "leaderboard.json"

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
            return json.load(file)
    except:
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

    # زمان کمتر، رتبه بهتر؛ در زمان برابر، حرکت کمتر
    records.sort(key=lambda x: (x["time"], x["moves"]))

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
    active = True

    while active:
        screen.fill(BLACK)

        draw_text(prompt, title_font, WHITE, WIDTH // 2, 250)
        draw_text(name + "|", font, YELLOW, WIDTH // 2, 370)
        draw_text("ENTER = Continue", small_font, WHITE, WIDTH // 2, 450)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
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
    while True:
        screen.fill(BLACK)

        draw_text("MEMORY MATCH", title_font, YELLOW, WIDTH // 2, 150)
        draw_text("Choose your difficulty", font, WHITE, WIDTH // 2, 250)

        buttons = [
            ("4 x 4", pygame.Rect(120, 320, 140, 65), 4),
            ("6 x 6", pygame.Rect(290, 320, 140, 65), 6),
            ("8 x 8", pygame.Rect(460, 320, 140, 65), 8),
            ("10 x 10", pygame.Rect(630, 320, 140, 65), 10)
        ]

        for text, rect, size in buttons:
            draw_button(text, rect)

        leaderboard_button = pygame.Rect(300, 450, 300, 65)
        draw_button("LEADERBOARD", leaderboard_button, PURPLE)

        draw_text("60 seconds challenge!", small_font, YELLOW,
                  WIDTH // 2, 560)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.MOUSEBUTTONDOWN:
                for text, rect, size in buttons:
                    if rect.collidepoint(event.pos):
                        return size

                if leaderboard_button.collidepoint(event.pos):
                    show_leaderboard()


# ---------------- LEADERBOARD SCREEN ----------------

def show_leaderboard():
    while True:
        screen.fill(BLACK)

        draw_text("LEADERBOARD", title_font, YELLOW,
                  WIDTH // 2, 90)

        records = load_leaderboard()

        draw_text(
            "RANK       NAME             TIME       MOVES       SIZE",
            small_font,
            WHITE,
            WIDTH // 2,
            190
        )

        if not records:
            draw_text("No records yet!", font, GRAY,
                      WIDTH // 2, 350)

        else:
            for index, record in enumerate(records[:12]):
                y = 240 + index * 40

                line = (
                    f"{index + 1}.          "
                    f"{record['name'][:14]:14} "
                    f"{record['time']}s          "
                    f"{record['moves']}          "
                    f"{record['size']}x{record['size']}"
                )

                color = YELLOW if index == 0 else WHITE

                draw_text(line, small_font, color,
                          WIDTH // 2, y)

        back_button = pygame.Rect(330, 700, 240, 60)
        draw_button("BACK", back_button, RED)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    return


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

    game_over = False
    result = None

    margin = 20
    top_space = 130

    available_width = WIDTH - margin * 2
    available_height = HEIGHT - top_space - margin

    card_size = min(
        available_width // size,
        available_height // size
    )

    grid_width = card_size * size
    grid_height = card_size * size

    start_x = (WIDTH - grid_width) // 2
    start_y = top_space + (available_height - grid_height) // 2

    last_open_time = 0

    while True:

        screen.fill(BLACK)

        elapsed = int(time.time() - start_time)
        remaining = max(0, 60 - elapsed)

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

        # کارت ها

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
                    max(16, min(45, card_size // 2))
                )

                draw_text(
                    card,
                    emoji_font,
                    WHITE,
                    rect.centerx,
                    rect.centery
                )

        pygame.display.flip()

        # بررسی برنده شدن

        if len(matched) == len(cards):
            result = "win"
            break

        # پایان زمان

        if remaining <= 0:
            result = "lose"
            break

        # برگرداندن کارت های اشتباه

        if len(opened) == 2:
            if time.time() - last_open_time >= 0.8:
                opened.clear()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_r:
                    return "restart"

                if event.key == pygame.K_m:
                    return "menu"

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

    # ---------------- RESULT ----------------

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

def result_screen(result, player_name):

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

            records = load_leaderboard()

            draw_text(
                f"Congratulations {player_name}!",
                font,
                YELLOW,
                WIDTH // 2,
                280
            )

            if records:
                record = records[-1] if False else None

            draw_text(
                "Your record has been saved!",
                small_font,
                WHITE,
                WIDTH // 2,
                350
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

        restart_button = pygame.Rect(180, 500, 220, 65)
        menu_button = pygame.Rect(500, 500, 220, 65)

        draw_button("PLAY AGAIN", restart_button, GREEN)
        draw_button("MAIN MENU", menu_button, BLUE)

        pygame.display.flip()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

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

        player_name = get_input("Enter your name")

        while True:

            result = start_game(size, player_name)

            if result == "menu":
                break

            if result == "restart":
                continue

            next_action = result_screen(result, player_name)

            if next_action == "restart":
                continue

            break


main()
