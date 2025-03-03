from numpy import angle
import pygame
from pygame.locals import *
from math import cos, sin, radians
import random
from assets.shapes import *

pygame.mixer.init()  # Initialize the mixer module for playing sounds.

# Player class represents the ship controlled by a player.
class Player:
    def __init__(self, width, height, device_id="local"):
        self.width, self.height = width, height  # Store game dimensions.
        self.device_id = device_id  # Device identifier.

        # Generate a unique color based on the device_id using MD5 hashing.
        import hashlib
        hash_val = int(hashlib.md5(device_id.encode()).hexdigest(), 16)
        self.color = ((hash_val & 0xFF0000) >> 16,
                      (hash_val & 0x00FF00) >> 8,
                      hash_val & 0x0000FF)

        # Build the ship's shape from three points (forming a triangle).
        # The ship is centered and its shape is determined by these three points.
        self.center = list(coords_to_rect([
            [width/2, height/2-50],
            [width/2-25, height/2+20],
            [width/2+25, height/2+20]
        ]).center)
        # Create three line segments for the ship's body and enlarge them.
        self.body = [
            Line([[width/2, height/2-50], [width/2-25, height/2+20]]).enlarge(0.6, self.center),
            Line([[width/2, height/2-50], [width/2+25, height/2+20]]).enlarge(0.6, self.center),
            Line([[width/2-20, height/2+4], [width/2+20, height/2+4]]).enlarge(0.6, self.center)
        ]
        # Determine the top point of the ship (the tip of the triangle).
        self.top = enlarge_coord([width/2, height/2-50], 0.6, self.center)

        self.angle = 0  # Starting rotation angle.
        self.ROTATION = 4  # How many degrees the ship rotates per update.

        self.VEL = 5  # Maximum velocity.
        self.vector = [0, 0]  # Current velocity vector.
        self.max_vel = [0, 0]  # Maximum velocity components based on current angle.
        self.direction = [1, 1]  # Direction multipliers for x and y axes.

        self.safe = False  # Indicates if the player is in invulnerable (safe) mode.
        self.timer = 0  # Timer for safe mode duration.
        self.visible = True  # Visibility flag for drawing.

        # Health is not used in a time-based game; a dummy value is assigned.
        self.health = 999  
        self.HEALTH_IMG = pygame.image.load("assets/images/health bar.png")
        self.HEALTH_IMG.set_colorkey((0, 0, 0))
        self.dead = False  # Indicates if the player is dead.
        self.death_timer = 180  # Timer used during the death animation.
        # Predefined movement adjustments for each line during the death animation.
        self.movements = [[-0.5, -0.5], [0.5, -0.5], [0, 0.5]]
        
        # Score and bonus counter for tracking performance.
        self.score = 0
        self.bonus_threshold_count = 1

    def death(self):
        """
        Run the death animation for the player.
        The animation rotates and moves each part of the ship.
        Returns a tuple with the player's health and a flag indicating if the animation is complete.
        """
        if self.death_timer == 180:
            # Choose random rotation values for each line on the first frame of death.
            self.angles = [random.choice([-3, 3]),
                           random.choice([-3, 3]),
                           random.choice([-3, 3])]
        # Apply movement and rotation for each line in the ship's body.
        for i, line in enumerate(self.body):
            line.move(self.movements[i][0], self.movements[i][1])
            line.rotate(self.angles[i])
        self.death_timer -= 1  # Decrement death animation timer.
        if self.death_timer <= 0:
            self.dead = False  # Reset death flag after animation ends.
            self.death_timer = 180  # Reset timer for future use.
            return self.health, True  # Animation finished.
        return self.health, False  # Animation still in progress.

    def move(self, move):
        """
        Handle player movement including rotation, acceleration, deceleration, and screen wrapping.
        :param move: Boolean indicating if the ship should accelerate.
        """
        keys = pygame.key.get_pressed()
        if keys[K_LEFT]:
            self.angle -= self.ROTATION
            if self.angle < 0:
                self.angle += 360  # Keep angle within 0-359 degrees.
            # Rotate each line in the body to reflect the change in angle.
            for line in self.body:
                line.rotate(-self.ROTATION, self.center)
            self.top = rotate_coord(self.top, -self.ROTATION, self.center)
        if keys[K_RIGHT]:
            self.angle += self.ROTATION
            if self.angle >= 360:
                self.angle -= 360
            for line in self.body:
                line.rotate(self.ROTATION, self.center)
            self.top = rotate_coord(self.top, self.ROTATION, self.center)
        
        # Determine maximum velocity based on the current rotation angle.
        self.max_vel = [self.VEL*sin(radians(self.angle)),
                        -self.VEL*cos(radians(self.angle))]
        # Set movement direction for proper acceleration and deceleration.
        self.direction[0] = 1 if (0 < self.angle < 180) else -1
        self.direction[1] = 1 if (90 < self.angle < 270) else -1
        
        if move:
            # Accelerate the ship gradually when movement is active.
            self.vector[0] += self.max_vel[0]*0.02
            self.vector[1] += self.max_vel[1]*0.02
            # Clamp velocity to the maximum values.
            if (self.vector[0] > self.max_vel[0] and self.direction[0] > 0) or \
               (self.vector[0] < self.max_vel[0] and self.direction[0] < 0):
                self.vector[0] = self.max_vel[0]
            if (self.vector[1] > self.max_vel[1] and self.direction[1] > 0) or \
               (self.vector[1] < self.max_vel[1] and self.direction[1] < 0):
                self.vector[1] = self.max_vel[1]
        else:
            # Decelerate the ship when movement is not active.
            self.vector[0] -= self.max_vel[0]*0.005
            self.vector[1] -= self.max_vel[1]*0.005
            # Stop movement if velocity reverses sign.
            if (self.vector[0] < 0 and self.direction[0] > 0) or \
               (self.vector[0] > 0 and self.direction[0] < 0):
                self.vector[0] = 0
            if (self.vector[1] < 0 and self.direction[1] > 0) or \
               (self.vector[1] > 0 and self.direction[1] < 0):
                self.vector[1] = 0
        
        # Update the position of each part of the ship by adding the current velocity.
        for line in self.body:
            line.move(self.vector[0], self.vector[1])
        self.top = [self.top[0]+self.vector[0], self.top[1]+self.vector[1]]
        self.center = [self.center[0]+self.vector[0], self.center[1]+self.vector[1]]
        
        # --- Screen Wrapping for Player ---
        dx, dy = 0, 0
        # Check if the player has moved beyond the horizontal boundaries.
        if self.center[0] > self.width + 31:
            dx = - (self.center[0] + 31)
            self.center[0] = -31
        elif self.center[0] < -31:
            dx = (self.width + 31) - self.center[0]
            self.center[0] = self.width + 31
        # Check if the player has moved beyond the vertical boundaries.
        if self.center[1] > self.height + 43:
            dy = - (self.center[1] + 43)
            self.center[1] = -43
        elif self.center[1] < -43:
            dy = (self.height + 43) - self.center[1]
            self.center[1] = self.height + 43
        # Apply the wrapping offset to all parts of the ship.
        if dx != 0 or dy != 0:
            for line in self.body:
                line.move(dx, dy)
            self.top = [self.top[0] + dx, self.top[1] + dy]
        # -----------------------------------

        # If the player is in safe mode, decrement the timer.
        if self.safe:
            self.timer -= 1
            if self.timer <= 0:
                self.safe = False

    def update(self):
        """
        Update player status; currently used to manage the safe mode timer.
        """
        if self.safe:
            self.timer -= 1
            if self.timer <= 0:
                self.safe = False

    def draw(self, surface):
        """
        Draw the player's ship on the given surface.
        Blinks the sprite if in safe mode to indicate invulnerability.
        """
        if self.safe and not self.dead and (self.timer % 25 < 12):
            draw_sprite = False  # Skip drawing to create a blinking effect.
        else:
            draw_sprite = True
        if draw_sprite:
            for line in self.body:
                line.aadraw(surface, self.color)

    def apply_remote_tilt(self, angle_value):
        """
        Adjust the player's rotation based on a remote tilt value.
        Positive values rotate right; negative values rotate left.
        The rotation amount is scaled relative to a base tilt value (15).
        """
        if abs(angle_value) < 1:
            return
        # Determine the scaled rotation amount.
        rotation_amount = self.ROTATION * (abs(angle_value) / 15.0)
        if angle_value > 0:
            self.angle += rotation_amount
            for line in self.body:
                line.rotate(rotation_amount, self.center)
            self.top = rotate_coord(self.top, rotation_amount, self.center)
        else:
            self.angle -= rotation_amount
            for line in self.body:
                line.rotate(-rotation_amount, self.center)
            self.top = rotate_coord(self.top, -rotation_amount, self.center)

