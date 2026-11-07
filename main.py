import pygame
import random
import json
import os
import math
import struct
import time
import array

pygame.init()

# ---------------- SETTINGS ----------------

WIDTH = 900
HEIGHT = 800

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Memory Match")

clock = pygame.time.Clock()

# COLORS
BG = (15, 18, 35)
PANEL = (27, 32, 57)
CARD = (42, 49, 79)
CARD_HOVER = (57, 68, 105)

WHITE = (245, 247, 255)
GRAY = (155, 165, 190)
BLUE = (75, 130, 255)
GREEN = (65, 205, 145)
RED = (245, 85, 105)
YELLOW = (255, 205, 90)
PURPLE = (155, 105, 255)

font = pygame.font.SysFont("segoeuiemoji", 26)
small_font = pygame.font.SysFont("segoeuiemoji", 19)
title_font = pygame.font.SysFont("segoeuiemoji", 58)
emoji_font = pygame.font.SysFont("segoeuiemoji", 35)

LEADERBOARD_FILE = "leaderboard.json"

DIFFICULTIES = {
    4: {"name": "EASY", "time": 90, "color": GREEN},
    6: {"name": "MEDIUM", "time": 150, "color": BLUE},
    8: {"name": "HARD", "time": 240, "color": YELLOW},
    10: {"name": "EXPERT", "time": 360, "color": RED}
}

# ---------------- SOUND SYSTEM ----------------

sound_enabled = False

music_channel = None
sfx_channel = None

SAMPLE_RATE = 22050


def create_sound(frequency, duration=0.15, volume=0.2):
    samples = int(SAMPLE_RATE * duration)
    buffer = bytearray()

    for i in range(samples):
        fade = min(1, i / 300, (samples - i) / 500)

        value = int(
            12000
            * volume
            * fade
            * math.sin(
                2 * math.pi * frequency * i / SAMPLE_RATE
            )
        )

        buffer.extend(struct.pack("<h", value))

    return pygame.mixer.Sound(buffer=bytes(buffer))


def create_music(notes, bpm=90, duration=8, volume=0.12):
    audio = array.array("h")

    beat_duration = 60 / bpm
    total_samples = int(SAMPLE_RATE * duration)

    for i in range(total_samples):

        current_time = i / SAMPLE_RATE

        beat = int(current_time / beat_duration)
        local_time = current_time % beat_duration

        frequency = notes[beat % len(notes)]

        if frequency == 0:
            audio.append(0)
            continue

        fade = min(1, local_time * 7)
        fade *= min(1, (beat_duration - local_time) * 5)

        main_wave = math.sin(
            2 * math.pi * frequency * current_time
        )

        second_wave = math.sin(
            2 * math.pi * frequency * 2 * current_time
        )

        third_wave = math.sin(
            2 * math.pi * frequency * 0.5 * current_time
        )

        value = (
            main_wave * 0.7
            + second_wave * 0.15
            + third_wave * 0.15
        )

        value *= fade * volume

        audio.append(
            max(-32767, min(32767, int(value * 16000)))
        )

    return pygame.mixer.Sound(buffer=audio.tobytes())


