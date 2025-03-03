# Asteroids Remake: Multiplayer Edition

This project is a modernized version of BrickSigma's original Asteroids remake. While the original was a singleplayer, lives-based game built with Python and Pygame, this version introduces several new features and enhancements, including multiplayer support and a time-based scoring system.

## Key Features

- **Multiplayer Support:** The game now supports multiple players. Players are managed using unique device IDs, enabling both local and remote participants.
- **Time-Based Gameplay:** Instead of traditional lives, the game runs on a 90-second timer. The player with the highest score at the end of the time limit wins the game.
- **Enhanced Scoring and Collision Mechanics:** Points are awarded based on the size of the asteroids destroyed. Larger asteroids yield fewer points while smaller, more challenging ones give higher scores. Collisions with asteroids reduce the player's score.

## Changes from the Original Project

BrickSigma's original project featured:
- **Single-Player Gameplay:** Only one player controlled the ship.
- **Lives-Based System:** Players had a set number of lives and lost them upon collisions.
- **Simpler Mechanics:** The focus was on a straightforward remake of *Asteroids*.

This enhanced version includes:
- **Multiplayer Mode:** A dictionary-based player management system now supports multiple players, including simulated remote players.
- **Time-Based Rounds:** Replacing the traditional lives system, the game now runs on a 90-second timer. The highest-scoring player wins at the end.
- **Remote Tilt Simulation:** Remote players can have their ship's tilt control by an external microcontroller controller.
- **Expanded Asteroid Behavior:** Asteroids come in different sizes, award varying points, and split into smaller pieces when destroyed.

## How to Play

- **Controls:**
  - **Local Player**
    - **Left/Right Arrow Keys:** Rotate your ship.
    - **Up Arrow Key:** Accelerate forward.
    - **Space Bar:** Fire bullets.
    - **P Key:** Pause the game.

  - **Remote Player**
    - **Tilt:** Tilt left or right to  rotate your ship accordingly.
    - **Primary Button:** Hold to accelerate forward. Unhold to decelerate and stop
    - **Secondary Button:** Fire bullets.
  
- **Objective:**  
  Survive and score as many points as possible by destroying asteroids. Avoid collisions, as these will penalize your score.

## Requirements

- Python 3.x
- Pygame
- NumPy
