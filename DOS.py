import pygame
import random
import math
import os
import sys

# Load high score from file
high_score = 0
if os.path.exists("highscore.txt"):
    with open("highscore.txt", "r") as file:
        high_score = int(file.read())

def resource_path(relative_path):
    try:
        # For PyInstaller
        base_path = sys._MEIPASS
    except AttributeError:
        # For running directly from source
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

pygame.init()
pygame.mixer.init()

#SOUND FX AND BG SOUND
click_sound = pygame.mixer.Sound(resource_path("music/Click1B.ogg"))
hurt_sound = pygame.mixer.Sound(resource_path("music/hurt.mp3"))
heal_sound = pygame.mixer.Sound(resource_path("music/heal.mp3"))


# Also update music loading:
music_tracks = [
    resource_path("music/Battle_Encounter.ogg"),
    resource_path("music/BossBattle.ogg")
]

current_track = 0

MUSIC_END = pygame.USEREVENT + 1
pygame.mixer.music.set_endevent(MUSIC_END)

#ICON
icon = pygame.image.load(resource_path("assets/screen.png"))

pygame.display.set_icon(icon)

# Start the first background music
pygame.mixer.music.load(music_tracks[current_track])
pygame.mixer.music.set_volume(0.4) 
pygame.mixer.music.play()


SCREEN_WIDTH = 460
SCREEN_HEIGHT = 640
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dodge or Smash")
score_font = pygame.font.SysFont(None, 36)

# Game control flags
start_game = False
game_over = False
button_font = pygame.font.SysFont(None, 40)
score = 0