def initialize_audio():

    global sound_enabled
    global music_channel
    global sfx_channel

    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(
                frequency=SAMPLE_RATE,
                size=-16,
                channels=1
            )

        pygame.mixer.set_num_channels(8)

        music_channel = pygame.mixer.Channel(0)
        sfx_channel = pygame.mixer.Channel(1)

        # MENU MUSIC - آرام و ملایم
        menu_music = create_music(
            [261, 329, 392, 329, 293, 349, 392, 349],
            bpm=65,
            duration=8,
            volume=0.10
        )

        # EASY MUSIC - آرام
        easy_music = create_music(
            [261, 293, 329, 293, 261, 329, 349, 329],
            bpm=75,
            duration=8,
            volume=0.11
        )

        # MEDIUM MUSIC - کمی هیجانی‌تر
        medium_music = create_music(
            [329, 392, 440, 392, 349, 440, 494, 440],
            bpm=100,
            duration=8,
            volume=0.12
        )

        # HARD MUSIC - هیجانی
        hard_music = create_music(
            [392, 440, 494, 523, 494, 440, 523, 587],
            bpm=125,
            duration=8,
            volume=0.14
        )

        # EXPERT MUSIC - بسیار پرانرژی
        expert_music = create_music(
            [440, 523, 587, 659, 587, 659, 784, 659],
            bpm=155,
            duration=8,
            volume=0.16
        )

        # GAME EFFECTS
        click_sound = create_sound(500, 0.08, 0.2)
        match_sound = create_sound(850, 0.18, 0.3)

        # VICTORY EFFECT
        win_sound = create_music(
            [523, 659, 784, 1046, 784, 1046],
            bpm=180,
            duration=1.5,
            volume=0.35
        )

        # GAME OVER EFFECT
        lose_sound = create_music(
            [392, 349, 293, 261, 220, 196],
            bpm=100,
            duration=1.8,
            volume=0.3
        )

        global audio_sounds

        audio_sounds = {
            "menu": menu_music,
            "easy": easy_music,
            "medium": medium_music,
            "hard": hard_music,
            "expert": expert_music,
            "click": click_sound,
            "match": match_sound,
            "win": win_sound,
            "lose": lose_sound
        }

        sound_enabled = True

    except pygame.error as error:
        print("Audio initialization failed:", error)
        sound_enabled = False


def play_music(name):

    if not sound_enabled:
        return

    music_channel.stop()

    music_channel.play(
        audio_sounds[name],
        loops=-1
    )


def stop_music():

    if sound_enabled:
        music_channel.fadeout(300)


def play_sound(name):

    if not sound_enabled:
        return

    sfx_channel.play(audio_sounds[name])


initialize_audio()


# ---------------- DRAWING HELPERS ----------------

def draw_text(text, font_obj, color, x, y, center=True):

    image = font_obj.render(str(text), True, color)

    if center:
        rect = image.get_rect(center=(x, y))
    else:
        rect = image.get_rect(topleft=(x, y))

    screen.blit(image, rect)


def draw_panel(rect, color=PANEL, radius=20):

    pygame.draw.rect(
        screen,
        color,
        rect,
        border_radius=radius
    )


def draw_button(text, rect, color=BLUE, hover_color=CARD_HOVER):

    mouse = pygame.mouse.get_pos()
    hovered = rect.collidepoint(mouse)

    current_color = hover_color if hovered else color

    pygame.draw.rect(
        screen,
        current_color,
        rect,
        border_radius=14
    )

    pygame.draw.rect(
        screen,
        (95, 110, 155),
        rect,
        1,
        border_radius=14
    )

    draw_text(
        text,
        small_font,
        WHITE,
        rect.centerx,
        rect.centery
    )


def draw_background():

    screen.fill(BG)

    pygame.draw.circle(
        screen,
        (25, 34, 65),
        (40, 50),
        170
    )

    pygame.draw.circle(
        screen,
        (30, 25, 65),
        (850, 740),
        200
    )


# ---------------- LEADERBOARD ----------------