# Bullets class handles the creation, movement, and drawing of bullets fired by players.
class Bullets:
    def __init__(self, width, height):
        self.width, self.height = width, height  # Screen dimensions.
        self.bullets = []  # List to store active bullets.
        self.VEL = 11  # Bullet velocity.
        self.key_pressed = False  # Flag to prevent multiple bullets from a single press.
        self.FIRE_SOUND = pygame.mixer.Sound("assets/sounds/fire.wav")
        self.FIRE_SOUND.set_volume(0.25)

    def bullet_handler(self, player, fire):
        """
        Update bullet positions and handle bullet creation and removal.
        :param player: The player firing the bullet.
        :param fire: Boolean flag indicating if the fire button is pressed.
        """
        # Update each bullet's position and remove if out of screen bounds.
        for index, bullet in reversed(list(enumerate(self.bullets))):
            bullet[0].x += bullet[1]
            bullet[0].y += bullet[2]
            if not (0 < bullet[0].x < self.width) or not (0 < bullet[0].y < self.height):
                self.bullets.pop(index)
        # If firing and a bullet hasn't already been spawned for this press, create a new bullet.
        if fire and not self.key_pressed and not player.dead:
            self.FIRE_SOUND.play()
            # Append a new bullet: its shape, x and y velocity, and the shooter's device ID.
            self.bullets.append([
                Circle(player.top, 2.5),
                self.VEL*sin(radians(player.angle)),
                -self.VEL*cos(radians(player.angle)),
                player.device_id
            ])
            self.key_pressed = True
        elif not fire:
            self.key_pressed = False

    def draw(self, surface):
        """
        Draw all active bullets on the provided surface.
        """
        for bullet in self.bullets:
            bullet[0].draw(surface, (255, 255, 255))

