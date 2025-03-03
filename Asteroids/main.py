import pygame
import sys
import random
from pygame.locals import *

# Import game asset modules for shapes, sprites, and scenes.
from assets.shapes import *
from assets.sprites import *
from assets.scenes import *

pygame.font.init()  # Initialize the font module for text rendering.

# Define colors.
BLACK = (0, 0, 0)
# Create a small font for the scoreboard using a custom font file.
SMALL_FONT = pygame.font.Font("assets/fonts/rexlia rg.otf", 16)

# Main game class for the Asteroids game.
class Asteroids_Game:
    def __init__(self):
        # Set game screen dimensions.
        self.WIDTH, self.HEIGHT = 650, 650
        # Initialize the game window.
        self.WIN = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Asteroids")  # Set window title.
        pygame.mouse.set_visible(False)  # Hide the mouse cursor.
        # Set the window icon.
        pygame.display.set_icon(pygame.image.load("assets/images/icon.png"))

        self.clock = pygame.time.Clock()  # Clock to manage FPS.
        self.FPS = 60  # Target frames per second.

        # Create a separate canvas surface for drawing game elements.
        self.canvas = pygame.Surface((self.WIDTH, self.HEIGHT))

        # Dictionary to hold player objects (key: device_id, value: Player object).
        self.players = {}
        self.main_player = None  # Reference to the local player.
        self.add_player("local")  # Add the local player to the game.
        
        # Initialize game objects.
        self.bullets = Bullets(self.WIDTH, self.HEIGHT)
        self.asteroids = Asteroids(self.WIDTH, self.HEIGHT).next_round()
        self.menu = Menu()
        self.game_over = Game_over(self.canvas)
        self.pause = Pause(self.canvas)

        # Flags for player's actions.
        self.fire = False
        self.move = False

        # Game time limit (90 seconds) and game state flag.
        self.time_left = 90.0
        self.game_ended = False  # Stops game updates when time expires.

        # Variables used for screen shake effect.
        self.shake = False
        self.shake_timer = 0

    def add_player(self, device_id):
        """
        Create and add a new Player object to the game.
        :param device_id: Identifier for the new player.
        :return: The newly created Player object.
        """
        new_player = Player(self.WIDTH, self.HEIGHT, device_id)
        self.players[device_id] = new_player
        # Set the first added player as the main (local) player.
        if self.main_player is None:
            self.main_player = new_player
        return new_player

    def remove_player(self, device_id):
        """
        Remove a player from the game based on their device ID.
        :param device_id: Identifier of the player to remove.
        """
        if device_id in self.players:
            del self.players[device_id]

    def reset_game(self):
        """
        Reset the game state including players, bullets, asteroids, and game timer.
        """
        # Reinitialize all players while preserving their device IDs.
        for device_id in self.players:
            self.players[device_id] = Player(self.WIDTH, self.HEIGHT, device_id)
        self.main_player = self.players.get("local")
        
        # Reset bullets and asteroid objects.
        self.bullets = Bullets(self.WIDTH, self.HEIGHT)
        self.asteroids = Asteroids(self.WIDTH, self.HEIGHT).next_round()
        self.fire = False
        self.time_left = 90.0
        self.game_ended = False

    def draw(self):
        """
        Draw all game elements to the canvas and update the display.
        Includes handling for a screen shake effect.
        """
        # Determine if screen shaking is needed and set a timer for the shake duration.
        if self.shake and self.shake_timer == 0:
            self.shake_timer = 15  # Duration for the shake effect.
        # Calculate a random offset for the screen shake if active.
        roll = [random.randint(-2, 2), random.randint(-2, 2)] if self.shake_timer > 0 else [0, 0]
        self.shake_timer = max(0, self.shake_timer - 1)
        self.shake = False  # Reset shake flag after applying effect.

        self.canvas.fill(BLACK)  # Clear the canvas with a black background.
        
        # Draw each player's sprite onto the canvas.
        for device_id, player in self.players.items():
            player.draw(self.canvas)
        
        # Sort players by score and display the top 3 on the scoreboard.
        top_players = sorted(self.players.items(), key=lambda item: item[1].score, reverse=True)[:3]
        for idx, (device_id, player) in enumerate(top_players):
            text = SMALL_FONT.render(f"{device_id}: {player.score}", True, (255, 255, 255))
            self.canvas.blit(text, (10, 10 + idx * (SMALL_FONT.get_height() + 2)))
        
        # Display remaining game time.
        time_text = SMALL_FONT.render(f"Time Left: {int(self.time_left)}", True, (255, 255, 255))
        self.canvas.blit(time_text, (self.WIDTH - time_text.get_width() - 10, 10))
        
        # Draw bullets and asteroids onto the canvas.
        self.bullets.draw(self.canvas)
        self.asteroids.draw(self.canvas)

        # Blit the canvas to the game window with any shake offset.
        self.WIN.blit(self.canvas, (roll[0], roll[1]))
        pygame.display.update()  # Refresh the display.

    def check_for_new_players(self):
        """
        Simulate receiving new players via a network JSON message.
        For testing purposes, this dummy logic randomly adds a new player.
        """
        # Only allow up to 20 players; use a random chance to simulate incoming JSON data.
        if len(self.players) < 20 and random.random() < 0.01: 
            # Example of simulated JSON data: {"device_id": "device_X", "angle": some_value}
            simulated_json = {"device_id": f"device_{len(self.players)}", "angle": random.choice([15, -15, 0])}
            device_id = simulated_json["device_id"]
            angle_value = simulated_json["angle"]
            # Add the new player if they don't already exist.
            if device_id not in self.players:
                self.add_player(device_id)
                print(f"New remote player joined: {device_id}")
            # Update the player's tilt based on the received angle value.
            self.players[device_id].apply_remote_tilt(angle_value)

    def main(self):        
        """
        Main game loop that handles game logic, event processing, and drawing.
        """
        run = True
        while run:
            # Check for incoming players and update their state.
            self.check_for_new_players()

            # If the game is not over, update the game timer.
            if not self.game_ended:
                self.time_left -= 1 / self.FPS
                if self.time_left <= 0:
                    self.game_ended = True
                    # When time expires, compute the winner based on highest score.
                    winner_id, winner_player = max(self.players.items(), key=lambda item: item[1].score)
                    self.winner_text = f"Winner: {winner_id}  Score: {winner_player.score}"

            # If the game is over, display the game-over screen and handle reset.
            if self.game_ended:
                reset = self.game_over.loop(self.WIN, self.winner_text, self.menu)
                if reset:
                    self.reset_game()
                self.clock.tick(self.FPS)
                continue

            # If the menu is active, run the menu loop.
            if self.menu.menu:
                self.menu.loop(self.WIN)
            else:
                # When there are no asteroids left, prepare the next round.
                if not len(self.asteroids.asteroids):
                    self.asteroids.asteroid_no += 1
                    # Limit the maximum number of asteroids to 6.
                    if self.asteroids.asteroid_no > 6: 
                        self.asteroids.asteroid_no = 6
                    self.asteroids.next_round()

                # Event handling.
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_UP:
                            self.move = True  # Start moving when up arrow is pressed.
                        if event.key == pygame.K_SPACE:
                            self.fire = True  # Start firing when space is pressed.
                        if event.key == K_p: 
                            CLICK_SOUND.play()  # Play pause sound.
                            # Pause the game; if reset is requested from pause, restart the game.
                            reset = self.pause.loop(self.WIN, self.canvas, self.menu, self.clock, self.FPS)
                            if reset:
                                self.reset_game()
                    if event.type == KEYUP:
                        if event.key == K_SPACE:
                            self.fire = False  # Stop firing when space is released.
                        if event.key == K_UP:
                            self.move = False  # Stop moving when up arrow is released.

                # Update each player's state (movement, safe timer, death animation).
                for device_id, player in self.players.items():
                    player.update()
                    # If a player is dead, process the death animation and possible respawn.
                    if player.dead:
                        health, end = player.death()
                        if end:
                            # Create a new player with the same score and bonus thresholds.
                            new_player = Player(self.WIDTH, self.HEIGHT, device_id)
                            new_player.score = player.score
                            new_player.bonus_threshold_count = player.bonus_threshold_count
                            new_player.safe = True  # Make the new player temporarily safe.
                            new_player.timer = 300  # Set invulnerability timer.
                            self.players[device_id] = new_player
                            # Update the main player reference if necessary.
                            if device_id == "local":
                                self.main_player = new_player

                # Handle movement for the main (local) player if they are not dead.
                if not self.main_player.dead:
                    self.main_player.move(self.move)

                # Move asteroids and detect collisions with players and bullets.
                # This function also returns whether a screen shake should occur.
                self.shake = self.asteroids.move(self.players, self.bullets.bullets, self.game_over, self.shake)
                # Handle bullet behavior (firing, collision) for the main player.
                self.bullets.bullet_handler(self.main_player, self.fire)
                # Render all game objects on the screen.
                self.draw()

            self.clock.tick(self.FPS)  # Maintain the game loop at the target FPS.

# Entry point: start the game when the script is run.
if __name__ == '__main__':
    Asteroids_Game().main()