def load_leaderboard():

    if not os.path.exists(LEADERBOARD_FILE):
        return []

    try:
        with open(
            LEADERBOARD_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        return data if isinstance(data, list) else []

    except (json.JSONDecodeError, OSError):
        return []


def save_leaderboard(records):

    with open(
        LEADERBOARD_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            records,
            file,
            ensure_ascii=False,
            indent=4
        )


def add_record(name, elapsed, moves, size):

    records = load_leaderboard()

    records.append({
        "name": name,
        "time": elapsed,
        "moves": moves,
        "size": size
    })

    save_leaderboard(records)


# ---------------- PLAYER NAME ----------------

def get_input(prompt):

    name = ""

    while True:

        draw_background()

        draw_panel(
            pygame.Rect(180, 220, 540, 350)
        )

        draw_text(
            prompt,
            title_font,
            WHITE,
            WIDTH // 2,
            300
        )

        input_rect = pygame.Rect(
            270, 370, 360, 65
        )

        pygame.draw.rect(
            screen,
            CARD,
            input_rect,
            border_radius=12
        )

        draw_text(
            name + "|",
            font,
            YELLOW,
            WIDTH // 2,
            402
        )

        draw_text(
            "ENTER: Continue     ESC: Back",
            small_font,
            GRAY,
            WIDTH // 2,
            490
        )

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

    play_music("menu")

    buttons = [
        ("4 x 4", "EASY", 90, 4,
         pygame.Rect(115, 300, 300, 85)),

        ("6 x 6", "MEDIUM", 150, 6,
         pygame.Rect(485, 300, 300, 85)),

        ("8 x 8", "HARD", 240, 8,
         pygame.Rect(115, 410, 300, 85)),

        ("10 x 10", "EXPERT", 360, 10,
         pygame.Rect(485, 410, 300, 85))
    ]

    leaderboard_button = pygame.Rect(
        235, 550, 200, 65
    )

    exit_button = pygame.Rect(
        465, 550, 200, 65
    )

    while True:

        draw_background()

        draw_text(
            "MEMORY MATCH",
            title_font,
            YELLOW,
            WIDTH // 2,
            115
        )

        draw_text(
            "TEST YOUR MEMORY",
            small_font,
            GRAY,
            WIDTH // 2,
            180
        )

        draw_panel(
            pygame.Rect(75, 245, 750, 290)
        )

        for label, difficulty, seconds, size, rect in buttons:

            color = DIFFICULTIES[size]["color"]

            draw_button(
                f"{label}   |   {difficulty}",
                rect,
                CARD,
                CARD_HOVER
            )

            draw_text(
                f"{seconds} seconds",
                small_font,
                color,
                rect.centerx,
                rect.centery + 24
            )

        draw_button(
            "LEADERBOARD",
            leaderboard_button,
            PURPLE
        )

        draw_button(
            "EXIT",
            exit_button,
            RED
        )

        draw_text(
            "Find all matching pairs before time runs out!",
            small_font,
            GRAY,
            WIDTH // 2,
            690
        )

        pygame.display.flip()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return "exit"

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    return "exit"

            if event.type == pygame.MOUSEBUTTONDOWN:

                for label, difficulty, seconds, size, rect in buttons:

                    if rect.collidepoint(event.pos):

                        play_sound("click")
                        return size

                if leaderboard_button.collidepoint(event.pos):

                    play_sound("click")
                    show_leaderboard()
                    play_music("menu")

                if exit_button.collidepoint(event.pos):
                    return "exit"

        clock.tick(60)


# ---------------- LEADERBOARD SCREEN ----------------

def show_leaderboard():

    while True:

        draw_background()

        draw_text(
            "LEADERBOARD",
            title_font,
            YELLOW,
            WIDTH // 2,
            65
        )

        records = load_leaderboard()

        y = 125

        for size, info in DIFFICULTIES.items():

            draw_panel(
                pygame.Rect(100, y, 700, 135),
                PANEL,
                14
            )

            draw_text(
                f"{info['name']}  ({size} x {size})",
                font,
                info["color"],
                125,
                y + 12,
                False
            )

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
                    130,
                    y + 65,
                    False
                )

            else:

                for index, record in enumerate(category_records[:2]):

                    line = (
                        f"{index + 1}.  "
                        f"{record.get('name', 'Unknown')[:18]}    "
                        f"{record.get('time', 0)}s    "
                        f"{record.get('moves', 0)} moves"
                    )

                    draw_text(
                        line,
                        small_font,
                        GREEN if index == 0 else WHITE,
                        130,
                        y + 58 + index * 30,
                        False
                    )

            y += 145

        back_button = pygame.Rect(
            330, 720, 240, 55
        )

        draw_button(
            "BACK TO MENU",
            back_button,
            BLUE
        )

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

                    play_sound("click")
                    return

        clock.tick(30)


# ---------------- GAME ----------------