# Asteroids class manages asteroid spawning, movement, collision detection, and particle effects.
class Asteroids:
    def __init__(self, width, height):
        self.width, self.height = width, height  # Game screen dimensions.
        self.asteroids = []  # List to store asteroid objects.
        # Define possible spawn ranges for asteroids on the screen.
        self.spawn_range = [
            [0, width//3, 0, height//3],
            [width//3, int(width*(2/3)), 0, height//3],
            [int(width*(2/3)), width, 0, height//3],
            [0, width//3, height//3, int(height*(2/3))],
            [int(width*(2/3)), width, height//3, int(height*(2/3))],
            [0, width//3, int(height*(2/3)), height],
            [width//2, int(width*(2/3)), int(height*(2/3)), height],
            [int(width*(2/3)), width, int(height*(2/3)), height]
        ]
        # Possible asteroid shapes represented as lists of points.
        self.ASTEROID_SHAPES = [
            [[23, 0], [72, 12], [79, 46], [64, 71], [25, 79], [0, 51], [0, 18]],
            [[25, 0], [79, 24], [79, 54], [46, 79], [2, 61], [0, 19]],
            [[25, 2], [66, 0], [79, 38], [67, 63], [38, 79], [14, 69], [0, 20]]
        ]
        self.asteroid_no = 4  # Starting number of asteroids.
        self.SCALE_FACTORS = [1, 0.625, 0.325]  # Scale factors for large, medium, and small asteroids.
        self.VELS = [1, 2, 1.75]  # Velocity values corresponding to different asteroid sizes.
        self.SIZES = ["L", "M", "S"]  # Labels for asteroid sizes.
        self.SCORES = [20, 50, 100]  # Score awarded for destroying each size.
        self.particles = []  # List for particle effects on asteroid destruction.
        self.DECAY = 1.2  # Decay rate for particle lifetimes.
        self.DEATH_SOUND = pygame.mixer.Sound("assets/sounds/dead.wav")
        self.DEATH_SOUND.set_volume(0.25)
        self.ASTEROID_SOUND = pygame.mixer.Sound("assets/sounds/asteroid hit.wav")
        self.ASTEROID_SOUND.set_volume(0.1)

    def spawn_particles(self, coord):
        """
        Spawn particle effects at a given coordinate (e.g., upon asteroid destruction).
        :param coord: The coordinate where the particles should originate.
        """
        number = random.randint(3, 5)  # Randomly decide the number of particles.
        x_vels = []
        y_vels = []
        # Generate each particle with random velocities.
        for i in range(number):
            x_vel, y_vel, x_vels, y_vels = self.velocity_randomizer(1.5, x_vels, y_vels)
            x_vels.append(x_vel)
            y_vels.append(y_vel)
            timer = random.randint(45, 60)  # Lifetime of the particle.
            self.particles.append([coord[:], x_vel, y_vel, timer])

    def handle_particles(self):
        """
        Update particle positions and remove them once their timer has decayed.
        """
        for index, particle in reversed(list(enumerate(self.particles))):
            particle[0][0] += particle[1]
            particle[0][1] += particle[2]
            particle[3] -= self.DECAY 
            if particle[3] <= 0: 
                self.particles.pop(index)

    def velocity_randomizer(self, size, x_vels, y_vels):
        """
        Generate random velocity components ensuring they are not too small or duplicates.
        :param size: Maximum absolute value for velocity.
        :param x_vels: List of x velocities already used.
        :param y_vels: List of y velocities already used.
        :return: Tuple of (x_vel, y_vel, updated x_vels, updated y_vels).
        """
        x_vel = random.uniform(-size, size)
        while (x_vel in x_vels) or -0.1 < x_vel < 0.1: 
            x_vel = random.uniform(-size, size)
        y_vel = random.uniform(-size, size)
        while (y_vel in y_vels) or -0.1 < y_vel < 0.1:
            y_vel = random.uniform(-size, size)
        return x_vel, y_vel, x_vels, y_vels

    def next_round(self):
        """
        Generate a new round of asteroids by spawning them in random positions.
        """
        x_vels = []
        y_vels = []
        for i in range(self.asteroid_no):
            x_vel, y_vel, x_vels, y_vels = self.velocity_randomizer(self.VELS[0], x_vels, y_vels)
            x_vels.append(x_vel)
            y_vels.append(y_vel)
            asteroid = Polygon(random.choice(self.ASTEROID_SHAPES))
            spawn = random.choice(self.spawn_range)
            asteroid.center = [random.randrange(spawn[0], spawn[1]),
                               random.randrange(spawn[2], spawn[3])]
            # Append asteroid info: shape, velocity, size ("L" for large), and multipliers.
            self.asteroids.append([asteroid, x_vel, y_vel, "L", 1, 1])
        return self

    def spawn_new(self, asteroid):
        """
        Spawn new smaller asteroids when a larger asteroid is hit.
        :param asteroid: The asteroid that was hit.
        :return: A list of newly spawned asteroid objects.
        """
        asteroids = []
        x_vels = []
        y_vels = []
        # Only spawn new asteroids if the original is not the smallest.
        if asteroid[3] != "S":
            for i in range(2):
                x_vel, y_vel, x_vels, y_vels = self.velocity_randomizer(self.VELS[self.SIZES.index(asteroid[3])+1],
                                                                       x_vels, y_vels)
                new_asteroid = Polygon(random.choice(self.ASTEROID_SHAPES)).enlarge(
                    self.SCALE_FACTORS[self.SIZES.index(asteroid[3])+1])
                new_asteroid.center = asteroid[0].center
                asteroids.append([new_asteroid, x_vel, y_vel,
                                  self.SIZES[self.SIZES.index(asteroid[3])+1], 1, 1])
                x_vels.append(x_vel)
                y_vels.append(y_vel)
        return asteroids

    def move(self, players, bullets, game_over, shake):
        """
        Update the positions of asteroids, handle screen wrapping, and detect collisions
        with bullets and players. Also triggers particle effects and sounds.
        :param players: Dictionary of player objects.
        :param bullets: List of active bullets.
        :param game_over: Reference to the game-over handler (not used directly here).
        :param shake: Boolean flag to trigger screen shake effect.
        :return: Updated shake flag indicating if a collision occurred.
        """
        new_asteroids = []
        for index, asteroid in reversed(list(enumerate(self.asteroids))):
            asteroid[0].move(asteroid[1], asteroid[2])
            # Screen wrapping for asteroids.
            if asteroid[0].center[0] > self.width + asteroid[0].rect.width//2:
                asteroid[0].center = [-asteroid[0].rect.width//2, asteroid[0].center[1]]
            elif asteroid[0].center[0] < -asteroid[0].rect.width//2:
                asteroid[0].center = [self.width + asteroid[0].rect.width//2, asteroid[0].center[1]]
            if asteroid[0].center[1] > self.height + asteroid[0].rect.height//2:
                asteroid[0].center = [asteroid[0].center[0], -asteroid[0].rect.height//2]
            elif asteroid[0].center[1] < -asteroid[0].rect.height//2:
                asteroid[0].center = [asteroid[0].center[0], self.height + asteroid[0].rect.height//2]

            collision = False
            # Check collision between asteroid and bullets.
            for j, bullet in reversed(list(enumerate(bullets))):
                if asteroid[0].collidecircle(bullet[0]):
                    points_map = {"L": 20, "M": 30, "S": 40}  # Points awarded per asteroid size.
                    points = points_map.get(asteroid[3], 20)
                    shooter_id = bullet[3]
                    # Award points to the appropriate player.
                    if shooter_id in players:
                        players[shooter_id].score += points
                    else:
                        players["local"].score += points
                    new_asteroids += self.spawn_new(asteroid)
                    self.spawn_particles(asteroid[0].center)
                    self.ASTEROID_SOUND.play()
                    self.asteroids.pop(index)
                    bullets.pop(j)
                    shake = True
                    collision = True
                    break
            if collision:
                continue

            # Check collision between asteroid and each player.
            for device_id, player in players.items():
                if not player.dead and not player.safe:
                    for line in player.body:
                        if line.collidepolygon(asteroid[0]):
                            self.DEATH_SOUND.play()
                            self.ASTEROID_SOUND.play()
                            player.dead = True
                            player.score -= 10  # Penalize the player for the collision.
                            new_asteroids += self.spawn_new(asteroid)
                            self.spawn_particles(asteroid[0].center)
                            self.asteroids.pop(index)
                            shake = True
                            collision = True
                            break
                    if collision:
                        break

        self.asteroids += new_asteroids  # Add newly spawned asteroids.
        self.handle_particles()  # Update particle effects.
        return shake  # Return whether a collision occurred (for screen shake).

    def draw(self, surface):
        """
        Draw all asteroids and active particles onto the provided surface.
        """
        for asteroid in self.asteroids:
            asteroid[0].draw(surface, (255, 255, 255), 2)
        for particle in self.particles:
            pygame.draw.circle(surface, (255, 255, 255), particle[0], 2)