# UI buttons (initialized once)
restart_button = pygame.Rect(SCREEN_WIDTH // 2 - 75, SCREEN_HEIGHT // 2 + 50, 150, 50)
quit_button = pygame.Rect(SCREEN_WIDTH // 2 - 75, SCREEN_HEIGHT // 2 + 120, 150, 50)

clock = pygame.time.Clock()

# Player setup
player = pygame.Rect(200, 540, 50, 50)
player_speed = 5
player_lives = 3

# Triangle cooldown and hint
triangle_cooldown = 0
triangle_hint_timer = 0
triangle_spawn_timer = 0
hint_font = pygame.font.SysFont(None, 40)

# Shape falling
shapes = []
normal_shape_speed = 5
slow_shape_speed = 3
shape_speed = normal_shape_speed

frame_counter = 0
difficulty_interval = 600
speed_increment = 1.0
max_shape_speed = 50

# Slow motion
slow_active = False
slow_available = True
slow_duration = 2 * 60
slow_timer = 0
cooldown_duration = 5 * 60
cooldown_timer = 0

running = True
while running:
    clock.tick(60)
    events = pygame.event.get()

    for event in events:
        if event.type == pygame.QUIT:
            running = False
        
        #BG MUSIC LOOP
        if event.type == MUSIC_END:
            current_track = (current_track + 1) % len(music_tracks)
            pygame.mixer.music.load(music_tracks[current_track])
            pygame.mixer.music.play()    

    screen.fill("#FFC894")

    #Title Screen
    if not start_game:
        font = pygame.font.SysFont(None, 60)
        text = font.render("DODGE OR SMASH", True, (64, 56, 49))
        screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 200))

        start_button = pygame.Rect((SCREEN_WIDTH - 150) // 2, 300, 150, 50)
        pygame.draw.rect(screen, (0, 120, 255), start_button, border_radius=10)
        button_text = font.render("START", True, (255, 255, 255))
        screen.blit(button_text, (
            start_button.x + (start_button.width - button_text.get_width()) // 2,
            start_button.y + (start_button.height - button_text.get_height()) // 2
        ))

        quit_button = pygame.Rect((SCREEN_WIDTH - 150) // 2, 390, 150, 50)
        pygame.draw.rect(screen, (0, 120, 255), quit_button, border_radius=10)
        button_text = font.render("QUIT", True, (255, 255, 255))
        screen.blit(button_text, (
            quit_button.x + (quit_button.width - button_text.get_width()) // 2,
            quit_button.y + (quit_button.height - button_text.get_height()) // 2
        ))

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos):
                    click_sound.play()
                    start_game = True
                elif quit_button.collidepoint(event.pos):
                    click_sound.play()
                    pygame.time.delay(200)
                    running = False

        pygame.display.flip()
        continue

    #Player movemnt
    if not game_over:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and player.left > 0:
            player.x -= player_speed
        if keys[pygame.K_d] and player.right < SCREEN_WIDTH:
            player.x += player_speed

        if keys[pygame.K_SPACE] and slow_available:
            slow_active = True
            slow_timer += 1
            if slow_timer >= slow_duration:
                slow_active = False
                slow_available = False
                slow_timer = 0
        else:
            slow_active = False

        if not slow_available:
            cooldown_timer += 1
            if cooldown_timer >= cooldown_duration:
                slow_available = True
                cooldown_timer = 0

        shape_speed = slow_shape_speed if slow_active else normal_shape_speed

        #triangle spawn rate
        triangle_spawn_timer += 1
        if triangle_spawn_timer >= 1800:
            triangle_spawn_timer = 0
            if random.randint(1, 100) <= 100:
                x = random.randint(50, SCREEN_WIDTH - 50)
                y = -50
                shapes.append(("triangle", [x, y, 25]))
                triangle_hint_timer = 120
        
        #Other shape spawn rate
        if random.randint(0, 50) == 0:
            if normal_shape_speed >= 15:
                shape_type = random.choice(["rect", "circle", "pentagon", "hexagon"])
            elif normal_shape_speed >= 10:
                shape_type = random.choice(["rect", "circle", "pentagon"])
            else:
                shape_type = random.choice(["rect", "circle"])

            # Define size BEFORE using it
            if shape_type == "rect":
                size = 50
            elif shape_type == "circle":
                size = 25
            elif shape_type == "pentagon":
                size = 50
            elif shape_type == "hexagon":
                size = 75

            # Now safe to use size
            x = random.randint(size, SCREEN_WIDTH - size)
            y = -size

            # Append correct shape
            if shape_type == "rect":
                shapes.append(("rect", pygame.Rect(x, y, size, size)))
            elif shape_type == "circle":
                shapes.append(("circle", [x, y, size]))
            elif shape_type == "pentagon":
                shapes.append(("pentagon", [x, y, size]))
            elif shape_type == "hexagon":
                shapes.append(("hexagon", [x, y, size]))

        for shape in shapes[:]:
            kind, data = shape

            if kind == "rect":
                data.y += shape_speed
                pygame.draw.rect(screen, (255, 50, 25), data)
                if player.colliderect(data):
                    hurt_sound.play()
                    player_lives -= 1
                    shapes.remove(shape)
                    if player_lives <= 0:
                        game_over = True
                        if score > high_score:
                            high_score = score
                            with open("highscore.txt", "w") as file:
                                file.write(str(high_score))
                elif data.y > SCREEN_HEIGHT:
                    shapes.remove(shape)
                    score += 1

            elif kind == "circle":
                data[1] += shape_speed
                pygame.draw.circle(screen, (69, 255, 155), (data[0], int(data[1])), data[2])
                if player.collidepoint(data[0], int(data[1])):
                    hurt_sound.play()
                    player_lives -= 1
                    shapes.remove(shape)
                    if player_lives <= 0:
                        game_over = True
                        if score > high_score:
                            high_score = score
                            with open("highscore.txt", "w") as file:
                                file.write(str(high_score))
                elif data[1] > SCREEN_HEIGHT:
                    shapes.remove(shape)
                    score += 1

            elif kind == "pentagon":
                cx, cy, size = data
                cy += shape_speed
                data[1] = cy
                points = [(cx + size * math.cos(i * 2 * math.pi / 5 - math.pi / 2),
                        cy + size * math.sin(i * 2 * math.pi / 5 - math.pi / 2)) for i in range(5)]
                pygame.draw.polygon(screen, (111, 255, 52), points)
                if player.collidepoint(cx, cy):
                    hurt_sound.play()
                    player_lives -= 1
                    shapes.remove(shape)
                    if player_lives <= 0:
                        game_over = True
                        if score > high_score:
                            high_score = score
                            with open("highscore.txt", "w") as file:
                                file.write(str(high_score))
                elif cy > SCREEN_HEIGHT:
                    shapes.remove(shape)
                    score += 1

            elif kind == "hexagon":
                cx, cy, size = data
                cy += shape_speed
                data[1] = cy
                points = [(cx + size * math.cos(i * 2 * math.pi / 6 - math.pi / 2),
                        cy + size * math.sin(i * 2 * math.pi / 6 - math.pi / 2)) for i in range(6)]
                pygame.draw.polygon(screen, (11, 200, 108), points)
                if player.collidepoint(cx, cy):
                    hurt_sound.play()
                    player_lives -= 1
                    shapes.remove(shape)
                    if player_lives <= 0:
                        game_over = True
                        if score > high_score:
                            high_score = score
                            with open("highscore.txt", "w") as file:
                                file.write(str(high_score))
                elif cy > SCREEN_HEIGHT:
                    shapes.remove(shape)
                    score += 1

            elif kind == "triangle":
                cx, cy, size = data
                cy += shape_speed
                data[1] = cy
                points = [(cx, cy), (cx - size, cy + size * 2), (cx + size, cy + size * 2)]
                pygame.draw.polygon(screen, (22, 180, 100), points)
                if player.collidepoint(cx, cy):
                    heal_sound.play()
                    player_lives += 1
                    shapes.remove(shape)
                elif cy > SCREEN_HEIGHT:
                    shapes.remove(shape)
        
        #Increase Speed of Falling shapes overtime
        frame_counter += 1
        if not slow_active and frame_counter % difficulty_interval == 0:
            if normal_shape_speed < max_shape_speed:
                normal_shape_speed += speed_increment
    
    #For Drawing UI
    screen.blit(score_font.render(f"Lives: {player_lives}", True, (255, 100, 100)), (10, 40))
    screen.blit(score_font.render(f"Score: {score}", True, (255, 255, 255)), (10, 10))
    screen.blit(score_font.render(f"High Score: {high_score}", True, (255, 255, 0)), (280, 10))

    if triangle_hint_timer > 0:
        triangle_hint_surface = hint_font.render("Triangle spawned! Grab it for +1 life!", True, (0, 200, 0))
        screen.blit(triangle_hint_surface, (
            SCREEN_WIDTH // 2 - triangle_hint_surface.get_width() // 2, 70))
        triangle_hint_timer -= 1
    
    #GameOver Screen
    if game_over:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        font_big = pygame.font.SysFont(None, 60)
        font_small = pygame.font.SysFont(None, 36)

        game_over_text = font_big.render("GAME OVER", True, (255, 0, 0))
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 200))

        score_text = font_small.render(f"Score: {score}", True, (255, 255, 255))
        high_score_text = font_small.render(f"Highest Score: {high_score}", True, (255, 255, 0))
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 270))
        screen.blit(high_score_text, (SCREEN_WIDTH // 2 - high_score_text.get_width() // 2, 310))

        # Fix button positions to avoid overlap
        restart_button.y = SCREEN_HEIGHT // 2 + 50
        quit_button.y = SCREEN_HEIGHT // 2 + 120

        pygame.draw.rect(screen, (0, 200, 0), restart_button, border_radius=10)
        restart_text = font_small.render("RESTART", True, (255, 255, 255))
        screen.blit(restart_text, (
            restart_button.x + (restart_button.width - restart_text.get_width()) // 2,
            restart_button.y + (restart_button.height - restart_text.get_height()) // 2))

        pygame.draw.rect(screen, (200, 0, 0), quit_button, border_radius=10)
        quit_text = font_small.render("QUIT", True, (255, 255, 255))
        screen.blit(quit_text, (
            quit_button.x + (quit_button.width - quit_text.get_width()) // 2,
            quit_button.y + (quit_button.height - quit_text.get_height()) // 2))

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if restart_button.collidepoint(event.pos):
                    score = 0
                    player_lives = 3
                    shapes.clear()
                    frame_counter = 0
                    normal_shape_speed = 5
                    slow_available = True
                    slow_timer = 0
                    cooldown_timer = 0
                    triangle_spawn_timer = 0
                    click_sound.play()
                    game_over = False
                elif quit_button.collidepoint(event.pos):
                    click_sound.play()
                    pygame.time.delay(200)
                    running = False

    pygame.draw.rect(screen, (255, 255, 255), player)
    pygame.display.flip()

pygame.quit()
