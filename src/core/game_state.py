from enum import Enum


class GameState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    WIN = "win"
    GAME_OVER = "game_over"
    EXIT = "exit"
