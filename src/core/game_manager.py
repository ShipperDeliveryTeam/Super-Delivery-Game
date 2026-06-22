import random
from pathlib import Path
from typing import List, Optional, Tuple

# pyrefly: ignore [missing-import]
import pygame

from .constants import (
    BACKGROUND_COLOR,
    GRID_LINE_COLOR,
    TEXT_COLOR,
    PLAYER_COLOR,
    NPC_COLORS,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    TILE_SIZE,
    GRID_COLS,
    GRID_ROWS,
    GAME_TITLE,
)
from .event_handler import CommandType, EventHandler, GameCommand
from .game_state import GameState
from .settings import GameSettings

from src.ai.game_pathfinder import GamePathfinder
from src.gameplay.delivery_task import DeliveryTask
from src.gameplay.order_generator import OrderGenerator
from src.gameplay.roundabout_geometry import build_roundabout_curve, curve_point
from src.maps.matrix_loader import MatrixLoader
from src.maps.tmx_loader import TmxMapLoader
from src.systems.stats_logger import StatsLogger, GameStatsRecord

from src.systems.asset_paths import (
    get_map_image_path,
    get_player_sprite_paths,
    get_npc_sprite_paths,
    get_icon_path,
    get_ui_asset_path,
    MAPS_DIR,
)
from src.systems.sprite_loader import SpriteLoader
from src.entities.directional_shipper import DirectionalShipper


