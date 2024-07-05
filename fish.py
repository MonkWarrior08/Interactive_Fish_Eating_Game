import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Initialize Pygame mixer for audio
pygame.mixer.init()

# Set up the display (1080p resolution)
width, height = 1920, 1080
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Dimi and Alice's Fish Eating Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Load and scale background image
background = pygame.image.load("underwater_background.png").convert()
background = pygame.transform.scale(background, (width, height))

# Load background music
pygame.mixer.music.load("sound.wav")
pygame.mixer.music.play(-1)  # -1 means loop indefinitely

# Load and scale fish images once
player_green = pygame.image.load("green_fish.png").convert_alpha()
player_red = pygame.image.load("red_fish.png").convert_alpha()
npc_orange = pygame.image.load("orange_fish.png").convert_alpha()
npc_blue = pygame.image.load("npc_fish.png").convert_alpha()

# Player fish
class Player:
    def __init__(self, x, y, size, controls, name, sprite):
        self.x = x
        self.y = y
        self.size = size
        self.speed = 3
        self.dx = 0
        self.dy = 0
        self.max_speed = 6
        self.angle = 0
        self.controls = controls
        self.score = 0
        self.dead = False
        self.name = name
        self.base_sprite = sprite
        self.update_sprite()

    def update_sprite(self):
        scaled_size = int(self.size * 2), self.size
        self.sprite = pygame.transform.scale(self.base_sprite, scaled_size)
        self.flipped_sprite = pygame.transform.flip(self.sprite, True, False)

    def move(self, keys):
        if self.dead:
            return

        # Apply "water resistance"
        self.dx *= 0.9
        self.dy *= 0.9

        # Move player
        if keys[self.controls['up']]: self.dy -= self.speed
        if keys[self.controls['down']]: self.dy += self.speed
        if keys[self.controls['left']]: self.dx -= self.speed
        if keys[self.controls['right']]: self.dx += self.speed

        # Limit speed
        speed = math.sqrt(self.dx**2 + self.dy**2)
        if speed > self.max_speed:
            self.dx = self.dx / speed * self.max_speed
            self.dy = self.dy / speed * self.max_speed

        # Update position
        self.x += self.dx
        self.y += self.dy

        # Keep player on screen
        self.x = max(self.size, min(width - self.size, self.x))
        self.y = max(self.size // 2, min(height - self.size // 2, self.y))

        # Update angle for drawing
        if self.dx != 0 or self.dy != 0:
            self.angle = math.degrees(math.atan2(-self.dy, self.dx))

    def grow(self, amount):
        self.size += amount
        self.update_sprite()

    def draw(self, screen):
        if self.dead:
            return

        # Choose the correct sprite based on direction
        if self.dx < 0:
            sprite = self.flipped_sprite
            angle = self.angle + 180
        else:
            sprite = self.sprite
            angle = self.angle

        # Rotate the sprite based on the movement direction
        rotated_sprite = pygame.transform.rotate(sprite, angle)
        sprite_rect = rotated_sprite.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(rotated_sprite, sprite_rect)

# Other fish
class Fish:
    def __init__(self, x, y, size, player_size, sprite):
        self.x = x
        self.y = y
        self.size = size
        self.base_speed = random.uniform(1, 3)
        self.speed = self.base_speed
        self.dx = self.base_speed if x < width / 2 else -self.base_speed
        self.dy = 0
        self.max_speed = 4
        self.direction = 1 if x < width / 2 else -1
        self.target = None
        self.chase_time = 0
        self.max_chase_time = random.randint(180, 300)  # 3-5 seconds at 60 FPS
        self.being_chased = False
        self.angle = 0
        self.base_sprite = sprite
        self.is_npc_fish = sprite == npc_blue
        self.update_sprite()

    def update_sprite(self):
        if self.is_npc_fish:
    # Make npc_fish.png slightly thicker
            scaled_size = int(self.size * 2.5), int(self.size * 1.4)  # Increased height factor from 1.25 to 1.4
        else:
            scaled_size = int(self.size * 2.5), int(self.size * 1.25)
        self.sprite = pygame.transform.scale(self.base_sprite, scaled_size)
        self.flipped_sprite = pygame.transform.flip(self.sprite, True, False)

    def move(self, other_fish, players):
        self.being_chased = False
        
        # Check if being chased by a larger fish or player
        for entity in other_fish + players:
            if entity != self and entity.size > self.size * 1.5:
                if isinstance(entity, Fish) and entity.target == self:
                    self.being_chased = True
                    break
                elif isinstance(entity, Player) and not entity.dead:
                    dx = self.x - entity.x
                    dy = self.y - entity.y
                    if math.hypot(dx, dy) < 250:  # Detection radius
                        self.being_chased = True
                        break

        if self.being_chased:
            self.flee(other_fish, players)
        else:
            self.normal_movement(other_fish, players)

        # Apply "water resistance"
        self.dx *= 0.98
        self.dy *= 0.98

        # Limit speed
        speed = math.sqrt(self.dx**2 + self.dy**2)
        if speed > self.max_speed:
            self.dx = self.dx / speed * self.max_speed
            self.dy = self.dy / speed * self.max_speed

        # Update position
        self.x += self.dx
        self.y += self.dy

        # Keep fish on screen vertically
        self.y = max(self.size // 2, min(height - self.size // 2, self.y))

        # Update angle for drawing
        if self.dx != 0 or self.dy != 0:
            self.angle = math.degrees(math.atan2(-self.dy, self.dx))

    def flee(self, other_fish, players):
        threats = other_fish + [p for p in players if not p.dead]
        nearest_threat = min(
            (threat for threat in threats if threat != self and threat.size > self.size * 1.5),
            key=lambda t: math.hypot(self.x - t.x, self.y - t.y),
            default=None
        )

        if nearest_threat:
            dx = self.x - nearest_threat.x
            dy = self.y - nearest_threat.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.dx += (dx / dist) * self.speed * 0.5
                self.dy += (dy / dist) * self.speed * 0.5
            self.direction = 1 if self.dx > 0 else -1
        else:
            self.normal_movement(other_fish, players)

    def normal_movement(self, other_fish, players):
        if not self.target:
            self.find_target(other_fish, players)

        if self.target and (self.target in other_fish or (isinstance(self.target, Player) and not self.target.dead)):
            self.chase_time += 1
            if self.chase_time > self.max_chase_time:
                self.reset_chase()
            else:
                dx = self.target.x - self.x
                dy = self.target.y - self.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    self.dx += (dx / dist) * self.speed * 0.1
                    self.dy += (dy / dist) * self.speed * 0.1
                self.direction = 1 if self.dx > 0 else -1
                return

        # Maintain general direction
        if (self.direction > 0 and self.x > width * 0.9) or (self.direction < 0 and self.x < width * 0.1):
            self.direction *= -1
            self.dx *= -1

        # Random vertical movement
        if random.random() < 0.05:
            self.dy += random.uniform(-0.5, 0.5)

        # Maintain horizontal movement
        self.dx += self.direction * 0.1

    def find_target(self, other_fish, players):
        potential_targets = other_fish + [p for p in players if not p.dead]
        nearest_target = None
        nearest_dist = float('inf')
        for target in potential_targets:
            if target != self and self.size > target.size * 1.5:
                dx = target.x - self.x
                dy = target.y - self.y
                dist = math.hypot(dx, dy)
                if dist < 200 and dist < nearest_dist:  # Chase detection radius
                    nearest_target = target
                    nearest_dist = dist
        if nearest_target:
            self.target = nearest_target
            self.speed = self.base_speed * 1.5  # Increase speed while chasing

    def reset_chase(self):
        self.target = None
        self.chase_time = 0
        self.speed = self.base_speed

    def draw(self, screen):
        if self.dx > 0:
            sprite = self.sprite
            angle = self.angle
        else:
            sprite = self.flipped_sprite
            angle = self.angle + 180

        # Rotate the sprite based on the movement direction
        rotated_sprite = pygame.transform.rotate(sprite, angle)
        sprite_rect = rotated_sprite.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(rotated_sprite, sprite_rect)

# Game variables
player1 = Player(width // 3, height // 2, 30, {'up': pygame.K_w, 'down': pygame.K_s, 'left': pygame.K_a, 'right': pygame.K_d}, "Dimi", player_green)
player2 = Player(2 * width // 3, height // 2, 30, {'up': pygame.K_UP, 'down': pygame.K_DOWN, 'left': pygame.K_LEFT, 'right': pygame.K_RIGHT}, "Alice", player_red)
players = [player1, player2]
other_fish = []
game_over = False
clock = pygame.time.Clock()

# Font
font = pygame.font.Font(None, 54)

def spawn_fish(player_size):
    # Adjust size range to favor smaller fish
    min_size = int(player_size * 0.3)
    max_size = int(player_size * 1.2)
    
    # Use a weighted random choice to favor smaller fish
    size_choices = [
        (min_size, 0.5),                          # 50% chance for minimum size
        (int(player_size * 0.5), 0.3),            # 30% chance for half player size
        (random.randint(min_size, max_size), 0.2) # 20% chance for random size
    ]
    
    size = random.choices([s[0] for s in size_choices], weights=[s[1] for s in size_choices])[0]
    
    x = -size if random.random() < 0.5 else width + size
    y = random.randint(0, height)
    sprite = npc_orange if random.random() < 0.5 else npc_blue
    return Fish(x, y, size, player_size, sprite)

def reset_game():
    global player1, player2, players, other_fish, game_over
    player1 = Player(width // 3, height // 2, 30, {'up': pygame.K_w, 'down': pygame.K_s, 'left': pygame.K_a, 'right': pygame.K_d}, "Dimi", player_green)
    player2 = Player(2 * width // 3, height // 2, 30, {'up': pygame.K_UP, 'down': pygame.K_DOWN, 'left': pygame.K_LEFT, 'right': pygame.K_RIGHT}, "Alice", player_red)
    players = [player1, player2]
    other_fish = []
    game_over = False

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and game_over:
            reset_game()

    if not game_over:
        keys = pygame.key.get_pressed()
        for player in players:
            player.move(keys)

        # Move and check other fish
        fish_to_remove = set()  # Use a set to keep track of fish to remove
        for fish in other_fish[:]:
            fish.move(other_fish, players)
            
            # Check if fish is out of bounds
            if (fish.x < -fish.size or fish.x > width + fish.size or 
                fish.y < -fish.size or fish.y > height + fish.size):
                fish_to_remove.add(fish)
                continue

            # Check collision with players
            for player in players:
                if not player.dead and math.hypot(player.x - fish.x, player.y - fish.y) < (player.size + fish.size) / 2:
                    if player.size > fish.size * 1.5:
                        player.score += 1
                        growth_amount = min(fish.size / 12, player.size)
                        player.grow(growth_amount)
                        fish_to_remove.add(fish)
                        break
                    elif fish.size > player.size * 1.5:
                        player.dead = True
                    break

            # Check collision with other fish
            if fish not in fish_to_remove:
                for other in other_fish[:]:
                    if fish != other and math.hypot(fish.x - other.x, fish.y - other.y) < (fish.size + other.size) / 2:
                        if fish.size > other.size * 1.5:
                            fish.size += 0.25
                            fish.update_sprite()
                            fish_to_remove.add(other)
                            fish.reset_chase()
                            break

        # Remove fish safely
        other_fish = [fish for fish in other_fish if fish not in fish_to_remove]

        # Check if both players are dead
        if all(player.dead for player in players):
            game_over = True

        # Spawn new fish
        if len(other_fish) < 50 and random.random() < 0.1:
            living_players = [player for player in players if not player.dead]
            if living_players:
                max_player_size = max(player.size for player in living_players)
            else:
                max_player_size = 30  # Default size if all players are dead
            other_fish.append(spawn_fish(max_player_size))

        # Draw background
        screen.blit(background, (0, 0))

        # Draw fish
        for fish in other_fish:
            fish.draw(screen)
        for player in players:
            player.draw(screen)

        # Draw scores
        score_text1 = font.render(f"{player1.name}: {player1.score}" + (" (DEAD)" if player1.dead else ""), True, WHITE)
        score_text2 = font.render(f"{player2.name}: {player2.score}" + (" (DEAD)" if player2.dead else ""), True, WHITE)
        screen.blit(score_text1, (15, 15))
        screen.blit(score_text2, (15, 70))

    else:
        # Game over screen
        game_over_text = font.render("Game Over! Press SPACE to restart", True, WHITE)
        screen.blit(game_over_text, (width // 2 - 250, height // 2 - 27))

    # Update display
    pygame.display.flip()

    # Control game speed
    clock.tick(60)

# Quit the game
pygame.mixer.music.stop()
pygame.quit()