import pygame
import random
import sys
import math
import struct
import io
import wave

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1)

# Window
WIDTH = 800
HEIGHT = 750

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Memory Match")

clock = pygame.time.Clock()

# Colors
BLACK = (20, 23, 35)
WHITE = (255, 255, 255)
BLUE = (65, 110, 220)
GREEN = (40, 190, 130)
PURPLE = (150, 90, 220)
YELLOW = (255, 210, 60)
CYAN = (50, 220, 230)
RED = (230, 75, 90)
GRAY = (140, 145, 160)

# Fonts
font = pygame.font.Font(None, 65)
small_font = pygame.font.Font(None, 35)
card_font = pygame.font.SysFont("segoeuiemoji", 50)

# Emojis
emojis = [
    "🍎", "🐱", "🚗", "⚽",
    "🐶", "🍕", "🎮", "⭐",
    "🍉", "🐸", "🎁", "🌈",
    "🍔", "🐼", "🚀", "🎵",
    "🍓", "🦊", "🐻", "🌻",
    "🎸", "🍩", "🐢", "🦁",
    "🍇", "🚲", "🐙", "🎯",
    "🌙", "🧸", "🍒", "🦋",
    "🐧", "🎨", "🍦", "🛸",
    "🐳", "🌵", "🎲", "🥝",
    "🦄", "🍪", "🏀", "🐝",
    "🎃", "🍋", "🐨", "💎",
    "🌍", "🎹"
]

# Sound Generator
def make_sound(frequency, duration, volume=0.3):

    sample_rate = 22050
    samples = bytearray()

    for i in range(int(sample_rate * duration)):

        t = i / sample_rate

        value = int(
            32767 * volume *
            math.sin(2 * math.pi * frequency * t)
        )

        samples.extend(struct.pack("<h", value))

    return pygame.mixer.Sound(buffer=bytes(samples))


click_sound = make_sound(500, 0.10)
match_sound = make_sound(850, 0.20)
wrong_sound = make_sound(220, 0.25)
win_sound = make_sound(1000, 0.50)
lose_sound = make_sound(180, 0.50)

# Background Music
def create_music():

    sample_rate = 22050

    melody = [440, 523, 659, 523, 392, 494, 587, 494]

    samples = bytearray()

    for frequency in melody:

        for i in range(int(sample_rate * 0.25)):

            t = i / sample_rate

            value = int(
                4000 * math.sin(2 * math.pi * frequency * t)
            )

            samples.extend(struct.pack("<h", value))

    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as file:

        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(sample_rate)
        file.writeframes(bytes(samples))

    buffer.seek(0)

    return pygame.mixer.Sound(buffer)


music = create_music()

# Game Variables
game_state = "menu"

rows = 4
cols = 4

cards = []
opened = []
matched = []

moves = 0

GAME_TIME = 60
start_time = 0
remaining_time = GAME_TIME

waiting = False
wait_time = 0

music_on = True
result_sound_played = False


# Text Function
def draw_text(text, font, color, x, y):

    image = font.render(str(text), True, color)
    screen.blit(image, (x, y))