class GameManager:
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

    def _asset_maps_dir(self) -> Path:
        return Path(MAPS_DIR)

    def _tmx_path(self, map_id: int) -> Path:
        from src.systems.asset_paths import PROJECT_ROOT
        
        candidates = [
            PROJECT_ROOT / "maps" / f"map{map_id}" / f"map{map_id}.tmx",
            PROJECT_ROOT / "maps" / f"map_{map_id}.tmx",
            self._asset_maps_dir() / f"map_{map_id}.tmx",
            self._asset_maps_dir() / f"map{map_id}.tmx",
        ]
        
        for c in candidates:
            if c.exists():
                return c
                
        return self._asset_maps_dir() / f"map_{map_id}.tmx"

    def _matrix_path(self, map_id: int) -> Path:
        return self._asset_maps_dir() / f"map_{map_id}_matrix.csv"

    def _allow_diagonal_movement(self) -> bool:
        return self.settings.selected_map_id == 2

    def _roundabout_center(self) -> tuple[float, float] | None:
        return (23.5, 16.5) if self.settings.selected_map_id == 2 else None

    def _roundabout_ring(self) -> tuple[Tuple[int, int], ...]:
        if self.settings.selected_map_id != 2:
            return ()

        return (
            (22, 14),
            (23, 14),
            (24, 14),
            (25, 15),
            (26, 16),
            (26, 17),
            (25, 18),
            (24, 19),
            (23, 19),
            (22, 18),
            (21, 17),
            (21, 16),
            (21, 15),
        )

    def _roundabout_connections(self) -> tuple[tuple[Tuple[int, int], Tuple[int, int]], ...]:
        if self.settings.selected_map_id != 2:
            return ()

        return (
            ((23, 13), (23, 14)),
            ((23, 19), (23, 20)),
            ((20, 15), (21, 16)),
            ((20, 18), (21, 17)),
            ((26, 16), (27, 15)),
            ((26, 17), (27, 18)),
        )

    def _load_ui_image(self, filename: str, size: tuple[int, int] | None = None):
        """
        Load ảnh giao diện menu từ assets/ui.
        Nếu thiếu file thì trả về None để game không bị lỗi.
        """
        try:
            path = get_ui_asset_path(filename)

            if not path:
                return None

            image = pygame.image.load(str(path)).convert_alpha()

            if size is not None:
                image = pygame.transform.smoothscale(image, size)

            return image

        except Exception as exc:
            print(f"[WARN] Không load được UI image {filename}: {exc}")
            return None

    def _load_ui_image(self, filename: str, size: tuple[int, int] | None = None):
        try:
            path = get_ui_asset_path(filename)

            if not path:
                return None

            image = pygame.image.load(str(path)).convert_alpha()

            if size is not None:
                image = pygame.transform.smoothscale(image, size)

            return image

        except Exception as exc:
            print(f"[WARN] Không load được UI image {filename}: {exc}")
            return None

    def _set_fullscreen_mode(self, enabled: bool) -> None:
        self.fullscreen_enabled = bool(enabled)

        if self.fullscreen_enabled:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.settings.get_window_size())

    def _draw_image_button(self, image, rect: pygame.Rect, fallback_text: str, bg_color: tuple[int, int, int]) -> None:
        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos)

        scale_rect = rect.copy()
        if hover:
            scale_rect.inflate_ip(8, 8)

        if image:
            img = pygame.transform.smoothscale(image, (scale_rect.width, scale_rect.height))
            self.screen.blit(img, scale_rect)
        else:
            color = tuple(min(255, c + 25) for c in bg_color) if hover else bg_color
            pygame.draw.rect(self.screen, color, scale_rect, border_radius=16)
            pygame.draw.rect(self.screen, (255, 255, 255), scale_rect, width=3, border_radius=16)
            self._draw_text(fallback_text, self.font_mid, (255, 255, 255), scale_rect.centerx, scale_rect.centery, center=True)

    def _draw_simulation_button(self, rect: pygame.Rect) -> None:
        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos)

        draw_rect = rect.copy()
        if hover:
            draw_rect.inflate_ip(8, 8)

        if self.ui_simulation_button:
            img = pygame.transform.smoothscale(self.ui_simulation_button, (draw_rect.width, draw_rect.height))
            self.screen.blit(img, draw_rect)
        else:
            color = (78, 220, 48) if hover else (55, 190, 70)
            pygame.draw.rect(self.screen, color, draw_rect, border_radius=18)
            pygame.draw.rect(self.screen, (20, 35, 24), draw_rect, width=5, border_radius=18)
            self._draw_text("AUTO", self.font_big, (255, 255, 255), draw_rect.centerx, draw_rect.centery, center=True)

    def _draw_small_round_button(self, rect: pygame.Rect, image, fallback_text: str, bg_color: tuple[int, int, int]) -> None:
        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos)

        draw_rect = rect.copy()
        if hover:
            draw_rect.inflate_ip(5, 5)

        if image:
            img = pygame.transform.smoothscale(image, (draw_rect.width, draw_rect.height))
            self.screen.blit(img, draw_rect)
        else:
            color = tuple(min(255, c + 30) for c in bg_color) if hover else bg_color
            pygame.draw.ellipse(self.screen, color, draw_rect)
            pygame.draw.ellipse(self.screen, (255, 255, 255), draw_rect, width=2)
            self._draw_text(fallback_text, self.font_small, (255, 255, 255), draw_rect.centerx, draw_rect.centery, center=True)

    def _load_map_preview_image(self, map_id: int, size: tuple[int, int]):
        """
        Load ảnh preview map cho menu chọn map.
        Ưu tiên các file:
        - assets/images/map_1_preview.png
        - assets/images/map1_preview.png
        - assets/images/map/map1.png
        - assets/maps/map_1.png
        """
        candidates = [
            Path("assets") / "images" / f"map_{map_id}_preview.png",
            Path("assets") / "images" / f"map{map_id}_preview.png",
            Path("assets") / "images" / "map" / f"map{map_id}.png",
            Path("assets") / "images" / "map" / f"map_{map_id}.png",
            Path("assets") / "maps" / f"map_{map_id}.png",
            Path("assets") / "maps" / f"map{map_id}.png",
        ]

        for path in candidates:
            if path.exists():
                try:
                    image = pygame.image.load(str(path)).convert_alpha()
                    return pygame.transform.smoothscale(image, size)
                except Exception:
                    pass

        return None

    def _draw_blue_sky_overlay(self) -> None:
        """
        Làm nền menu sáng hơn theo tông trời xanh.
        Nếu có Phongnen.png thì phủ lớp xanh lên trên để bớt tối.
        """
        sky = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        for y in range(SCREEN_HEIGHT):
            ratio = y / max(1, SCREEN_HEIGHT)
            r = int(45 + ratio * 25)
            g = int(165 + ratio * 25)
            b = int(245 - ratio * 20)
            pygame.draw.line(sky, (r, g, b, 120), (0, y), (SCREEN_WIDTH, y))

        self.screen.blit(sky, (0, 0))

    def _draw_moving_clouds(self) -> None:
        """
        Mây chuyển động nhẹ trong menu.
        Không cần file ảnh riêng.
        """
        offset = getattr(self, "menu_cloud_offset", 0.0)

        cloud_specs = [
            (120, 190, 1.00, 0),
            (510, 145, 0.85, 95),
            (880, 205, 1.15, 185),
            (1280, 155, 0.95, 270),
            (1520, 235, 0.75, 340),
        ]

        for base_x, y, scale, extra in cloud_specs:
            x = int((base_x + extra - offset) % (SCREEN_WIDTH + 360)) - 180
            self._draw_cloud(x, y, scale)

    def _draw_cloud(self, x: int, y: int, scale: float = 1.0) -> None:
        color = (245, 252, 255, 205)
        shadow = (180, 220, 245, 95)

        parts = [
            (0, 22, 58, 32),
            (44, 4, 68, 48),
            (102, 18, 80, 38),
            (162, 30, 60, 26),
        ]

        for px, py, w, h in parts:
            rect = pygame.Rect(
                x + int(px * scale),
                y + int(py * scale) + 5,
                int(w * scale),
                int(h * scale),
            )
            pygame.draw.ellipse(self.screen, shadow, rect)

        for px, py, w, h in parts:
            rect = pygame.Rect(
                x + int(px * scale),
                y + int(py * scale),
                int(w * scale),
                int(h * scale),
            )
            pygame.draw.ellipse(self.screen, color, rect)

    def _draw_map_selector(self) -> None:
        """
        Vẽ khu chọn map giống màn hình mẫu:
        MAP < 01 >
        [preview map]
        DIFFICULTY: EASY / MEDIUM / HARD
        """
        panel = pygame.Rect(SCREEN_WIDTH - 610, 245, 500, 320)
        self._draw_panel(panel, alpha=95, border=False)

        title_y = panel.y + 18
        self._draw_text("MAP", self.font_mid, (255, 255, 255), panel.x + 145, title_y, center=True)

        self.map_prev_button_rect = pygame.Rect(panel.x + 210, panel.y + 4, 54, 54)
        self.map_next_button_rect = pygame.Rect(panel.x + 362, panel.y + 4, 54, 54)

        self._draw_text_button(self.map_prev_button_rect, "‹", (65, 180, 85))
        self._draw_text_button(self.map_next_button_rect, "›", (65, 180, 85))

        map_num_text = f"{self.settings.selected_map_id:02d}"
        self._draw_text(map_num_text, self.font_mid, (255, 255, 255), panel.x + 316, title_y, center=True)

        preview_w = 430
        preview_h = 180
        self.map_preview_rect = pygame.Rect(panel.x + 35, panel.y + 72, preview_w, preview_h)

        preview = self._load_map_preview_image(self.settings.selected_map_id, (preview_w, preview_h))

        if preview:
            self.screen.blit(preview, self.map_preview_rect)
            pygame.draw.rect(self.screen, (255, 255, 255), self.map_preview_rect, width=4, border_radius=8)
        else:
            pygame.draw.rect(self.screen, (35, 45, 55), self.map_preview_rect, border_radius=8)
            pygame.draw.rect(self.screen, (255, 255, 255), self.map_preview_rect, width=4, border_radius=8)
            self._draw_text(
                f"MAP {self.settings.selected_map_id} PREVIEW",
                self.font_small,
                (255, 255, 255),
                self.map_preview_rect.centerx,
                self.map_preview_rect.centery,
                center=True,
            )

        difficulty = self._get_map_difficulty_text(self.settings.selected_map_id)
        self._draw_text("DIFFICULTY:", self.font_mid, (255, 255, 255), panel.x + 190, panel.y + 285, center=True)
        self._draw_text(difficulty, self.font_mid, (80, 255, 90), panel.x + 335, panel.y + 285, center=True)

    def _get_map_difficulty_text(self, map_id: int) -> str:
        if map_id == 1:
            return "EASY"
        if map_id == 2:
            return "MEDIUM"
        return "HARD"

    def _change_menu_map(self, delta: int) -> None:
        new_map = self.settings.selected_map_id + delta

        if new_map < 1:
            new_map = 3
        elif new_map > 3:
            new_map = 1

        self.settings.set_map(new_map)
        self._load_map_for_selected_map()
        self._reset_game()
        self.state = GameState.MENU

    def _draw_menu_top_buttons(self) -> None:
        # Hạ nút xuống rõ ràng để không bị thanh cửa sổ Windows che.
        self.sound_button_rect = pygame.Rect(SCREEN_WIDTH - 105, 82, 64, 64)
        self.menu_button_rect = pygame.Rect(SCREEN_WIDTH - 185, 82, 64, 64)

        sound_img = self.ui_sound_on if self.settings.sound_enabled else self.ui_sound_off
        sound_text = "ON" if self.settings.sound_enabled else "OFF"

        self._draw_small_round_button(
            self.menu_button_rect,
            self.ui_menu_button,
            "☰",
            (90, 130, 230),
        )

        self._draw_small_round_button(
            self.sound_button_rect,
            sound_img,
            sound_text,
            (65, 190, 95) if self.settings.sound_enabled else (180, 70, 70),
        )


    def _draw_menu_dropdown(self) -> None:
        if not self.menu_panel_open:
            return

        panel = pygame.Rect(SCREEN_WIDTH - 330, 98, 300, 245)
        self._draw_panel(panel, alpha=180, border=True)

        self._draw_text("MENU", self.font_mid, (255, 230, 110), panel.centerx, panel.y + 25, center=True)

        self.rules_button_rect = pygame.Rect(panel.x + 35, panel.y + 65, 230, 45)
        self.window_button_rect = pygame.Rect(panel.x + 35, panel.y + 122, 230, 45)
        self.exit_button_rect = pygame.Rect(panel.x + 35, panel.y + 179, 230, 45)

        self._draw_text_button(self.rules_button_rect, "1. Game Rules", (55, 120, 220))
        self._draw_text_button(self.window_button_rect, "2. Window Settings", (75, 145, 95))
        self._draw_text_button(self.exit_button_rect, "3. Exit Game", (180, 70, 70))

    def _draw_text_button(self, rect: pygame.Rect, text: str, bg_color: tuple[int, int, int]) -> None:
        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos)
        color = tuple(min(255, c + 25) for c in bg_color) if hover else bg_color
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, width=2, border_radius=10)
        self._draw_text(text, self.font_small, (255, 255, 255), rect.centerx, rect.centery, center=True)

    def _draw_rules_popup(self) -> None:
        if not self.rules_popup_open:
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 145))
        self.screen.blit(overlay, (0, 0))

        box = pygame.Rect(SCREEN_WIDTH // 2 - 420, SCREEN_HEIGHT // 2 - 275, 840, 550)
        self._draw_panel(box, alpha=225, border=True)

        self._draw_text("GAME RULES", self.font_big, (255, 230, 110), box.centerx, box.y + 48, center=True)

        rules = [
            "1. You are the main shipper in the city.",
            "2. Customers use Local Search to choose a store.",
            "3. Go to the Store to pick up the order, then deliver it to the House.",
            "4. Four NPC shippers compete against you using AI algorithms.",
            "5. NPCs use BFS, A*, Beam Search, and Q-Learning.",
            "6. Press SPACE to let Auto Player follow the selected algorithm.",
            "7. The first shipper to reach the target money wins.",
            "8. Results are saved to stats.csv for the report.",
        ]

        y = box.y + 115
        for line in rules:
            self._draw_text(line, self.font_small, (245, 245, 245), box.x + 55, y)
            y += 42

        self.close_popup_rect = pygame.Rect(box.centerx - 90, box.bottom - 75, 180, 48)
        self._draw_text_button(self.close_popup_rect, "Close", (70, 125, 220))

    def _draw_window_popup(self) -> None:
        if not self.window_popup_open:
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 145))
        self.screen.blit(overlay, (0, 0))

        box = pygame.Rect(SCREEN_WIDTH // 2 - 360, SCREEN_HEIGHT // 2 - 210, 720, 420)
        self._draw_panel(box, alpha=225, border=True)

        self._draw_text("WINDOW SETTINGS", self.font_big, (255, 230, 110), box.centerx, box.y + 55, center=True)

        status = "Fullscreen" if self.fullscreen_enabled else "Windowed"
        self._draw_text(f"Current mode: {status}", self.font_mid, (245, 245, 245), box.centerx, box.y + 125, center=True)

        self.windowed_button_rect = pygame.Rect(box.centerx - 260, box.y + 190, 220, 60)
        self.fullscreen_button_rect = pygame.Rect(box.centerx + 40, box.y + 190, 220, 60)
        self.close_popup_rect = pygame.Rect(box.centerx - 90, box.bottom - 80, 180, 48)

        self._draw_text_button(self.windowed_button_rect, "Windowed", (75, 145, 95))
        self._draw_text_button(self.fullscreen_button_rect, "Fullscreen", (55, 120, 220))
        self._draw_text_button(self.close_popup_rect, "Close", (180, 90, 70))

    def _handle_mouse_click(self, pos: tuple[int, int]) -> None:
        if self.state != GameState.MENU:
            return

        if self.rules_popup_open:
            if self.close_popup_rect and self.close_popup_rect.collidepoint(pos):
                self.rules_popup_open = False
            return

        if self.window_popup_open:
            if self.windowed_button_rect and self.windowed_button_rect.collidepoint(pos):
                self._set_fullscreen_mode(False)
            elif self.fullscreen_button_rect and self.fullscreen_button_rect.collidepoint(pos):
                self._set_fullscreen_mode(True)
            elif self.close_popup_rect and self.close_popup_rect.collidepoint(pos):
                self.window_popup_open = False
            return

        if self.sound_button_rect and self.sound_button_rect.collidepoint(pos):
            self.settings.toggle_sound()
            return

        if self.menu_button_rect and self.menu_button_rect.collidepoint(pos):
            self.menu_panel_open = not self.menu_panel_open
            return

        if hasattr(self, "map_prev_button_rect") and self.map_prev_button_rect and self.map_prev_button_rect.collidepoint(pos):
            self._change_menu_map(-1)
            return

        if hasattr(self, "map_next_button_rect") and self.map_next_button_rect and self.map_next_button_rect.collidepoint(pos):
            self._change_menu_map(1)
            return

        if self.menu_panel_open:
            if self.rules_button_rect and self.rules_button_rect.collidepoint(pos):
                self.rules_popup_open = True
                self.menu_panel_open = False
                return

            if self.window_button_rect and self.window_button_rect.collidepoint(pos):
                self.window_popup_open = True
                self.menu_panel_open = False
                return

            if self.exit_button_rect and self.exit_button_rect.collidepoint(pos):
                self.running = False
                return

        if self.simulation_button_rect and self.simulation_button_rect.collidepoint(pos):
            self._start_simulation_mode()
            return

        if self.play_button_rect and self.play_button_rect.collidepoint(pos):
            self._start_play_mode()
            return

    def _start_play_mode(self) -> None:
        self.simulation_mode = False
        self._reset_game()
        self.state = GameState.PLAYING

    def _start_simulation_mode(self) -> None:
        self.simulation_mode = True
        self._reset_game()
        self.auto_player_enabled = False
        self.player_path_hint = []
        self.state = GameState.SIMULATION

    def _load_assets(self) -> None:
        self.ui_background = self._load_ui_image("phongnen.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.ui_logo = self._load_ui_image("logo.png", (860, 300))
        right_path = get_player_sprite_paths().get("right")
        self.ui_shipper = None
        if right_path and right_path.exists():
            try:
                self.ui_shipper = pygame.image.load(str(right_path)).convert_alpha()
            except Exception:
                pass

        self.ui_play_button = self.sprite_loader.load_image(
            get_icon_path("play"),
            size=(310, 115),
            fallback_color=(55, 200, 70),
            fallback_text="PLAY",
        )
        self.ui_simulation_button = self._load_simulation_button_image()
        self.ui_sound_on = self.sprite_loader.load_image(
            get_icon_path("sound_on"),
            size=(58, 58),
            fallback_color=(65, 190, 95),
            fallback_text="ON",
        )
        self.ui_sound_off = self.sprite_loader.load_image(
            get_icon_path("sound_off"),
            size=(58, 58),
            fallback_color=(180, 70, 70),
            fallback_text="OFF",
        )
        self.ui_menu_button = self.sprite_loader.load_image(
            get_icon_path("menu"),
            size=(58, 58),
            fallback_color=(90, 130, 230),
            fallback_text="☰",
        )
        self.icons["store"] = self.sprite_loader.load_image(
            get_icon_path("store"),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=(240, 170, 60),
            fallback_text="S",
        )

        self.icons["house"] = self.sprite_loader.load_image(
            get_icon_path("house"),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=(80, 180, 100),
            fallback_text="H",
        )

        self.icons["money"] = self.sprite_loader.load_image(
            get_icon_path("money"),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=(240, 210, 70),
            fallback_text="$",
        )

        # Load location icons
        self.icons["location_player"] = self.sprite_loader.load_image(
            get_icon_path("location_shipper"),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=(55, 120, 220),
            fallback_text="LOC",
        )
        self.icons["location_npc1"] = self.sprite_loader.load_image(
            get_icon_path("location_npc1"),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=(220, 55, 55),
            fallback_text="LOC1",
        )
        self.icons["location_npc2"] = self.sprite_loader.load_image(
            get_icon_path("location_npc2"),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=(55, 220, 55),
            fallback_text="LOC2",
        )
        self.icons["location_npc3"] = self.sprite_loader.load_image(
            get_icon_path("location_npc3"),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=(220, 220, 55),
            fallback_text="LOC3",
        )

    def _load_simulation_button_image(self):
        path = get_icon_path("simulation")

        if not path:
            return self.sprite_loader.load_image(
                None,
                size=(310, 115),
                fallback_color=(55, 120, 220),
                fallback_text="SIM",
            )

        try:
            image = pygame.image.load(str(path)).convert_alpha()
            width, height = image.get_size()

            # Old exports were full-screen canvases. Current button art is already
            # a wide button, so only crop near-square/full-canvas images.
            if width >= 1000 and height >= 700 and width / max(1, height) < 2.2:
                crop = pygame.Rect(
                    int(width * 0.07),
                    int(height * 0.31),
                    int(width * 0.86),
                    int(height * 0.36),
                )
                image = image.subsurface(crop).copy()

            return image

        except Exception as exc:
            print(f"[WARN] Khong load duoc simulation button: {path} | {exc}")
            return self.sprite_loader.load_image(
                None,
                size=(310, 115),
                fallback_color=(55, 120, 220),
                fallback_text="SIM",
            )

    def _load_map_for_selected_map(self) -> None:
        map_id = self.settings.selected_map_id
        tmx_path = self._tmx_path(map_id)

        if tmx_path.exists():
            try:
                data = self.tmx_loader.load(tmx_path)

                self.grid_matrix = data.grid
                self.map_cols = data.width
                self.map_rows = data.height
                self.map_image = data.surface

                if data.pixel_width != SCREEN_WIDTH or data.pixel_height != SCREEN_HEIGHT:
                    self.map_image = pygame.transform.smoothscale(data.surface, (SCREEN_WIDTH, SCREEN_HEIGHT))

                # Nếu TMX không render được image layer thì ép load PNG map.
                if not self._surface_has_visible_pixels(self.map_image):
                    print("[WARN] TMX surface trống, fallback sang ảnh PNG map.")
                    self._load_png_map_background()

                self.store_positions = data.store_positions
                self.house_positions = data.house_positions
                self.trap_positions = set(data.trap_positions)
                self.player_spawn = data.player_spawn or (3, 3)
                self.npc_spawns = data.npc_spawns or []

                self.blocked_positions = self.tmx_loader.blocked_positions(self.grid_matrix)
                self.pathfinder = GamePathfinder(
                    self.map_cols,
                    self.map_rows,
                    self.blocked_positions,
                    allow_diagonal=self._allow_diagonal_movement(),
                    roundabout_ring=self._roundabout_ring(),
                    roundabout_connections=self._roundabout_connections(),
                )
                self.map_source = f"TMX: {tmx_path.name}"
                self._ensure_minimum_positions()
                return

            except Exception as exc:
                print(f"[WARN] Không load được TMX {tmx_path}: {exc}")
                print("[WARN] Fallback sang CSV matrix.")

        self._load_csv_matrix_fallback(map_id)

    def _load_csv_matrix_fallback(self, map_id: int) -> None:
        matrix_path = self._matrix_path(map_id)
        self.grid_matrix = self.matrix_loader.load_csv(matrix_path)

        if not matrix_path.exists():
            self.matrix_loader.save_csv(matrix_path, self.grid_matrix)

        self.map_cols = GRID_COLS
        self.map_rows = GRID_ROWS
        self.blocked_positions = self.matrix_loader.blocked_positions(self.grid_matrix)
        self.store_positions = self.matrix_loader.extract_positions(self.grid_matrix, MatrixLoader.STORE)
        self.house_positions = self.matrix_loader.extract_positions(self.grid_matrix, MatrixLoader.HOUSE)
        self.trap_positions = set(self.matrix_loader.extract_positions(self.grid_matrix, MatrixLoader.TRAP))
        self.player_spawn = (3, 3)
        self.npc_spawns = []

        safe = set(self.store_positions + self.house_positions) | self.trap_positions
        self.blocked_positions -= safe
        self.pathfinder = GamePathfinder(
            self.map_cols,
            self.map_rows,
            self.blocked_positions,
            allow_diagonal=self._allow_diagonal_movement(),
            roundabout_ring=self._roundabout_ring(),
            roundabout_connections=self._roundabout_connections(),
        )
        self.map_source = f"CSV: {matrix_path.name}"
        self._load_png_map_background()
        self._ensure_minimum_positions()

    def _surface_has_visible_pixels(self, surface: pygame.Surface | None) -> bool:
        """
        Kiểm tra TMX surface có pixel thật không.
        Nếu surface trống/transparent thì fallback sang ảnh PNG map.
        """
        if surface is None:
            return False

        try:
            rect = surface.get_bounding_rect()
            return rect.width > 0 and rect.height > 0
        except Exception:
            return False

    def _load_png_map_background(self) -> None:
        """
        Load ảnh nền thật của map từ PNG.
        Hàm này dùng để fallback khi TMX không render được image layer.
        """
        map_path = get_map_image_path(self.settings.selected_map_id)

        if map_path:
            print(f"[MAP] Load background image: {map_path}")
            self.map_image = self.sprite_loader.load_image(
                map_path,
                size=(SCREEN_WIDTH, SCREEN_HEIGHT),
                fallback_color=BACKGROUND_COLOR,
                fallback_text="MAP",
            )
        else:
            print(f"[WARN] Không tìm thấy ảnh nền map {self.settings.selected_map_id}.")
            print("[WARN] Hãy đặt ảnh vào một trong các đường dẫn:")
            print(f"       assets/images/map/map{self.settings.selected_map_id}.png")
            print(f"       assets/images/map/map_{self.settings.selected_map_id}.png")
            print(f"       assets/maps/map_{self.settings.selected_map_id}.png")


    def _ensure_minimum_positions(self) -> None:
        if not self.store_positions:
            self.store_positions = [
                self._nearest_walkable((6, 5)),
                self._nearest_walkable((18, 10)),
                self._nearest_walkable((31, 16)),
                self._nearest_walkable((40, 22)),
            ]

        if not self.house_positions:
            self.house_positions = [
                self._nearest_walkable((10, 22)),
                self._nearest_walkable((22, 27)),
                self._nearest_walkable((36, 27)),
                self._nearest_walkable((44, 10)),
            ]

        self.player_spawn = self._nearest_walkable(self.player_spawn)

    def _grid_to_screen(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        x, y = pos
        cell_w = SCREEN_WIDTH / max(1, self.map_cols)
        cell_h = SCREEN_HEIGHT / max(1, self.map_rows)
        return int(x * cell_w), int(y * cell_h)

    def _cell_size_screen(self) -> Tuple[int, int]:
        return int(SCREEN_WIDTH / max(1, self.map_cols)), int(SCREEN_HEIGHT / max(1, self.map_rows))

    def _nearest_walkable(self, start: Tuple[int, int]) -> Tuple[int, int]:
        if self.pathfinder.is_walkable(start):
            return start

        sx, sy = start

        for radius in range(1, max(self.map_cols, self.map_rows)):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    pos = (sx + dx, sy + dy)

                    if self.pathfinder.is_walkable(pos):
                        return pos

        return (0, 0)

    def _create_shipper_objects(self) -> None:
        player_sprites = self.sprite_loader.load_directional_set(
            get_player_sprite_paths(),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=PLAYER_COLOR,
            label="P",
        )

        self.player = DirectionalShipper("Player", self.player_spawn, player_sprites, TILE_SIZE)
        self.player.allow_diagonal = self._allow_diagonal_movement()
        self.player.configure_roundabout(
            self._roundabout_center(),
            self._roundabout_ring(),
            self._roundabout_connections(),
        )

        self.npc_shippers = []
        default_positions = [(8, 8), (14, 10), (20, 12)]
        algorithms = ["BFS", "ASTAR", "Q_LEARNING"]

        for i in range(3):
            npc_sprites = self.sprite_loader.load_directional_set(
                get_npc_sprite_paths(i + 1),
                size=(TILE_SIZE, TILE_SIZE),
                fallback_color=NPC_COLORS[i % len(NPC_COLORS)],
                label=str(i + 1),
            )

            raw_pos = self.npc_spawns[i] if i < len(self.npc_spawns) else default_positions[i]
            pos = self._nearest_walkable(raw_pos)

            npc = DirectionalShipper(f"NPC {i + 1}", pos, npc_sprites, TILE_SIZE)
            npc.algorithm = algorithms[i]
            npc.allow_diagonal = self._allow_diagonal_movement()
            npc.configure_roundabout(
                self._roundabout_center(),
                self._roundabout_ring(),
                self._roundabout_connections(),
            )
            self.npc_shippers.append(npc)

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(self.settings.fps) / 1000.0
            self._handle_commands()
            self._update(dt)
            self._draw()

        pygame.quit()

    def _handle_commands(self) -> None:
        for command in self.event_handler.handle_events():
            self._execute_command(command)

    def _execute_command(self, command: GameCommand) -> None:
        ctype = command.type

        if ctype == CommandType.QUIT:
            self.running = False

        elif ctype == CommandType.MOUSE_CLICK:
            self._handle_mouse_click(command.value)

        elif ctype == CommandType.START_GAME:
            if self.state in (GameState.MENU, GameState.GAME_OVER, GameState.WIN):
                self._start_play_mode()
            elif self.state == GameState.PAUSED:
                self.state = GameState.SIMULATION if self.simulation_mode else GameState.PLAYING

        elif ctype == CommandType.PAUSE_GAME:
            if self.state in (GameState.PLAYING, GameState.SIMULATION):
                self.state = GameState.PAUSED
            elif self.state == GameState.PAUSED:
                self.state = GameState.SIMULATION if self.simulation_mode else GameState.PLAYING
            elif self.state in (GameState.WIN, GameState.GAME_OVER):
                self.state = GameState.MENU

        elif ctype == CommandType.SELECT_MAP and command.value is not None:
            self.settings.set_map(int(command.value))
            self._load_map_for_selected_map()
            self._reset_game()

        elif ctype == CommandType.SELECT_ALGORITHM and command.value is not None:
            self.settings.set_algorithm(str(command.value))

            if not self.simulation_mode:
                self._refresh_player_path_hint()

        elif ctype == CommandType.TOGGLE_GRID:
            self.settings.toggle_grid()

        elif ctype == CommandType.TOGGLE_PATH_HINT:
            self.settings.toggle_path_hint()

        elif ctype == CommandType.TOGGLE_SOUND:
            self.settings.toggle_sound()

        elif ctype == CommandType.TOGGLE_AUTO_PLAYER:
            self.auto_player_enabled = not self.auto_player_enabled
            self._refresh_player_path_hint()

        elif ctype == CommandType.TOGGLE_HUD:
            self.hud_mode = (self.hud_mode + 1) % 3

        elif ctype == CommandType.MOVE_UP:
            self._request_player_step(0, -1)

        elif ctype == CommandType.MOVE_DOWN:
            self._request_player_step(0, 1)

        elif ctype == CommandType.MOVE_LEFT:
            self._request_player_step(-1, 0)

        elif ctype == CommandType.MOVE_RIGHT:
            self._request_player_step(1, 0)

        elif ctype == CommandType.STOP_MOVE:
            self.move_dir = (0, 0)

        elif ctype == CommandType.DEBUG_WIN:
            self._finish_game("Player")

        elif ctype == CommandType.DEBUG_LOSE:
            self._finish_game("NPC DEBUG")

    def _request_player_step(self, dx: int, dy: int) -> None:
        if self.state != GameState.PLAYING or self.auto_player_enabled:
            return

        if self._allow_diagonal_movement():
            self._poll_keyboard_movement()
            return

        self.move_dir = (int(dx), int(dy))
        self._move_player(allow_queue=True)

    def _poll_keyboard_movement(self) -> None:
        keys = pygame.key.get_pressed()

        dx, dy = 0, 0

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = 1

        if not self._allow_diagonal_movement() and dx != 0:
            dy = 0

        self.move_dir = (dx, dy)

        if self.player and (dx != 0 or dy != 0):
            self.player.set_direction_from_delta(dx, dy)

    def _update_smooth_entities(self, dt: float) -> None:
        if self.player:
            self.player.update_smooth(dt)

            if self.state == GameState.PLAYING:
                self._handle_player_task_at_current_pos()

        for npc in self.npc_shippers:
            npc.update_smooth(dt)

    def _move_player_auto(self) -> None:
        if not self.player:
            return

        if self.player_task is None or self.player_task.delivered:
            self.player_task = self._new_task("Player")

        base_pos = self._movement_base_pos(self.player)

        if (
            not self.player_path_hint
            or self.player_path_hint[-1] != self.player_task.target_pos
            or base_pos not in self.player_path_hint[:2]
        ):
            self._refresh_player_path_hint()

        while self.player_path_hint and self.player_path_hint[0] == base_pos:
            self.player_path_hint.pop(0)

        if not self.player_path_hint:
            self._refresh_player_path_hint()

        if not self.player_path_hint:
            return

        next_pos = self.player_path_hint[0]
        dx = next_pos[0] - base_pos[0]
        dy = next_pos[1] - base_pos[1]

        if not self.pathfinder.can_step(base_pos, next_pos):
            self._refresh_player_path_hint()
            return

        old_dir = self.move_dir
        self.move_dir = (dx, dy)
        self._move_player()
        self.move_dir = old_dir

        if self.player_path_hint and self.player_path_hint[0] == next_pos:
            self.player_path_hint.pop(0)

    def _update(self, dt: float) -> None:
        if self.state == GameState.MENU:
            self.menu_cloud_offset = (getattr(self, "menu_cloud_offset", 0.0) + dt * 28) % (SCREEN_WIDTH + 360)
            return

        if self.state not in (GameState.PLAYING, GameState.SIMULATION):
            return

        self._update_smooth_entities(dt)
        self.elapsed_time += dt

        if self.state == GameState.PLAYING and not self.auto_player_enabled:
            self._poll_keyboard_movement()

        self.move_timer += dt

        if self.state == GameState.PLAYING and self.move_timer >= 0.065:
            self.move_timer = 0.0

            if self.auto_player_enabled:
                self._move_player_auto()
            else:
                self._move_player(allow_queue=True)

        self.npc_timer += dt

        if self.npc_timer >= 0.065:
            self.npc_timer = 0.0
            self._update_npcs()

        self.order_timer += dt

        if self.state == GameState.PLAYING and self.order_timer >= 0.8:
            self.order_timer = 0.0
            self._refresh_player_path_hint()

        if self.state == GameState.SIMULATION:
            return

        if self.player and self.player.money >= self.settings.target_revenue:
            self._finish_game("Player")
            return

        for npc in self.npc_shippers:
            if npc.money >= self.settings.target_revenue:
                self._finish_game(npc.name)
                return

    def _finish_game(self, winner_name: str) -> None:
        if self.result_logged:
            return

        self.winner_name = winner_name
        self.state = GameState.WIN if winner_name == "Player" else GameState.GAME_OVER
        self._log_result()
        self.result_logged = True

    def _log_result(self) -> None:
        player_money = self.player.money if self.player else 0
        player_orders = self.player.orders if self.player else 0

        record = GameStatsRecord(
            timestamp=StatsLogger.now_text(),
            map_id=self.settings.selected_map_id,
            map_source=self.map_source,
            winner=self.winner_name,
            player_win=(self.winner_name == "Player"),
            elapsed_time=round(self.elapsed_time, 2),
            target_revenue=self.settings.target_revenue,
            player_money=player_money,
            player_orders=player_orders,
            player_algorithm=self.settings.selected_algorithm,
            player_expanded_nodes=self.player_path_expanded,
        )

        for index, npc in enumerate(self.npc_shippers, start=1):
            setattr(record, f"npc_{index}_money", npc.money)
            setattr(record, f"npc_{index}_orders", npc.orders)
            setattr(record, f"npc_{index}_algorithm", getattr(npc, "algorithm", ""))
            setattr(record, f"npc_{index}_expanded_nodes", self.npc_expanded.get(npc.name, 0))

        self.stats_logger.write_record(record)

    def _new_task(self, holder_name: Optional[str] = None) -> DeliveryTask:
        fallback_task = None

        for _ in range(40):
            task = self.order_generator.create_order(
                stores=self.store_positions,
                houses=self.house_positions,
                pathfinder=self.pathfinder,
                holder_name=holder_name,
            )

            if fallback_task is None:
                fallback_task = task

            if self._task_is_reachable(task, holder_name):
                return task

        reachable_task = self._first_reachable_task(holder_name)
        return reachable_task or fallback_task

    def _holder_grid_pos(self, holder_name: Optional[str]) -> Tuple[int, int] | None:
        if holder_name == "Player" and self.player:
            return self._movement_base_pos(self.player)

        for npc in self.npc_shippers:
            if npc.name == holder_name:
                return self._movement_base_pos(npc)

        return None

    def _task_is_reachable(self, task: DeliveryTask, holder_name: Optional[str]) -> bool:
        start = self._holder_grid_pos(holder_name)

        if start is not None:
            to_store = self.pathfinder.find_path(start, task.store_pos, "ASTAR")

            if not to_store.success:
                return False

        to_house = self.pathfinder.find_path(task.store_pos, task.house_pos, "ASTAR")
        return bool(to_house.success)

    def _first_reachable_task(self, holder_name: Optional[str]) -> DeliveryTask | None:
        start = self._holder_grid_pos(holder_name)

        for store in self.store_positions:
            if start is not None and not self.pathfinder.find_path(start, store, "ASTAR").success:
                continue

            for house in self.house_positions:
                result = self.pathfinder.find_path(store, house, "ASTAR")

                if result.success:
                    self.order_generator.last_result = None
                    return DeliveryTask(
                        store_pos=store,
                        house_pos=house,
                        reward=90,
                        holder_name=holder_name,
                    )

        return None

    def _movement_base_pos(self, shipper) -> Tuple[int, int]:
        if getattr(shipper, "is_moving", False):
            return tuple(getattr(shipper, "target_grid_pos", shipper.grid_pos))

        return tuple(shipper.grid_pos)

    def _try_move_shipper_delta(self, shipper, dx: int, dy: int, allow_queue: bool = True) -> bool:
        dx = int(dx)
        dy = int(dy)

        allow_diagonal = self._allow_diagonal_movement()

        if allow_diagonal:
            if max(abs(dx), abs(dy)) != 1 or (dx == 0 and dy == 0):
                return False
        elif abs(dx) + abs(dy) != 1:
            return False

        if not allow_queue and getattr(shipper, "is_moving", False):
            return False

        base_x, base_y = self._movement_base_pos(shipper)
        next_pos = (
            max(0, min(self.map_cols - 1, base_x + dx)),
            max(0, min(self.map_rows - 1, base_y + dy)),
        )

        if next_pos == (base_x, base_y):
            return True

        if not self.pathfinder.can_step((base_x, base_y), next_pos):
            return False

        shipper.allow_diagonal = allow_diagonal
        return bool(shipper.move_grid(dx, dy, self.map_cols, self.map_rows, min_y=0, allow_diagonal=allow_diagonal))

    def _handle_player_task_at_current_pos(self) -> None:
        if not self.player:
            return

        if self.player_task is None or self.player_task.delivered:
            self.player_task = self._new_task("Player")

        self.player_task.assign_to("Player")

        picked = self.player_task.try_pickup("Player", self.player.grid_pos)
        delivered = self.player_task.try_deliver("Player", self.player.grid_pos)

        if picked:
            self._refresh_player_path_hint()

        if delivered:
            self.player.money += self.player_task.reward
            self.player.orders += 1
            self.player_task = self._new_task("Player")
            self._refresh_player_path_hint()

        if self.player.grid_pos in self.trap_positions:
            if self._player_last_trap_penalty_pos == self.player.grid_pos:
                return

            self.player.money = max(0, self.player.money - 15)
            self._player_last_trap_penalty_pos = self.player.grid_pos
        else:
            self._player_last_trap_penalty_pos = None

    def _move_player(self, allow_queue: bool = True) -> None:
        if not self.player:
            return

        dx, dy = self.move_dir

        if dx == 0 and dy == 0:
            return

        if not self._try_move_shipper_delta(self.player, dx, dy, allow_queue=allow_queue):
            return

        self._handle_player_task_at_current_pos()

    def _update_npcs(self) -> None:
        for npc in self.npc_shippers:
            if npc.name not in self.npc_tasks or self.npc_tasks[npc.name].delivered:
                self.npc_tasks[npc.name] = self._new_task(npc.name)
                self.npc_paths[npc.name] = []

            task = self.npc_tasks[npc.name]
            task.assign_to(npc.name)

            if not self.npc_paths.get(npc.name):
                result = self.pathfinder.find_path(self._movement_base_pos(npc), task.target_pos, npc.algorithm)
                self.npc_paths[npc.name] = result.path[1:] if result.success and len(result.path) > 1 else []
                self.npc_expanded[npc.name] = result.expanded_nodes

            path = self.npc_paths.get(npc.name, [])

            if path and getattr(npc, "queued_grid_pos", None) is None:
                base_pos = self._movement_base_pos(npc)

                while path and path[0] == base_pos:
                    path.pop(0)

                if path:
                    next_pos = path[0]
                    dx = next_pos[0] - base_pos[0]
                    dy = next_pos[1] - base_pos[1]

                    if self._try_move_shipper_delta(npc, dx, dy):
                        path.pop(0)
                    else:
                        self.npc_paths[npc.name] = []

            picked = task.try_pickup(npc.name, npc.grid_pos)
            delivered = task.try_deliver(npc.name, npc.grid_pos)

            if picked:
                self.npc_paths[npc.name] = []

            if delivered:
                npc.money += task.reward
                npc.orders += 1
                self.npc_tasks[npc.name] = self._new_task(npc.name)
                self.npc_paths[npc.name] = []

            if npc.grid_pos in self.trap_positions:
                npc.money = max(0, npc.money - 10)

    def _refresh_player_path_hint(self) -> None:
        if not self.player:
            return

        if self.player_task is None or self.player_task.delivered:
            self.player_task = self._new_task("Player")

        result = self.pathfinder.find_path(
            self._movement_base_pos(self.player),
            self.player_task.target_pos,
            self.settings.selected_algorithm,
        )

        self.player_path_hint = result.path
        self.player_path_expanded = result.expanded_nodes

    def _draw(self) -> None:
        self.screen.fill(BACKGROUND_COLOR)

        if self.state == GameState.MENU:
            self._draw_menu()

        elif self.state in (GameState.PLAYING, GameState.SIMULATION):
            self._draw_game()

        elif self.state == GameState.PAUSED:
            self._draw_game()
            self._draw_pause()

        elif self.state == GameState.WIN:
            self._draw_result("YOU WIN!", "You reached the target money before the NPCs.")

        elif self.state == GameState.GAME_OVER:
            self._draw_result("GAME OVER", f"{self.winner_name} reached the target money before you.")

        pygame.display.flip()

    def _draw_menu(self) -> None:
        """
        Menu chính chỉnh theo mẫu:
        - Trời xanh
        - Mây bay nhẹ
        - Logo lớn hơn và hạ xuống
        - Shipper lớn hơn nút Play
        - Nút menu/loa hạ xuống không bị khuất
        """
        # Nền gốc
        if self.ui_background:
            self.screen.blit(self.ui_background, (0, 0))
        else:
            self.screen.fill((60, 180, 245))

        # Phủ xanh để nền tối thành bầu trời xanh hơn
        self._draw_blue_sky_overlay()

        # Mây chuyển động
        self._draw_moving_clouds()

        # Nút menu + âm thanh góc phải, hạ xuống
        self._draw_menu_top_buttons()

        # Logo / tên game lớn và hạ xuống
        if self.ui_logo:
            logo_w = 860
            logo_h = 300
            logo = pygame.transform.smoothscale(self.ui_logo, (logo_w, logo_h))
            logo_rect = logo.get_rect()
            logo_rect.centerx = SCREEN_WIDTH // 2
            logo_rect.y = 15
            self.screen.blit(logo, logo_rect)
        else:
            self._draw_text(
                "SUPER DELIVERY GAME",
                self.font_big,
                (255, 230, 80),
                SCREEN_WIDTH // 2,
                145,
                center=True,
            )

        # LEVEL box bên trái
        level_x = 210
        level_y = 305
        self._draw_text("LEVEL", self.font_mid, (255, 255, 255), level_x + 80, level_y, center=True)
        level_box = pygame.Rect(level_x + 28, level_y + 45, 120, 78)
        self._draw_panel(level_box, alpha=185, border=True)
        self._draw_text(f"{self.settings.selected_map_id:02d}", self.font_big, (255, 255, 255), level_box.centerx, level_box.centery - 4, center=True)

        # Map selector + preview
        self._draw_map_selector()

        # Nhân vật chính thật to, lớn hơn nút Play
        if self.ui_shipper:
            img_w, img_h = self.ui_shipper.get_size()
            target_h = 430
            target_w = int(img_w * (target_h / img_h)) if img_h > 0 else 620
            shipper = pygame.transform.smoothscale(self.ui_shipper, (target_w, target_h))
            shipper_rect = shipper.get_rect()
            shipper_rect.left = 65
            shipper_rect.bottom = SCREEN_HEIGHT - 30
            self.screen.blit(shipper, shipper_rect)

        # Nút Play lớn nhưng nhỏ hơn shipper
        button_w = 410
        simulation_h = 138
        self.simulation_button_rect = pygame.Rect(0, 0, button_w, simulation_h)
        self.simulation_button_rect.right = SCREEN_WIDTH - 145
        self.simulation_button_rect.bottom = SCREEN_HEIGHT - 246
        self._draw_simulation_button(self.simulation_button_rect)

        play_w = button_w
        play_h = 132
        self.play_button_rect = pygame.Rect(0, 0, play_w, play_h)
        self.play_button_rect.right = SCREEN_WIDTH - 145
        self.play_button_rect.bottom = SCREEN_HEIGHT - 78
        self._draw_image_button(self.ui_play_button, self.play_button_rect, "PLAY", (55, 200, 70))

        # Menu dropdown và popup
        self._draw_menu_dropdown()
        self._draw_rules_popup()
        self._draw_window_popup()


    def _draw_game(self) -> None:
        if self.map_image:
            self.screen.blit(self.map_image, (0, 0))
        else:
            self.screen.fill(BACKGROUND_COLOR)
            self._draw_matrix_overlay()

        self._draw_static_icons()

        if self.simulation_mode or self.settings.show_path_hint:
            self._draw_paths()

        if not self.simulation_mode and self.player:
            self._draw_shipper_scaled(self.player)

        for npc in self.npc_shippers:
            self._draw_shipper_scaled(npc)

        if self.settings.show_grid:
            self._draw_grid()

        # Draw bouncing location pins for active tasks
        self._draw_active_locations()

        if self.simulation_mode:
            self._draw_simulation_hud()
        else:
            self._draw_hud_clean()

    def _draw_active_locations(self) -> None:
        import math
        import pygame

        time_ticks = pygame.time.get_ticks()
        bounce_offset = abs(math.sin(time_ticks * 0.005)) * 10  # Jump height up to 10 pixels

        # Draw for Player
        if not self.simulation_mode and getattr(self, 'player_task', None) and not self.player_task.delivered:
            self._draw_bouncing_location("location_player", self.player_task.target_pos, bounce_offset)

        # Draw for NPCs
        if hasattr(self, 'npc_tasks'):
            for i, npc in enumerate(self.npc_shippers):
                task = self.npc_tasks.get(npc.name)
                if task and not task.delivered:
                    icon_name = f"location_npc{i + 1}"
                    if icon_name not in self.icons:
                        icon_name = "location_npc1" # Fallback
                    self._draw_bouncing_location(icon_name, task.target_pos, bounce_offset)

    def _draw_bouncing_location(self, icon_name: str, grid_pos: Tuple[int, int], bounce_offset: float) -> None:
        icon = self.icons.get(icon_name)
        if not icon:
            return

        x, y = self._grid_to_screen(grid_pos)

        # Center horizontally, and offset vertically by the bounce amount
        # We also offset a bit up so the pin's bottom points to the center of the cell
        cell_w, cell_h = self._cell_size_screen()
        icon_w, icon_h = icon.get_size()

        draw_x = x + (cell_w - icon_w) // 2
        draw_y = y + (cell_h - icon_h) // 2 - int(bounce_offset) - (icon_h // 4)

        self.screen.blit(icon, (draw_x, draw_y))

    def _draw_shipper_scaled(self, shipper) -> None:
        sprite = shipper.sprites.get(shipper.direction) or shipper.sprites.get("idle")
        cell_w, cell_h = self._cell_size_screen()

        if hasattr(shipper, "render_pos"):
            rx, ry = shipper.render_pos
            x = int(rx * cell_w)
            y = int(ry * cell_h)
        else:
            x, y = self._grid_to_screen(shipper.grid_pos)

        if sprite.get_width() != cell_w or sprite.get_height() != cell_h:
            sprite = pygame.transform.smoothscale(sprite, (cell_w, cell_h))

        self.screen.blit(sprite, (x, y))

    def _draw_matrix_overlay(self) -> None:
        cell_w, cell_h = self._cell_size_screen()

        for y, row in enumerate(self.grid_matrix):
            for x, code in enumerate(row):
                rect = (x * cell_w, y * cell_h, cell_w, cell_h)

                if code == MatrixLoader.BLOCK:
                    pygame.draw.rect(self.screen, (45, 45, 52), rect)
                elif code == MatrixLoader.WATER:
                    pygame.draw.rect(self.screen, (40, 100, 170), rect)
                elif code == MatrixLoader.TRAP:
                    pygame.draw.rect(self.screen, (150, 75, 35), rect)

    def _draw_static_icons(self) -> None:
        # User requested to remove S and H icons from the map, replaced by active bouncing locations
        pass

    def _draw_target_marker(self, grid_pos: Tuple[int, int]) -> None:
        x, y = self._grid_to_screen(grid_pos)
        cell_w, cell_h = self._cell_size_screen()
        pygame.draw.rect(self.screen, (255, 235, 60), (x + 2, y + 2, cell_w - 4, cell_h - 4), width=3, border_radius=6)

    def _draw_paths(self) -> None:
        if not self.simulation_mode:
            self._draw_path(self.player_path_hint, (255, 245, 50), radius=4, width=4, glow=True)
            return

        colors = [(255, 80, 80), (60, 235, 125), (255, 180, 55), (165, 125, 255)]

        for i, npc in enumerate(self.npc_shippers):
            path = [self._movement_base_pos(npc)] + list(self.npc_paths.get(npc.name, []))
            self._draw_path(path, colors[i % len(colors)], radius=5, width=5, glow=True)
            self._draw_algorithm_label(npc, colors[i % len(colors)])

    def _draw_path(
        self,
        path: List[Tuple[int, int]],
        color: Tuple[int, int, int],
        radius: int = 3,
        width: int = 3,
        glow: bool = False,
    ) -> None:
        if not path:
            return

        cell_w, cell_h = self._cell_size_screen()
        anchor_points = []

        for gx, gy in path:
            x, y = self._grid_to_screen((gx, gy))
            anchor_points.append((x + cell_w // 2, y + cell_h // 2))

        points = self._path_render_points(path, cell_w, cell_h)

        if len(points) >= 2:
            if glow:
                pygame.draw.lines(self.screen, (20, 20, 24), False, points, width + 5)
                glow_color = tuple(min(255, int(c * 0.65 + 70)) for c in color)
                pygame.draw.lines(self.screen, glow_color, False, points, width + 2)

            pygame.draw.lines(self.screen, color, False, points, width)

        for point in anchor_points:
            if glow:
                pygame.draw.circle(self.screen, (20, 20, 24), point, radius + 3)
            pygame.draw.circle(self.screen, color, point, radius)

    def _path_render_points(
        self,
        path: List[Tuple[int, int]],
        cell_w: int,
        cell_h: int,
    ) -> list[tuple[int, int]]:
        if not path:
            return []

        def screen_center(grid_x: float, grid_y: float) -> tuple[int, int]:
            return (
                int((grid_x + 0.5) * cell_w),
                int((grid_y + 0.5) * cell_h),
            )

        output = [screen_center(*path[0])]
        center = self._roundabout_center()

        for start, end in zip(path, path[1:]):
            curve = build_roundabout_curve(
                start,
                end,
                center,
                self._roundabout_ring(),
                self._roundabout_connections(),
            )

            if curve is None:
                output.append(screen_center(*end))
                continue

            for sample in range(1, 7):
                output.append(screen_center(*curve_point(curve, sample / 6.0)))

        return output

    def _draw_algorithm_label(self, npc, color: Tuple[int, int, int]) -> None:
        x, y = self._grid_to_screen(npc.grid_pos)
        cell_w, cell_h = self._cell_size_screen()
        label = str(getattr(npc, "algorithm", npc.name))
        text = self.font_tiny.render(label, True, (255, 255, 255))
        pad_x, pad_y = 6, 3
        rect = pygame.Rect(x, y - 22, text.get_width() + pad_x * 2, text.get_height() + pad_y * 2)
        rect.centerx = x + cell_w // 2

        panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        panel.fill((10, 14, 22, 165))
        self.screen.blit(panel, (rect.x, rect.y))
        pygame.draw.rect(self.screen, color, rect, width=2, border_radius=5)
        self.screen.blit(text, (rect.x + pad_x, rect.y + pad_y))

    def _draw_icon(self, icon_name: str, grid_pos: Tuple[int, int]) -> None:
        x, y = self._grid_to_screen(grid_pos)
        cell_w, cell_h = self._cell_size_screen()
        icon = self.icons.get(icon_name)

        if icon:
            if icon.get_width() != cell_w or icon.get_height() != cell_h:
                icon = pygame.transform.smoothscale(icon, (cell_w, cell_h))

            self.screen.blit(icon, (x, y))

        else:
            color = {
                "store": (240, 170, 60),
                "house": (80, 180, 100),
                "money": (240, 210, 70),
            }.get(icon_name, (255, 255, 255))

            pygame.draw.rect(self.screen, color, (x + 4, y + 4, cell_w - 8, cell_h - 8), border_radius=6)

    def _draw_grid(self) -> None:
        cell_w, cell_h = self._cell_size_screen()

        for x in range(0, SCREEN_WIDTH + 1, max(1, cell_w)):
            pygame.draw.line(self.screen, GRID_LINE_COLOR, (x, 0), (x, SCREEN_HEIGHT), 1)

        for y in range(0, SCREEN_HEIGHT + 1, max(1, cell_h)):
            pygame.draw.line(self.screen, GRID_LINE_COLOR, (0, y), (SCREEN_WIDTH, y), 1)

    def _draw_simulation_hud(self) -> None:
        top_bar = pygame.Rect(0, 0, SCREEN_WIDTH, 34)
        self._draw_panel(top_bar, alpha=115, border=False)
        text = f"SIMULATION | Map {self.settings.selected_map_id} | Time {self.elapsed_time:05.1f}s | ESC Pause | P Path | G Grid"
        self._draw_text(text, self.font_tiny, (255, 255, 255), 10, 9)

        board_w = 385
        row_h = 27
        board_h = 42 + len(self.npc_shippers) * row_h
        board = pygame.Rect(SCREEN_WIDTH - board_w - 12, 48, board_w, board_h)
        self._draw_panel(board, alpha=135, border=True)
        self._draw_text("ALGORITHM GROUPS", self.font_small, (255, 230, 110), board.x + 12, board.y + 10)

        colors = [(255, 80, 80), (60, 235, 125), (255, 180, 55), (165, 125, 255)]
        y = board.y + 38
        for i, npc in enumerate(self.npc_shippers):
            color = colors[i % len(colors)]
            pygame.draw.circle(self.screen, color, (board.x + 18, y + 8), 6)
            task = self.npc_tasks.get(npc.name)
            target = task.target_pos if task else "-"
            label = f"{npc.name}: {getattr(npc, 'algorithm', '')} -> {target}"
            self._draw_text(label, self.font_tiny, (245, 245, 245), board.x + 34, y)
            y += row_h

    def _draw_hud_clean(self) -> None:
        """
        HUD mới:
        - Mặc định gọn, không che nhiều map.
        - H để đổi chế độ:
          hud_mode = 1: gọn
          hud_mode = 2: đầy đủ
          hud_mode = 0: ẩn
        """
        hud_mode = getattr(self, "hud_mode", 1)

        if hud_mode == 0:
            return

        money = self.player.money if self.player else 0
        orders = self.player.orders if self.player else 0
        mode = "AUTO" if self.auto_player_enabled else "MANUAL"

        task_short = "No task"
        task_detail = []

        if self.player_task:
            status = "STORE" if not self.player_task.picked_up else "HOUSE"
            target = self.player_task.target_pos
            local_cost = getattr(self.order_generator.last_result, "cost", 0)

            task_short = (
                f"Task: {status} {target} | "
                f"${self.player_task.reward} | "
                f"LS {local_cost} | "
                f"Nodes {self.player_path_expanded}"
            )

            task_detail = [
                f"Status: {'GO TO STORE' if not self.player_task.picked_up else 'DELIVER TO HOUSE'}",
                f"Target grid: {target}",
                f"Store -> House: {self.player_task.store_pos} -> {self.player_task.house_pos}",
                f"Local Search cost: {local_cost}",
                f"Reward: ${self.player_task.reward}",
                f"Expanded nodes: {self.player_path_expanded}",
            ]

        # =========================
        # MODE 1: HUD gọn mặc định
        # =========================
        if hud_mode == 1:
            top_bar = pygame.Rect(0, 0, SCREEN_WIDTH, 32)
            self._draw_panel(top_bar, alpha=105, border=False)

            top_text = (
                f"Time {self.elapsed_time:05.1f}s | "
                f"Money ${money}/{self.settings.target_revenue} | "
                f"Orders {orders} | "
                f"AI {self.settings.selected_algorithm} | "
                f"{mode} | "
                f"{task_short}"
            )

            self._draw_text(top_text, self.font_tiny, (255, 255, 255), 10, 8)

            bottom_bar = pygame.Rect(0, SCREEN_HEIGHT - 24, SCREEN_WIDTH, 24)
            self._draw_panel(bottom_bar, alpha=85, border=False)

            help_text = "H HUD | WASD Move | SPACE Auto | F1 BFS | F2 A* | F3 Beam | F4 Partial | F5 Q-Learning | P Path | G Grid | ESC Pause"
            self._draw_text(help_text, self.font_tiny, (255, 255, 255), 10, SCREEN_HEIGHT - 20)

            return

        # =========================
        # MODE 2: HUD đầy đủ nhưng đẩy xuống dưới
        # =========================
        top_bar = pygame.Rect(0, 0, SCREEN_WIDTH, 34)
        self._draw_panel(top_bar, alpha=120, border=False)

        top_text = (
            f"Time {self.elapsed_time:05.1f}s | "
            f"Money ${money}/{self.settings.target_revenue} | "
            f"Orders {orders} | "
            f"AI {self.settings.selected_algorithm} | "
            f"Mode {mode} | "
            f"Map {self.settings.selected_map_id}"
        )
        self._draw_text(top_text, self.font_tiny, (255, 255, 255), 10, 9)

        # Mission panel xuống góc dưới trái để không che đường trên
        mission_box = pygame.Rect(12, SCREEN_HEIGHT - 190, 430, 148)
        self._draw_panel(mission_box, alpha=125, border=True)
        self._draw_text("PLAYER MISSION", self.font_small, (255, 230, 110), 24, mission_box.y + 10)

        y = mission_box.y + 38
        for line in task_detail if task_detail else ["No active task"]:
            self._draw_text(line, self.font_tiny, (245, 245, 245), 24, y)
            y += 19

        # NPC panel xuống góc dưới phải
        board_w = 405
        board_h = 148
        board = pygame.Rect(SCREEN_WIDTH - board_w - 12, SCREEN_HEIGHT - 190, board_w, board_h)
        self._draw_panel(board, alpha=125, border=True)
        self._draw_text("NPC SCOREBOARD", self.font_small, (255, 230, 110), board.x + 12, board.y + 10)

        y = board.y + 38
        for npc in self.npc_shippers:
            task = self.npc_tasks.get(npc.name)
            action = ""

            if task:
                action = "Pickup" if not task.picked_up else "Deliver"

            line = f"{npc.name}: ${npc.money:03d} | {npc.algorithm:<10} | {action:<7} | Nodes {self.npc_expanded.get(npc.name, 0)}"
            self._draw_text(line, self.font_tiny, (245, 245, 245), board.x + 12, y)
            y += 24

        help_bar = pygame.Rect(0, SCREEN_HEIGHT - 28, SCREEN_WIDTH, 28)
        self._draw_panel(help_bar, alpha=95, border=False)
        help_text = "H HUD | WASD move | SPACE auto-player | F1-F5 algorithms | P path | G grid | ESC pause"
        self._draw_text(help_text, self.font_tiny, (255, 255, 255), 10, SCREEN_HEIGHT - 22)


    def _draw_panel(self, rect: pygame.Rect, alpha: int = 150, border: bool = True) -> None:
        panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        panel.fill((10, 14, 22, alpha))
        self.screen.blit(panel, (rect.x, rect.y))

        if border:
            pygame.draw.rect(self.screen, (255, 255, 255), rect, width=1, border_radius=6)

    def _draw_pause(self) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        self._draw_text("PAUSED", self.font_big, (255, 255, 255), SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40, center=True)
        self._draw_text("ESC or ENTER to continue", self.font_mid, (255, 255, 255), SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20, center=True)

    def _draw_result(self, title: str, subtitle: str) -> None:
        self.screen.fill((22, 29, 39))
        self._draw_text(title, self.font_big, (255, 230, 120), SCREEN_WIDTH // 2, 180, center=True)
        self._draw_text(subtitle, self.font_mid, (255, 255, 255), SCREEN_WIDTH // 2, 245, center=True)

        money = self.player.money if self.player else 0
        orders = self.player.orders if self.player else 0

        box = pygame.Rect(SCREEN_WIDTH // 2 - 300, 300, 600, 220)
        self._draw_panel(box, alpha=170, border=True)

        lines = [
            f"Winner: {self.winner_name}",
            f"Time: {self.elapsed_time:.1f}s",
            f"Player money: ${money}/{self.settings.target_revenue}",
            f"Player orders: {orders}",
            "Result saved to stats.csv",
            "ENTER: Play again | ESC: Back to menu",
        ]

        y = 325

        for line in lines:
            self._draw_text(line, self.font_small, (245, 245, 245), SCREEN_WIDTH // 2, y, center=True)
            y += 32

    def _draw_text(self, text: str, font: pygame.font.Font, color: Tuple[int, int, int], x: int, y: int, center: bool = False) -> None:
        surface = font.render(str(text), True, color)
        rect = surface.get_rect()

        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)

        self.screen.blit(surface, rect)

    def _reset_game(self) -> None:
        self.elapsed_time = 0.0
        self.result_logged = False
        self.winner_name = ""
        self.auto_player_enabled = False
        self.move_dir = (0, 0)
        self._player_last_trap_penalty_pos = None

        self._create_shipper_objects()

        self.player_task = None if self.simulation_mode else self._new_task("Player")
        self.npc_tasks = {}
        self.npc_paths = {}
        self.npc_expanded = {}

        if self.player:
            self.player.money = 0
            self.player.orders = 0
            self.player.set_grid_pos(self._nearest_walkable(self.player_spawn))

        for npc in self.npc_shippers:
            npc.money = 0
            npc.orders = 0

        if self.simulation_mode:
            self.player_path_hint = []
            self.player_path_expanded = 0
        else:
            self._refresh_player_path_hint()



# =========================================================
# LETTERBOX DISPLAY PATCH
# Giữ world 1536x1024 nhưng hiển thị fit trong cửa sổ 1408x736.
# Không crop map, không phóng to map quá màn hình.
# =========================================================

try:
    _SUPER_DELIVERY_ORIGINAL_DRAW = GameManager._draw
except Exception:
    _SUPER_DELIVERY_ORIGINAL_DRAW = None


def _super_delivery_present_letterbox(self, world_surface):
    display = pygame.display.get_surface()
    if display is None:
        return

    win_w, win_h = display.get_size()
    world_w, world_h = world_surface.get_size()

    scale = min(win_w / world_w, win_h / world_h)
    scaled_w = max(1, int(world_w * scale))
    scaled_h = max(1, int(world_h * scale))

    offset_x = (win_w - scaled_w) // 2
    offset_y = (win_h - scaled_h) // 2

    self._viewport_scale = scale
    self._viewport_offset = (offset_x, offset_y)

    display.fill((0, 0, 0))
    scaled = pygame.transform.smoothscale(world_surface, (scaled_w, scaled_h))
    display.blit(scaled, (offset_x, offset_y))
    pygame.display.flip()


def _super_delivery_draw_letterboxed(self):
    world_size = (1536, 1024)

    if not hasattr(self, "_letterbox_world_surface"):
        self._letterbox_world_surface = pygame.Surface(world_size).convert()

    display_screen = self.screen
    self.screen = self._letterbox_world_surface
    self._letterbox_world_surface.fill((0, 0, 0))

    if _SUPER_DELIVERY_ORIGINAL_DRAW is not None:
        _SUPER_DELIVERY_ORIGINAL_DRAW(self)

    self.screen = display_screen
    _super_delivery_present_letterbox(self, self._letterbox_world_surface)


try:
    if _SUPER_DELIVERY_ORIGINAL_DRAW is not None and not getattr(GameManager, "_letterbox_patch_applied", False):
        GameManager._draw = _super_delivery_draw_letterboxed
        GameManager._letterbox_patch_applied = True
except Exception as exc:
    print(f"[WARN] Letterbox patch failed: {exc}")


try:
    _SUPER_DELIVERY_ORIGINAL_HANDLE_MOUSE_CLICK = GameManager._handle_mouse_click

    def _super_delivery_handle_mouse_click_letterbox(self, pos):
        scale = getattr(self, "_viewport_scale", 1.0)
        offset_x, offset_y = getattr(self, "_viewport_offset", (0, 0))

        if scale and scale > 0:
            x = int((pos[0] - offset_x) / scale)
            y = int((pos[1] - offset_y) / scale)
            pos = (x, y)

        return _SUPER_DELIVERY_ORIGINAL_HANDLE_MOUSE_CLICK(self, pos)

    if not getattr(GameManager, "_letterbox_mouse_patch_applied", False):
        GameManager._handle_mouse_click = _super_delivery_handle_mouse_click_letterbox
        GameManager._letterbox_mouse_patch_applied = True

except Exception:
    pass


