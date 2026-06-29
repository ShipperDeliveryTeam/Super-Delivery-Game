from dataclasses import dataclass, field
from typing import List, Tuple

from .constants import (
    GAME_TITLE,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    TILE_SIZE,
    GRID_COLS,
    GRID_ROWS,
    DEFAULT_MAP_ID,
    DEFAULT_ALGORITHM,
    TARGET_REVENUE,
    ALGORITHMS,
)


@dataclass
class GameSettings:
    title: str = GAME_TITLE
    screen_width: int = SCREEN_WIDTH
    screen_height: int = SCREEN_HEIGHT
    window_width: int = SCREEN_WIDTH
    window_height: int = SCREEN_HEIGHT
    fps: int = FPS
    tile_size: int = TILE_SIZE
    grid_cols: int = GRID_COLS
    grid_rows: int = GRID_ROWS

    selected_map_id: int = DEFAULT_MAP_ID
    selected_algorithm: str = DEFAULT_ALGORITHM
    selected_algorithm_group_id: int = 1

    sound_enabled: bool = True
    show_grid: bool = False
    show_path_hint: bool = True
    debug: bool = False
    target_revenue: int = TARGET_REVENUE

    available_algorithms: List[str] = field(default_factory=lambda: list(ALGORITHMS))

    def get_window_size(self):
        return (1408, 736)

    def set_map(self, map_id: int) -> None:
        try:
            map_id = int(map_id)
        except Exception:
            return

        if 1 <= map_id <= 3:
            self.selected_map_id = map_id

    def set_algorithm_group(self, group_id: int) -> None:
        try:
            group_id = int(group_id)
        except Exception:
            return

        if 1 <= group_id <= 6:
            self.selected_algorithm_group_id = group_id

    def set_algorithm(self, algorithm: str) -> None:
        algorithm = str(algorithm or "").upper()

        alias = {
            "A*": "ASTAR",
            "A_STAR": "ASTAR",
            "BEAM_SEARCH": "BEAM",
            "PARTIAL": "PARTIAL_OBSERVATION",
            "QLEARNING": "Q_LEARNING",
            "Q-LEARNING": "Q_LEARNING",
        }

        algorithm = alias.get(algorithm, algorithm)

        if algorithm in self.available_algorithms:
            self.selected_algorithm = algorithm

    def toggle_sound(self) -> bool:
        self.sound_enabled = not self.sound_enabled
        return self.sound_enabled

    def toggle_grid(self) -> bool:
        self.show_grid = not self.show_grid
        return self.show_grid

    def toggle_path_hint(self) -> bool:
        self.show_path_hint = not self.show_path_hint
        return self.show_path_hint