def start_game(size, player_name):

    # Select music according to difficulty
    music_names = {
        4: "easy",
        6: "medium",
        8: "hard",
        10: "expert"
    }

    play_music(music_names[size])

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

        draw_background()

        elapsed = int(time.time() - start_time)
        remaining = max(0, time_limit - elapsed)

        draw_panel(
            pygame.Rect(20, 15, 860, 75)
        )

        draw_text(
            f"PLAYER: {player_name}",
            small_font,
            WHITE,
            40,
            40,
            False
        )

        draw_text(
            f"TIME: {remaining}s",
            font,
            YELLOW if remaining > 10 else RED,
            WIDTH // 2,
            52
        )

        draw_text(
            f"MOVES: {moves}",
            small_font,
            WHITE,
            WIDTH - 150,
            40,
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
                color = CARD

            pygame.draw.rect(
                screen,
                color,
                rect,
                border_radius=8
            )

            if index in matched or index in opened:

                current_emoji_font = pygame.font.SysFont(
                    "segoeuiemoji",
                    max(12, min(45, card_size // 2))
                )

                draw_text(
                    card,
                    current_emoji_font,
                    WHITE,
                    rect.centerx,
                    rect.centery
                )

        pygame.display.flip()

        if len(matched) == len(cards):
            result = "win"
            break

        if remaining <= 0:
            result = "lose"
            break

        if len(opened) == 2:

            if time.time() - last_open_time >= 0.8:
                opened.clear()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    stop_music()
                    return "menu"

                if event.key == pygame.K_r:
                    stop_music()
                    return "restart"

                if event.key == pygame.K_q:
                    stop_music()
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
                        play_sound("click")

                        if len(opened) == 2:

                            moves += 1

                            first = opened[0]
                            second = opened[1]

                            if cards[first] == cards[second]:

                                matched.extend(opened)
                                opened.clear()

                                play_sound("match")

                            else:
                                last_open_time = time.time()

        clock.tick(60)

    elapsed = int(time.time() - start_time)

    # Stop stage music and play the result effect
    stop_music()

    if result == "win":

        add_record(
            player_name,
            elapsed,
            moves,
            size
        )

        play_sound("win")

    else:
        play_sound("lose")

    return result, elapsed, moves


# ---------------- RESULT SCREEN ----------------

def result_screen(result, player_name, elapsed, moves):

    while True:

        draw_background()

        draw_panel(
            pygame.Rect(150, 180, 600, 440)
        )

        if result == "win":

            draw_text(
                "YOU WIN!",
                title_font,
                GREEN,
                WIDTH // 2,
                250
            )

            draw_text(
                f"Congratulations {player_name}!",
                font,
                YELLOW,
                WIDTH // 2,
                340
            )

            draw_text(
                f"Time: {elapsed} seconds",
                small_font,
                WHITE,
                WIDTH // 2,
                410
            )

            draw_text(
                f"Moves: {moves}",
                small_font,
                WHITE,
                WIDTH // 2,
                450
            )

            draw_text(
                "Your record has been saved!",
                small_font,
                GREEN,
                WIDTH // 2,
                500
            )

        else:

            draw_text(
                "YOU LOST!",
                title_font,
                RED,
                WIDTH // 2,
                260
            )

            draw_text(
                "شما باختید!",
                font,
                WHITE,
                WIDTH // 2,
                350
            )

            draw_text(
                "Your record was not saved.",
                small_font,
                GRAY,
                WIDTH // 2,
                420
            )

        restart_button = pygame.Rect(
            180, 550, 220, 55
        )

        menu_button = pygame.Rect(
            500, 550, 220, 55
        )

        draw_button(
            "PLAY AGAIN",
            restart_button,
            GREEN
        )

        draw_button(
            "MAIN MENU",
            menu_button,
            BLUE
        )

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

                    play_sound("click")
                    return "restart"

                if menu_button.collidepoint(event.pos):

                    play_sound("click")
                    return "menu"

        clock.tick(30)


# ---------------- MAIN LOOP ----------------

def main():

    while True:

        size = main_menu()

        if size == "exit":
            break

        player_name = get_input("ENTER YOUR NAME")

        if player_name is None:
            break

        if player_name == "":
            continue

        while True:

            game_result = start_game(
                size,
                player_name
            )

            if game_result == "exit":
                pygame.quit()
                return

            if game_result == "menu":
                break

            if game_result == "restart":
                continue

            result, elapsed, moves = game_result

            next_action = result_screen(
                result,
                player_name,
                elapsed,
                moves
            )

            if next_action == "restart":
                continue

            break

    stop_music()
    pygame.quit()


if __name__ == "__main__":
    main()