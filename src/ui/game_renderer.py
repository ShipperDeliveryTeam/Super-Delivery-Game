from __future__ import annotations

from typing import List, Tuple

# pyrefly: ignore [missing-import]
import pygame

from src.core.constants import (
    BACKGROUND_COLOR,
    GRID_LINE_COLOR,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)
from src.core.game_state import GameState
from src.gameplay.roundabout_geometry import build_roundabout_curve, curve_point
from src.maps.matrix_loader import MatrixLoader


class GameRendererMixin:
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
        # pyrefly: ignore [missing-import]
        import pygame

        time_ticks = pygame.time.get_ticks()
        bounce_offset = abs(math.sin(time_ticks * 0.005)) * 10  # Jump height up to 10 pixels

        if not self.simulation_mode:
            self._draw_player_offer_markers(bounce_offset)

        # Draw for Player
        if (
            not self.simulation_mode
            and getattr(self, 'player_task', None)
            and self.player_task.picked_up
            and not self.player_task.delivered
        ):
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

    def _draw_player_offer_markers(self, bounce_offset: float) -> None:
        offers = [
            task for task in getattr(self, "available_player_tasks", [])
            if not getattr(task, "picked_up", False)
        ]
        selected_index = getattr(self, "selected_player_order_index", -1)
        cell_w, cell_h = self._cell_size_screen()
        self._offer_marker_rects = []

        for index, task in enumerate(offers[:5]):
            x, y = self._grid_to_screen(task.store_pos)
            center = (x + cell_w // 2, y + cell_h // 2 - int(bounce_offset * 0.45))
            selected = index == selected_index
            icon = self.icons.get("location_shop")
            if icon:
                scale = 1.6; icon_w = max(1, int(icon.get_width() * scale)); icon_h = max(1, int(icon.get_height() * scale))
                icon = pygame.transform.smoothscale(icon, (icon_w, icon_h))
                draw_x = center[0] - icon_w // 2
                draw_y = center[1] - icon_h + cell_h // 3
                self.screen.blit(icon, (draw_x, draw_y))
            else:
                self._draw_target_marker(task.store_pos)
            self._offer_marker_rects.append(pygame.Rect(center[0] - 22, center[1] - 22, 44, 44))

            if selected:
                target_x, target_y = self._grid_to_screen(task.house_pos)
                target_center = (target_x + cell_w // 2, target_y + cell_h // 2)
                house_number = self._house_number(task.house_pos)
                label = str(house_number) if house_number else "H"
                self._draw_text(label, self.font_tiny, (9, 27, 50), target_center[0] + 1, target_center[1] - 6, center=True)
                self._draw_text(label, self.font_tiny, (255, 255, 255), target_center[0], target_center[1] - 7, center=True)

    def _draw_bouncing_location(self, icon_name: str, grid_pos: Tuple[int, int], bounce_offset: float) -> None:
        icon = self.icons.get(icon_name)
        if not icon:
            return

        x, y = self._grid_to_screen(grid_pos)

        cell_w, cell_h = self._cell_size_screen()
        scale = 1.6; icon_w = max(1, int(icon.get_width() * scale)); icon_h = max(1, int(icon.get_height() * scale))
        icon = pygame.transform.smoothscale(icon, (icon_w, icon_h))

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

        scale = 1.35; draw_w = max(1, int(cell_w * scale)); draw_h = max(1, int(cell_h * scale))
        if sprite.get_width() != draw_w or sprite.get_height() != draw_h:
            sprite = pygame.transform.smoothscale(sprite, (draw_w, draw_h))

        draw_x = x + (cell_w - draw_w) // 2
        draw_y = y + cell_h - draw_h
        self.screen.blit(sprite, (draw_x, draw_y))

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
