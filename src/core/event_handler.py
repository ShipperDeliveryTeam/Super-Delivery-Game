from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

import pygame


class CommandType(Enum):
    NONE = "none"
    QUIT = "quit"

    START_GAME = "start_game"
    PAUSE_GAME = "pause_game"
    RESTART_GAME = "restart_game"

    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    STOP_MOVE = "stop_move"
    MOUSE_CLICK = "mouse_click"

    SELECT_MAP = "select_map"
    SELECT_ALGORITHM = "select_algorithm"

    TOGGLE_SOUND = "toggle_sound"
    TOGGLE_GRID = "toggle_grid"
    TOGGLE_PATH_HINT = "toggle_path_hint"
    TOGGLE_AUTO_PLAYER = "toggle_auto_player"
    TOGGLE_HUD = "toggle_hud"

    DEBUG_WIN = "debug_win"
    DEBUG_LOSE = "debug_lose"


@dataclass
class GameCommand:
    type: CommandType
    value: Optional[object] = None


class EventHandler:
    def __init__(self) -> None:
        self.last_mouse_pos: Tuple[int, int] = (0, 0)

    def handle_events(self) -> List[GameCommand]:
        commands: List[GameCommand] = []

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                commands.append(GameCommand(CommandType.QUIT))

            elif event.type == pygame.KEYDOWN:
                commands.extend(self._handle_key_down(event.key))

            elif event.type == pygame.KEYUP:
                commands.extend(self._handle_key_up(event.key))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    commands.append(GameCommand(CommandType.MOUSE_CLICK, event.pos))

            elif event.type == pygame.MOUSEMOTION:
                self.last_mouse_pos = event.pos

        return commands

    def _handle_key_down(self, key: int) -> List[GameCommand]:
        commands: List[GameCommand] = []

        if key == pygame.K_ESCAPE:
            commands.append(GameCommand(CommandType.PAUSE_GAME))

        elif key == pygame.K_RETURN:
            commands.append(GameCommand(CommandType.START_GAME))

        elif key in (pygame.K_w, pygame.K_UP):
            commands.append(GameCommand(CommandType.MOVE_UP))

        elif key in (pygame.K_s, pygame.K_DOWN):
            commands.append(GameCommand(CommandType.MOVE_DOWN))

        elif key in (pygame.K_a, pygame.K_LEFT):
            commands.append(GameCommand(CommandType.MOVE_LEFT))

        elif key in (pygame.K_d, pygame.K_RIGHT):
            commands.append(GameCommand(CommandType.MOVE_RIGHT))

        elif key == pygame.K_SPACE:
            commands.append(GameCommand(CommandType.TOGGLE_AUTO_PLAYER))

        elif key == pygame.K_h:
            commands.append(GameCommand(CommandType.TOGGLE_HUD))

        elif key == pygame.K_g:
            commands.append(GameCommand(CommandType.TOGGLE_GRID))

        elif key == pygame.K_p:
            commands.append(GameCommand(CommandType.TOGGLE_PATH_HINT))

        elif key == pygame.K_m:
            commands.append(GameCommand(CommandType.TOGGLE_SOUND))

        elif key == pygame.K_k:
            commands.append(GameCommand(CommandType.DEBUG_WIN))

        elif key == pygame.K_l:
            commands.append(GameCommand(CommandType.DEBUG_LOSE))

        elif key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
            commands.append(GameCommand(CommandType.SELECT_MAP, int(pygame.key.name(key))))

        elif key == pygame.K_F1:
            commands.append(GameCommand(CommandType.SELECT_ALGORITHM, "BFS"))

        elif key == pygame.K_F2:
            commands.append(GameCommand(CommandType.SELECT_ALGORITHM, "ASTAR"))

        elif key == pygame.K_F3:
            commands.append(GameCommand(CommandType.SELECT_ALGORITHM, "BEAM"))

        elif key == pygame.K_F4:
            commands.append(GameCommand(CommandType.SELECT_ALGORITHM, "PARTIAL_OBSERVATION"))

        elif key == pygame.K_F5:
            commands.append(GameCommand(CommandType.SELECT_ALGORITHM, "Q_LEARNING"))

        return commands

    def _handle_key_up(self, key: int) -> List[GameCommand]:
        if key in (
            pygame.K_w,
            pygame.K_UP,
            pygame.K_s,
            pygame.K_DOWN,
            pygame.K_a,
            pygame.K_LEFT,
            pygame.K_d,
            pygame.K_RIGHT,
        ):
            return [GameCommand(CommandType.STOP_MOVE)]

        return []
