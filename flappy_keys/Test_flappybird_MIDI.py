import pygame
import pygame.midi
import mido
from mido import MidiFile, Message, MidiTrack
import random
import time
from collections import deque

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
note_events = deque(maxlen=10) 

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

leaderboard_left = []
leaderboard_right = []

try:
    with open("leaderboard.txt", "r") as f:
        leaderboard = [line.strip().split(',') for line in f]
        leaderboard = [(name, float(score)) for name, score in leaderboard]
    leaderboard.sort(key=lambda x: x[1], reverse=True)
except FileNotFoundError:
    leaderboard = []

def update_leaderboard(hand, name, time):
    global leaderboard_left, leaderboard_right
    if hand == 'left':
        leaderboard_left.append((name, time))
        leaderboard_left.sort(key=lambda x: x[1], reverse=True)
        leaderboard_left = leaderboard_left[:5]
    else:
        leaderboard_right.append((name, time))
        leaderboard_right.sort(key=lambda x: x[1], reverse=True)
        leaderboard_right = leaderboard_right[:5]


def update_leaderboard(hand, name, score):
    global leaderboard_left, leaderboard_right
    if hand == 'left':
        leaderboard_left.append((name, score))
        leaderboard_left.sort(key=lambda x: x[1], reverse=True)
        leaderboard_left = leaderboard_left[:5]  # Keep top 5
    else:
        leaderboard_right.append((name, score))
        leaderboard_right.sort(key=lambda x: x[1], reverse=True)
        leaderboard_right = leaderboard_right[:5]  # Keep top 5


def display_leaderboards(screen):
    # Display Left Hand Leaderboard
    start_y_left = 50
    font = pygame.font.SysFont(None, 36)
    display_text(screen, "Left Hand Leaderboard", (50, start_y_left - 30), size=30, color=(0, 0, 255))
    for name, score in leaderboard_left[:5]:
        text_surf = font.render(f"{name}: {score:.2f}s", True, (0, 0, 0))
        screen.blit(text_surf, (50, start_y_left))
        start_y_left += 30

    # Display Right Hand Leaderboard
    start_y_right = 50
    display_text(screen, "Right Hand Leaderboard", (400, start_y_right - 30), size=30, color=(0, 0, 255))
    for name, score in leaderboard_right[:5]:
        text_surf = font.render(f"{name}: {score:.2f}s", True, (0, 0, 0))
        screen.blit(text_surf, (400, start_y_right))  # Adjust position as needed
        start_y_right += 30
    
def save_leaderboards():
    with open("leaderboard_left.txt", "w") as f_left, open("leaderboard_right.txt", "w") as f_right:
        for name, score in leaderboard_left:
            f_left.write(f"{name},{score}\n")
        for name, score in leaderboard_right:
            f_right.write(f"{name},{score}\n")

def load_leaderboards():
    global leaderboard_left, leaderboard_right
    try:
        with open("leaderboard_left.txt", "r") as f_left:
            leaderboard_left = [line.strip().split(',') for line in f_left]
            leaderboard_left = [(name, float(score)) for name, score in leaderboard_left]
        with open("leaderboard_right.txt", "r") as f_right:
            leaderboard_right = [line.strip().split(',') for line in f_right]
            leaderboard_right = [(name, float(score)) for name, score in leaderboard_right]
    except FileNotFoundError:
        leaderboard_left = []
        leaderboard_right = []



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

def choose_hand(screen):
    font = pygame.font.SysFont(None, 55)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_l:
                    return 'left'
                elif event.key == pygame.K_r:
                    return 'right'
        
        screen.fill((255, 255, 255))
        text_surf = font.render("Choose Hand: L for Left, R for Right", True, (0, 0, 0))
        screen.blit(text_surf, (100, 250))
        pygame.display.flip()
        clock.tick(30)

def process_keyboard_input():
    global bird_velocity, last_key
    keys = pygame.key.get_pressed()

    if keys[pygame.K_c] or keys[pygame.K_d]:
        new_key = 'C' if keys[pygame.K_c] else 'D'
        if new_key != last_key:
            flap()
            last_key = new_key


def process_midi_events():
    global bird_velocity, last_key

    minimal_gap = 0.05  # Minimum gap between notes to count as separate
    simultaneous_threshold = 0.02  # Threshold for simultaneous note presses

    while True:  # Loop to process available MIDI messages
        msg = midi_input.poll()  # Non-blocking receive
        if msg is None:
            break  # No more messages, break out of the loop

        if msg.type == 'note_on' and msg.velocity > 0:
            current_time = time.time()  # Get the current time
            note_events.append((msg.note, current_time))  # Append note and timestamp

            if len(note_events) < 2:
                continue  # Need at least two events to compare

            # Get the last two note events
            _, prev_time = note_events[-2]
            note, current_time = note_events[-1]

            time_gap = current_time - prev_time

            if time_gap <= simultaneous_threshold:
                continue  # Ignore simultaneous notes

            if note % 12 in [0, 2]:  # Check for C's and D's
                new_key = 'C' if note % 12 == 0 else 'D'
                if new_key != last_key and time_gap > minimal_gap:
                    bird_velocity = flap_strength
                    last_key = new_key
                    print(f"MIDI Note: {note}, Timestamp: {current_time}")




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
last_note_time = time.time()

hand = None  # Variable to store the selected hand

# At game initialization
load_leaderboards()

# Game Loop
# Main Game Loop
while running:
    screen.fill((255, 255, 255))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    if not game_started:
        if keys[pygame.K_SPACE]:
            hand = choose_hand(screen)  # Hand selection right after the game starts
            game_started = True
            game_start_time = pygame.time.get_ticks()
            last_key = None
        else:
            display_text(screen, "Press Space to Start", (150, 250), size=40, color=(0, 0, 0))
    else:
        if not game_over:
            update_bird_position()
            draw_bird(screen, bird_position)
            handle_obstacles()
            handle_collision()
            process_midi_events()
            process_keyboard_input()
        else:
            display_game_over(screen)
            if keys[pygame.K_r]:
                reset_game()
            else:
                if not name_entered:
                    name = prompt_for_name(screen, "New High Score! Enter Name: ")
                    update_leaderboard(hand, name, game_end_time)
                    save_leaderboards()  # Save leaderboards after updating

                    name_entered = True
                display_leaderboards(screen)  # Display both leaderboards

        if game_started and not game_over:
            elapsed_time = (pygame.time.get_ticks() - game_start_time) / 1000
            display_text(screen, f"Time: {elapsed_time:.2f}s", (650, 10), size=30, color=(0, 0, 0))
        if game_over:
            display_game_over(screen)
            if not name_entered:
                name = prompt_for_name(screen, "Enter Name: ")
                update_leaderboard(hand, name, game_end_time)
                save_leaderboards()  # Save leaderboards after updating
                name_entered = True
            display_leaderboards(screen)  # Display updated leaderboards
            if keys[pygame.K_r]:  # Reset the game if 'R' is pressed
                reset_game()

    pygame.display.flip()
    clock.tick(30)


midi_input.close()  # Close the MIDI input
pygame.quit()


