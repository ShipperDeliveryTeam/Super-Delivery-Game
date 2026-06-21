from enum import Enum


class GameState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    SIMULATION = "simulation"
    PAUSED = "paused"
    WIN = "win"
    GAME_OVER = "game_over"
    EXIT = "exit"
