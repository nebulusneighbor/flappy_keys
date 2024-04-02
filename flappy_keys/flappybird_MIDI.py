import pygame
import pygame.midi
import mido
from mido import MidiFile, Message, MidiTrack
import random

pygame.init()
pygame.midi.init()

print("from mido", mido.get_input_names())
# Prompt for user choice
midi_input_index = int(input("Enter the index of your MIDI device: "))
midi_input_name = mido.get_input_names()[midi_input_index]
midi_input = mido.open_input(midi_input_name)

print(f"Using MIDI Input: {midi_input_name}")

# # List all available MIDI devices
# for i in range(pygame.midi.get_count()):
#     print("from pygame",pygame.midi.get_device_info(i))

# # Set up the MIDI input device (replace 'input_id' with the correct device ID)
# input_id = pygame.midi.get_default_input_id()
# midi_input = pygame.midi.Input(input_id)

game_end_time = None


last_key = None
name_entered = False
# Alternatively, with mido
# Replace 'Midi Input Name' with the name of your MIDI device
# input_port = mido.open_input('Midi Input Name')
# Game variables
bird_position = [100, 100]  # Starting position of the bird
bird_velocity = 5  # Initial velocity
gravity = 0.5  # Gravity effect
flap_strength = -2.5  # The upward force when the bird flaps
health = 100  # Initial health of the character

def prompt_for_name(screen, prompt):
    name = ""
    font = pygame.font.SysFont(None, 55)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return name
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    name += event.unicode
        screen.fill((255, 255, 255))
        text_surf = font.render(prompt + name, True, (0, 0, 0))
        screen.blit(text_surf, (50, 100))
        pygame.display.flip()
        clock.tick(30)

leaderboard = []
try:
    with open("leaderboard.txt", "r") as f:
        leaderboard = [line.strip().split(',') for line in f]
        leaderboard = [(name, float(score)) for name, score in leaderboard]
    leaderboard.sort(key=lambda x: x[1], reverse=True)
except FileNotFoundError:
    leaderboard = []

def update_leaderboard(leaderboard, name, time):
    leaderboard.append((name, time))
    leaderboard.sort(key=lambda x: x[1], reverse=True)  # Sort by time/score in descending order
    return leaderboard[:5]  # Keep top 5

def display_leaderboard(screen, leaderboard):
    start_y = 10
    for name, time in leaderboard:
        text_surf = font.render(f"{name}: {time:.2f}s", True, (0, 0, 0))
        screen.blit(text_surf, (650, start_y))
        start_y += 30  # Move down for the next entry

class Obstacle:
    def __init__(self, x, width, height, gap, color=(0, 255, 0)):
        self.x = x
        self.width = width
        self.top_height = height  # Height of the top obstacle
        self.gap = gap  # Gap between top and bottom obstacles
        self.color = color
        self.passed = False  # To check if the bird has passed the obstacle

    def draw(self, screen):
        # Draw top obstacle
        pygame.draw.rect(screen, self.color, (self.x, 0, self.width, self.top_height))
        # Draw bottom obstacle
        pygame.draw.rect(screen, self.color, (self.x, self.top_height + self.gap, self.width, 600 - self.top_height - self.gap))

    def move(self, velocity):
        self.x -= velocity  # Move the obstacle to the left

# You can create obstacles like this:
obstacles = []

obstacles.append(Obstacle(800, 70, 200, 150))  # Example obstacle

def handle_obstacles():
    global obstacles, last_obstacle_spawn_time

    current_time = pygame.time.get_ticks()
    if current_time - last_obstacle_spawn_time > spawn_obstacle_every:
        width, height, gap = random.randint(50, 100), random.randint(150, 300), random.randint(100, 200)
        obstacles.append(Obstacle(800, width, height, gap, (0,0,0)))
        last_obstacle_spawn_time = current_time

    for obstacle in obstacles[:]:
        obstacle.move(5)
        obstacle.draw(screen)
        if obstacle.x + obstacle.width < 0:
            obstacles.remove(obstacle)

def handle_collision():
    global game_over, health, game_end_time

    if check_collision(bird_position, obstacles) or bird_position[1] >= 585:  # 585 to consider the ground
        game_over = True
        health = 0
        game_end_time = (pygame.time.get_ticks() - game_start_time) / 1000


def check_collision(bird_position, obstacles):
    global health  # Make sure to declare health as global if you're modifying it
    bird_rect = pygame.Rect(bird_position[0] - 15, bird_position[1] - 15, 30, 30)

    for obstacle in obstacles:
        top_rect = pygame.Rect(obstacle.x, 0, obstacle.width, obstacle.top_height)
        bottom_rect = pygame.Rect(obstacle.x, obstacle.top_height + obstacle.gap, obstacle.width, 600 - obstacle.top_height - obstacle.gap)

        if bird_rect.colliderect(top_rect) or bird_rect.colliderect(bottom_rect) or bird_position[1] >= 585:
            health -= 10  # Reduce health by 10 (or any other value you deem appropriate)
            return True

    return False

