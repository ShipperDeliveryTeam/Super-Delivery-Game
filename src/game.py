# pyrefly: ignore [missing-import]
import os
import sys
import ctypes

# pyrefly: ignore [missing-import]
import pygame
# pyrefly: ignore [missing-import]
import pytmx

from .config import *
from .algorithms.bfs import bfs


class Game:
    """Game chính.

    Quy ước tọa độ trong toàn bộ game:
        - Grid position: (row, col)
        - Pixel position: (x, y)

    Sửa lỗi map bị lệch/cắt:
        - Không scale ảnh map trực tiếp về SCREEN_WIDTH/SCREEN_HEIGHT nữa.
        - Kích thước map lấy từ file TMX.
        - Vẽ mọi thứ lên world_surface đúng kích thước gốc của map.
        - Sau đó mới scale cả world_surface xuống cửa sổ nếu màn hình máy nhỏ.
    """

    def __init__(self, map_file):
        pygame.init()
        # Initialize a temporary hidden display for font/image init required by pytmx
        pygame.display.set_mode((1, 1), pygame.HIDDEN)
        pygame.display.set_caption("Shipper Delivery Game - BFS Map 1")
        self.clock = pygame.time.Clock()

        self.grid = []
        self.start_pos = None
        self.end_pos = None
        self.map_bg = None

        # Load TMX trước để biết kích thước thật của map.
        self.load_map(map_file)

        # Kích thước thật của thế giới game, tính theo pixel gốc của TMX.
        self.world_width = self.cols * self.tile_size
        self.world_height = self.rows * self.tile_size
        self.world_surface = pygame.Surface((self.world_width, self.world_height)).convert()

        # Tạo cửa sổ cho phép kéo giãn (RESIZABLE)
        info = pygame.display.Info()
        self.window_width = int(info.current_w * 0.85)
        self.window_height = int(info.current_h * 0.85)
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
        
        # Ép buộc hệ điều hành Windows Cực đại hóa (Maximize) cửa sổ
        try:
            hwnd = pygame.display.get_wm_info()["window"]
            ctypes.windll.user32.ShowWindow(hwnd, 3) # 3 = SW_MAXIMIZE
            pygame.event.pump() # Bắt buộc Pygame cập nhật sự kiện thay đổi kích thước
            self.window_width, self.window_height = self.screen.get_size()
        except Exception as e:
            print("Cảnh báo: Không thể maximize cửa sổ bằng ctypes:", e)

        self._recalculate_scale()

        self.path = []
        self.visited = set()
        self.shipper_pos = self.start_pos
        self.path_index = 0

        self.generator = None
        self.current_node = None
        self.frontier = []
        self.explored = set()
        self.is_searching = False
        self.search_timer = 0

        self.is_animating = False
        self.manual_mode = False
        self.move_timer = 0

    def _recalculate_scale(self):
        # Tính toán tỷ lệ để vẽ map nằm giữa màn hình, hỗ trợ upscale và downscale
        scale = min(self.window_width / self.world_width, self.window_height / self.world_height)
        self.drawn_width = int(self.world_width * scale)
        self.drawn_height = int(self.world_height * scale)
        self.offset_x = (self.window_width - self.drawn_width) // 2
        self.offset_y = (self.window_height - self.drawn_height) // 2

    def load_map(self, file_path):
        self.map_file = file_path
        self.tmx_data = pytmx.load_pygame(file_path)

        self.cols = self.tmx_data.width
        self.rows = self.tmx_data.height
        self.tile_size = self.tmx_data.tilewidth

        if self.tmx_data.tilewidth != self.tmx_data.tileheight:
            raise ValueError("Game hiện chỉ hỗ trợ tile vuông. Hãy đặt tilewidth = tileheight trong Tiled.")

        # Parse Collision Layer
        try:
            collision_layer = self.tmx_data.get_layer_by_name("Collision")
        except ValueError as exc:
            raise ValueError("Không tìm thấy layer 'Collision' trong file TMX.") from exc

        self.grid = []
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                gid = collision_layer.data[r][c]
                row.append(OBSTACLE if gid != 0 else ROAD)
            self.grid.append(row)

        # Parse Objects Layer
        try:
            object_group = self.tmx_data.get_layer_by_name("Objects")
        except ValueError as exc:
            raise ValueError("Không tìm thấy object layer 'Objects' trong file TMX.") from exc

        for obj in object_group:
            pos = self.pixel_to_grid(obj.x, obj.y)
            if obj.name == "shipper_spawn":
                self.start_pos = pos
            elif obj.name == "customer_house_1":
                self.end_pos = pos

        if self.start_pos is None:
            raise ValueError("Không tìm thấy object 'shipper_spawn' trong layer Objects.")
        if self.end_pos is None:
            raise ValueError("Không tìm thấy object 'customer_house_1' trong layer Objects.")

        # Đảm bảo điểm bắt đầu và đích không bị coi là vật cản.
        for pos in (self.start_pos, self.end_pos):
            r, c = pos
            if 0 <= r < self.rows and 0 <= c < self.cols:
                self.grid[r][c] = ROAD

        # Load ảnh map đúng kích thước gốc, không scale méo.
        self.map_bg = self.load_background_from_tmx(file_path)

    def load_background_from_tmx(self, file_path):
        """Lấy ảnh nền cho map hiện tại.
        
        Thay vì lấy từ tileset (vì tileset chỉ là ảnh nhỏ chứa tile),
        ta sẽ tìm ảnh cùng tên với map (vd: map1.tmx -> map1.png) trong thư mục assets/images/map.
        """
        map_name = os.path.splitext(os.path.basename(file_path))[0]
        image_name = map_name + ".png"
        
        # C:\AI\Super-Delivery-Game\assets\images\map
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        image_path = os.path.join(project_root, "assets", "images", "map", image_name)
        
        expected_size = (self.cols * self.tile_size, self.rows * self.tile_size)
        
        if os.path.exists(image_path):
            bg = pygame.image.load(image_path).convert()
            if bg.get_size() != expected_size:
                print(
                    "WARNING: Kích thước ảnh map không khớp TMX: "
                    f"ảnh={bg.get_size()}, TMX={expected_size}. "
                    "Game sẽ không scale ảnh để tránh lệch tọa độ. "
                )
            return bg

        print(f"WARNING: Không tìm thấy ảnh nền {image_path}. Game sẽ vẽ map dạng debug.")
        return None

    def pixel_to_grid(self, x, y):
        """Đổi tọa độ pixel của Tiled/Pygame sang grid (row, col)."""
        col = int(x // self.tile_size)
        row = int(y // self.tile_size)
        return row, col

    def grid_to_rect(self, pos):
        """Đổi grid (row, col) sang pygame.Rect pixel gốc."""
        r, c = pos
        return pygame.Rect(c * self.tile_size, r * self.tile_size, self.tile_size, self.tile_size)

    def draw_transparent_rect(self, rect, color, alpha):
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        s.fill((*color, alpha))
        self.world_surface.blit(s, rect)

    def draw_grid(self):
        # 1. Draw Background lên world_surface kích thước gốc.
        if self.map_bg:
            self.world_surface.blit(self.map_bg, (0, 0))
        else:
            self.world_surface.fill(BLACK)

        explored_positions = {state[0] for state in self.explored} if self.explored else set()
        frontier_positions = {node.state[0] for node in self.frontier} if self.frontier else set()
        current_pos = self.current_node.state[0] if self.current_node else None

        # 2. Draw algorithm overlays.
        for r in range(self.rows):
            for c in range(self.cols):
                rect = self.grid_to_rect((r, c))

                # Fallback nếu không load được ảnh nền.
                if not self.map_bg:
                    pygame.draw.rect(self.world_surface, ROAD_COLOR, rect)
                    if self.grid[r][c] == OBSTACLE:
                        pygame.draw.rect(self.world_surface, OBSTACLE_COLOR, rect)

                if self.is_searching:
                    if (r, c) == current_pos:
                        self.draw_transparent_rect(rect, CURRENT_COLOR, 150)
                    elif (r, c) in frontier_positions:
                        self.draw_transparent_rect(rect, FRONTIER_COLOR, 110)
                    elif (r, c) in explored_positions:
                        self.draw_transparent_rect(rect, VISITED_COLOR, 90)
                elif self.path:
                    if (r, c) in explored_positions and not self.is_animating:
                        self.draw_transparent_rect(rect, VISITED_COLOR, 60)
                    if (r, c) in self.path:
                        self.draw_transparent_rect(rect, PATH_COLOR, 170)

                if SHOW_GRID:
                    pygame.draw.rect(self.world_surface, LIGHT_GRAY, rect, 1)

        # Draw destination indicator sau overlay để dễ thấy.
        if self.end_pos:
            rect = self.grid_to_rect(self.end_pos)
            pygame.draw.circle(self.world_surface, DESTINATION_COLOR, rect.center, self.tile_size // 3)

    def draw_shipper(self):
        if self.shipper_pos:
            rect = self.grid_to_rect(self.shipper_pos)
            pygame.draw.rect(self.world_surface, SHIPPER_COLOR, rect)

    def present_world(self):
        """Scale cả world_surface ra cửa sổ. Tất cả tọa độ vẫn đúng vì đã vẽ ở hệ gốc."""
        self.screen.fill(BLACK)
        if (self.drawn_width, self.drawn_height) == (self.world_width, self.world_height):
            self.screen.blit(self.world_surface, (self.offset_x, self.offset_y))
        else:
            scaled = pygame.transform.smoothscale(self.world_surface, (self.drawn_width, self.drawn_height))
            self.screen.blit(scaled, (self.offset_x, self.offset_y))

    def run_algorithm(self):
        print("Starting BFS visualization...")
        self.generator = bfs(self.grid, self.start_pos, self.end_pos)
        self.is_searching = True
        self.path = []
        self.explored = set()
        self.frontier = []
        self.current_node = None
        self.shipper_pos = self.start_pos

    def run(self):
        running = True
        anim_timer = 0

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.window_width, self.window_height = event.w, event.h
                    self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
                    self._recalculate_scale()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:
                        self.manual_mode = not self.manual_mode
                        self.is_searching = False
                        self.is_animating = False
                        self.path = []
                        self.explored = set()
                        self.frontier = []
                        print(f"Manual Mode: {'ON' if self.manual_mode else 'OFF'}")

                    if event.key == pygame.K_SPACE and not self.is_searching and not self.is_animating and not self.manual_mode:
                        self.run_algorithm()

            # Manual Movement Logic
            if self.manual_mode:
                keys = pygame.key.get_pressed()
                self.move_timer += self.clock.get_time()
                if self.move_timer > 150:
                    dr, dc = 0, 0
                    if keys[pygame.K_UP] or keys[pygame.K_w]:
                        dr = -1
                    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                        dr = 1
                    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                        dc = -1
                    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                        dc = 1

                    if dr != 0 or dc != 0:
                        nr, nc = self.shipper_pos[0] + dr, self.shipper_pos[1] + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            if self.grid[nr][nc] != OBSTACLE:
                                self.shipper_pos = (nr, nc)
                                self.move_timer = 0
                                print(f"Moved to: {self.shipper_pos}")
                            else:
                                print(f"Blocked by OBSTACLE at {nr}, {nc}")

            # Search visualization logic
            elif self.is_searching:
                self.search_timer += self.clock.get_time()
                if self.search_timer > 5:
                    self.search_timer = 0
                    try:
                        self.current_node, self.frontier, self.explored = next(self.generator)

                        if self.current_node and len(self.current_node.state[1]) == 0:
                            from .algorithms.common import reconstruct_path
                            self.path = reconstruct_path(self.current_node)
                            print(f"Path found! Length: {len(self.path)}")
                            self.is_searching = False
                            self.is_animating = True
                            self.path_index = 0
                    except StopIteration:
                        self.is_searching = False
                        if not self.path:
                            print("No path found!")

            # Animation logic for shipper
            elif self.is_animating:
                anim_timer += self.clock.get_time()
                if anim_timer > 100:
                    anim_timer = 0
                    if self.path_index < len(self.path):
                        self.shipper_pos = self.path[self.path_index]
                        self.path_index += 1
                    else:
                        self.is_animating = False

            self.draw_grid()
            self.draw_shipper()
            self.present_world()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()
