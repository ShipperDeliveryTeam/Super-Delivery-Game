# pyrefly: ignore [missing-import]
import pygame

# =======================================================
# DEFAULT MAP SETTINGS
# Các giá trị này chỉ là mặc định. Khi load file .tmx,
# game.py sẽ tự lấy width/height/tilewidth/tileheight từ TMX.
# =======================================================
COLS = 48
ROWS = 32
TILE_SIZE = 32

# Khi ảnh map lớn hơn màn hình máy tính, game sẽ tự thu nhỏ cửa sổ
# theo tỉ lệ này để không bị mất/cắt hình.
MAX_WINDOW_RATIO = 0.90

# Bật True nếu muốn nhìn lưới debug. Mặc định tắt để không che ảnh map.
SHOW_GRID = True

FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)

ROAD_COLOR = WHITE
OBSTACLE_COLOR = GRAY
SHIPPER_COLOR = (0, 100, 255)      # Blue
DESTINATION_COLOR = (255, 0, 0)    # Red
PATH_COLOR = (255, 255, 0)         # Yellow
VISITED_COLOR = (173, 216, 230)    # Light Blue
CURRENT_COLOR = (255, 165, 0)      # Orange
FRONTIER_COLOR = (0, 255, 0)       # Green

# Element Types
ROAD = '.'
OBSTACLE = '#'
START = 'S'
END = 'E'