def handle_high_score_entry():
    global name_entered, game_end_time, leaderboard  # Added 'leaderboard' to global declaration

    if not name_entered and game_end_time and (len(leaderboard) < 5 or game_end_time > leaderboard[-1][1]):
        name = prompt_for_name(screen, "New High Score! Enter Name: ")
        leaderboard.append((name, game_end_time))
        leaderboard.sort(key=lambda x: x[1], reverse=True)
        leaderboard = leaderboard[:5]  # Keep top 5
        with open("leaderboard.txt", "w") as f:
            for entry in leaderboard:
                f.write(f"{entry[0]},{entry[1]}\n")
        name_entered = True



def display_game_over(screen):
    font = pygame.font.SysFont(None, 55)
    text = font.render('Game Over!', True, (255, 0, 0))
    screen.blit(text, (250, 300))


def generate_obstacle():
    # Generate obstacles at random positions
    pass

def flap():
    global bird_velocity
    bird_velocity = flap_strength

def update_bird_position():
    global bird_position, bird_velocity
    bird_velocity += gravity
    bird_position[1] += bird_velocity

def process_input(last_key):
    global bird_velocity
    for msg in midi_input.iter_pending():
        if msg.type == 'note_on' and msg.velocity > 0:  # Note on
            note = msg.note
            if note % 12 in [0, 2]:  # All C's and D's
                new_key = 'C' if note % 12 == 0 else 'D'
                if new_key != last_key:  # Alternate keys
                    bird_velocity = flap_strength
                    last_key = new_key
                    print(f"MIDI Note: {note}")  # Debugging

    keys = pygame.key.get_pressed()
    if ((keys[pygame.K_c] and last_key != 'C') or (keys[pygame.K_d] and last_key != 'D')) and not any(msg.type == 'note_on' for msg in midi_input.iter_pending()):
        bird_velocity = flap_strength
        last_key = 'C' if keys[pygame.K_c] else 'D'

    return last_key


def draw_bird(screen, position):
    pygame.draw.circle(screen, (255, 200, 0), position, 15)
    # (255, 200, 0) is the RGB color for the bird; position is a tuple (x, y); 15 is the radius of the circle.

def display_text(screen, message, position, size=55, color=(255, 0, 0)):
    font = pygame.font.SysFont(None, size)
    text = font.render(message, True, color)
    screen.blit(text, position)

def reset_game():
    global game_started, game_over, name_entered, bird_position, bird_velocity, health, obstacles, game_start_time, last_key, game_end_time
    game_started = False
    game_over = False
    name_entered = False
    bird_position = [100, 100]
    bird_velocity = 5
    health = 100
    obstacles = []
    game_start_time = pygame.time.get_ticks()
    game_end_time = None
    last_key = None


screen = pygame.display.set_mode((800, 600))  # Set screen size
font = pygame.font.SysFont(None, 36)  # Define the font object here

# Initialize the clock
clock = pygame.time.Clock()
game_start_time = pygame.time.get_ticks()  # Record the start time of the game


# Before the game loop
spawn_obstacle_every = 2000  # milliseconds (e.g., spawn an obstacle every 2 seconds)
last_obstacle_spawn_time = pygame.time.get_ticks()  # Initialize the last spawn time

game_over = False
game_started = False  
running = True

name_entered = False
last_key = None

# Game Loop
while running:
    screen.fill((255, 255, 255))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if not game_started:
        # Display "Press Space to Start" and wait for the SPACE key press to start the game
        if keys[pygame.K_SPACE]:
            game_started = True
            game_start_time = pygame.time.get_ticks()  # Start the game timer
            last_key = None  # Ensure the last key is reset at the start
        else:
            display_text(screen, "Press Space to Start", (150, 250), size=40, color=(0, 0, 0))
    else:
        # Game has started
        if not game_over:
            # Game is running
            last_key = process_input(last_key)
            update_bird_position()
            draw_bird(screen, bird_position)
            handle_obstacles()  # You'll define this function to manage obstacles
            handle_collision()  # You'll define this function to check for collisions
        else:
            # Game is over
            display_game_over(screen)
            if keys[pygame.K_r]:
                reset_game()
            else:
                handle_high_score_entry()  # You'll define this function to handle high score entry and display
                display_leaderboard(screen, leaderboard)

        # Display time elapsed in the upper right corner
        if game_started and not game_over:
            elapsed_time = (pygame.time.get_ticks() - game_start_time) / 1000  # Convert to seconds
            display_text(screen, f"Time: {elapsed_time:.2f}s", (650, 10), size=30, color=(0, 0, 0))

    pygame.display.flip()
    clock.tick(30)

midi_input.close()  # Close the MIDI input
pygame.quit()