# Start Game
def start_game(r, c):

    global rows, cols
    global cards, opened, matched
    global moves, start_time
    global waiting, game_state
    global remaining_time, result_sound_played

    rows = r
    cols = c

    total = rows * cols

    selected = emojis[:total // 2]

    cards = selected * 2
    random.shuffle(cards)

    opened = []
    matched = []

    moves = 0

    start_time = pygame.time.get_ticks()
    remaining_time = GAME_TIME

    waiting = False
    result_sound_played = False

    game_state = "playing"


# Menu
def draw_menu():

    screen.fill(BLACK)

    draw_text("MEMORY MATCH", font, CYAN, 190, 100)

    draw_text("Choose Board Size", small_font, WHITE, 270, 220)

    options = [
        ("4 x 4", 4, 4),
        ("6 x 6", 6, 6),
        ("8 x 8", 8, 8),
        ("10 x 10", 10, 10)
    ]

    for i, (label, r, c) in enumerate(options):

        rect = pygame.Rect(100 + i * 155, 320, 130, 65)

        pygame.draw.rect(screen, PURPLE, rect, border_radius=12)

        text = small_font.render(label, True, WHITE)

        screen.blit(text, text.get_rect(center=rect.center))

    draw_text("Time Limit: 60 Seconds", small_font, YELLOW, 250, 470)


# Game Board
def draw_game():

    screen.fill(BLACK)

    elapsed = (pygame.time.get_ticks() - start_time) // 1000

    global remaining_time
    remaining_time = max(0, GAME_TIME - elapsed)

    draw_text("MEMORY MATCH", font, CYAN, 200, 15)

    timer_color = RED if remaining_time <= 10 else WHITE

    draw_text(
        f"Time: {remaining_time}s",
        small_font,
        timer_color,
        70,
        90
    )

    draw_text(
        f"Moves: {moves}",
        small_font,
        WHITE,
        600,
        90
    )

    margin = 25
    gap = 5

    available_width = WIDTH - 2 * margin
    available_height = 550

    size = min(
        (available_width - (cols - 1) * gap) // cols,
        (available_height - (rows - 1) * gap) // rows
    )

    total_width = cols * size + (cols - 1) * gap
    total_height = rows * size + (rows - 1) * gap

    start_x = (WIDTH - total_width) // 2
    start_y = 140 + (550 - total_height) // 2

    for i in range(len(cards)):

        row = i // cols
        col = i % cols

        x = start_x + col * (size + gap)
        y = start_y + row * (size + gap)

        rect = pygame.Rect(x, y, size, size)

        if i in matched:
            color = GREEN

        elif i in opened:
            color = YELLOW

        else:
            color = BLUE

        pygame.draw.rect(
            screen,
            color,
            rect,
            border_radius=6
        )

        if i in matched or i in opened:

            text = card_font.render(cards[i], True, BLACK)

            screen.blit(
                text,
                text.get_rect(center=rect.center)
            )

        else:

            text = font.render("?", True, WHITE)

            screen.blit(
                text,
                text.get_rect(center=rect.center)
            )

    draw_text("R = Restart", small_font, GRAY, 310, 710)


# Result Screen
def draw_result():

    screen.fill(BLACK)

    if game_state == "win":

        draw_text("YOU WIN!", font, GREEN, 270, 200)

        draw_text("You found all pairs!", small_font, WHITE, 230, 300)

    else:

        draw_text("YOU LOST!", font, RED, 270, 200)

        draw_text("شما باختید!", small_font, YELLOW, 320, 300)

    draw_text(f"Moves: {moves}", small_font, WHITE, 320, 390)

    draw_text("Press R to Play Again", small_font, CYAN, 260, 500)

    draw_text("Press M for Menu", small_font, WHITE, 290, 550)


# Main Loop
running = True

while running:

    if game_state == "menu":

        draw_menu()

    elif game_state == "playing":

        # Countdown
        elapsed = (pygame.time.get_ticks() - start_time) // 1000

        remaining_time = max(0, GAME_TIME - elapsed)

        # Win Check
        if len(matched) == len(cards) and cards:

            game_state = "win"

            if not result_sound_played:
                win_sound.play()
                result_sound_played = True

        # Time Check
        elif remaining_time <= 0:

            game_state = "lose"

            if not result_sound_played:
                lose_sound.play()
                result_sound_played = True

        if game_state == "playing":

            if waiting:

                if pygame.time.get_ticks() - wait_time > 1000:

                    opened.clear()
                    waiting = False

            draw_game()

    elif game_state in ("win", "lose"):

        draw_result()

    # Events
    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

        # Menu
        if game_state == "menu":

            if event.type == pygame.MOUSEBUTTONDOWN:

                mx, my = event.pos

                if 320 <= my <= 385:

                    if 100 <= mx <= 230:
                        start_game(4, 4)

                    elif 255 <= mx <= 385:
                        start_game(6, 6)

                    elif 410 <= mx <= 540:
                        start_game(8, 8)

                    elif 565 <= mx <= 695:
                        start_game(10, 10)

                    if game_state == "playing" and music_on:
                        music.play(-1)

        # Playing
        elif game_state == "playing":

            if event.type == pygame.MOUSEBUTTONDOWN:

                if waiting:
                    continue

                mx, my = event.pos

                margin = 25
                gap = 5

                available_width = WIDTH - 2 * margin
                available_height = 550

                size = min(
                    (available_width - (cols - 1) * gap) // cols,
                    (available_height - (rows - 1) * gap) // rows
                )

                total_width = cols * size + (cols - 1) * gap
                total_height = rows * size + (rows - 1) * gap

                start_x = (WIDTH - total_width) // 2
                start_y = 140 + (550 - total_height) // 2

                for i in range(len(cards)):

                    row = i // cols
                    col = i % cols

                    x = start_x + col * (size + gap)
                    y = start_y + row * (size + gap)

                    rect = pygame.Rect(x, y, size, size)

                    if rect.collidepoint(mx, my):

                        if i not in opened and i not in matched:

                            opened.append(i)

                            click_sound.play()

                            if len(opened) == 2:

                                moves += 1

                                first = opened[0]
                                second = opened[1]

                                if cards[first] == cards[second]:

                                    matched.extend(opened)
                                    opened.clear()

                                    match_sound.play()

                                else:

                                    wrong_sound.play()

                                    waiting = True
                                    wait_time = pygame.time.get_ticks()

                        break

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_r:

                    start_game(rows, cols)

        # Results
        elif game_state in ("win", "lose"):

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_r:

                    start_game(rows, cols)

                elif event.key == pygame.K_m:

                    game_state = "menu"

    pygame.display.update()

    clock.tick(60)


pygame.quit()
sys.exit()
