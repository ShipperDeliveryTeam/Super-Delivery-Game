from src.entities.directional_shipper import DirectionalShipper
from pathlib import Path
from typing import List, Optional, Tuple

# pyrefly: ignore [missing-import]
import pygame

from .command_handler import CommandHandlerMixin
from .constants import GAME_TITLE, GRID_COLS, GRID_ROWS, SCREEN_WIDTH, TILE_SIZE
from .event_handler import EventHandler
from .game_state import GameState
from .settings import GameSettings
from .state_updater import StateUpdaterMixin
from src.ai.game_pathfinder import GamePathfinder
from src.gameplay.delivery_manager import DeliveryManagerMixin
from src.gameplay.delivery_task import DeliveryTask
from src.gameplay.game_flow import GameFlowMixin
from src.gameplay.gameplay_controller import GameplayControllerMixin
from src.gameplay.movement_service import MovementServiceMixin
from src.gameplay.order_generator import OrderGenerator
from src.gameplay.auto.controller import AutoModeMixin
from src.gameplay.play.controller import PlayModeMixin
from src.maps.map_manager import MapManagerMixin
from src.maps.matrix_loader import MatrixLoader
from src.maps.tmx_loader import TmxMapLoader
from src.systems.asset_manager import AssetManagerMixin
from src.systems.sprite_loader import SpriteLoader
from src.systems.stats_logger import StatsLogger
from src.ui.button import ButtonMixin
from src.ui.game_renderer import GameRendererMixin
from src.ui.hud import HudMixin
from src.ui.menu import MenuMixin
from src.ui.pause_menu import PauseMenuMixin
from src.ui.popup import PopupMixin
from src.ui.result_screen import ResultScreenMixin
from src.ui.text_renderer import TextRendererMixin
from src.ui.viewport import ViewportMixin


class GameManager(
    ViewportMixin,
    MenuMixin,
    ButtonMixin,
    PopupMixin,
    GameRendererMixin,
    HudMixin,
    PauseMenuMixin,
    ResultScreenMixin,
    TextRendererMixin,
    CommandHandlerMixin,
    StateUpdaterMixin,
    PlayModeMixin,
    AutoModeMixin,
    MovementServiceMixin,
    DeliveryManagerMixin,
    GameFlowMixin,
    GameplayControllerMixin,
    MapManagerMixin,
    AssetManagerMixin,
):
    def __init__(self, settings: GameSettings | None = None, debug: bool = False) -> None:
        pygame.init()
        pygame.font.init()

        self.settings = settings or GameSettings()
        self.settings.debug = bool(debug or self.settings.debug)

        self.screen = pygame.display.set_mode(self.settings.get_window_size())
        pygame.display.set_caption(self.settings.title or GAME_TITLE)

        self.clock = pygame.time.Clock()
        self.event_handler = EventHandler()
        self.state = GameState.MENU
        self.running = True

        self.font_big = pygame.font.SysFont("arial", 42, bold=True)
        self.font_mid = pygame.font.SysFont("arial", 24, bold=True)
        self.font_small = pygame.font.SysFont("arial", 18)
        self.font_tiny = pygame.font.SysFont("arial", 15)

        self.sprite_loader = SpriteLoader(TILE_SIZE)
        self.matrix_loader = MatrixLoader(GRID_COLS, GRID_ROWS)
        self.tmx_loader = TmxMapLoader(GRID_COLS, GRID_ROWS, TILE_SIZE)
        self.stats_logger = StatsLogger("stats.csv")
        self.order_generator = OrderGenerator()

        self.map_image = None
        self.map_source = "none"
        self.icons = {}
        self.ui_logo = None
        self.ui_background = None
        self.ui_shipper = None
        self.ui_simulation_button = None
        self.ui_play_button = None
        self.ui_sound_on = None
        self.ui_sound_off = None
        self.ui_menu_button = None

        self.simulation_button_rect = None
        self.play_button_rect = None
        self.sound_button_rect = None
        self.menu_button_rect = None
        self.rules_button_rect = None
        self.window_button_rect = None
        self.exit_button_rect = None
        self.close_popup_rect = None
        self.windowed_button_rect = None
        self.fullscreen_button_rect = None

        self.menu_panel_open = False
        self.rules_popup_open = False
        self.window_popup_open = False
        self.fullscreen_enabled = False
        self.menu_cloud_offset = 0.0
        self.ui_logo = None
        self.ui_background = None
        self.ui_shipper = None

        self.grid_matrix = self.matrix_loader.create_demo_matrix()
        self.map_cols = GRID_COLS
        self.map_rows = GRID_ROWS
        self.blocked_positions = set()

        self.store_positions: list[Tuple[int, int]] = []
        self.house_positions: list[Tuple[int, int]] = []
        self.trap_positions: set[Tuple[int, int]] = set()

        self.player_spawn: Tuple[int, int] = (3, 3)
        self.npc_spawns: list[Tuple[int, int]] = []

        self.pathfinder = GamePathfinder(
            GRID_COLS,
            GRID_ROWS,
            set(),
            allow_diagonal=self._allow_diagonal_movement(),
            roundabout_ring=self._roundabout_ring(),
            roundabout_connections=self._roundabout_connections(),
        )

        self.player: Optional[DirectionalShipper] = None
        self.player_task: Optional[DeliveryTask] = None
        self.player_path_hint: List[Tuple[int, int]] = []
        self.player_path_expanded = 0
        self._player_last_trap_penalty_pos: Tuple[int, int] | None = None

        self.npc_shippers: list[DirectionalShipper] = []
        self.npc_tasks: dict[str, DeliveryTask] = {}
        self.npc_paths: dict[str, List[Tuple[int, int]]] = {}
        self.npc_expanded: dict[str, int] = {}

        self.move_dir = (0, 0)
        self.move_timer = 0.0
        self.npc_timer = 0.0
        self.order_timer = 0.0

        self.elapsed_time = 0.0
        self.result_logged = False
        self.winner_name = ""
        self.auto_player_enabled = False
        self.simulation_mode = False
        self.hud_mode = 1

        self._load_assets()
        self._load_map_for_selected_map()
        self._reset_game()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(self.settings.fps) / 1000.0
            self._handle_commands()
            self._update(dt)
            self._draw()

        pygame.quit()
