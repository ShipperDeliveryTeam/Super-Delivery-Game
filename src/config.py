import pygame

# Grid Settings
COLS = 48
ROWS = 32
TILE_SIZE = 25

# Screen Settings
SCREEN_WIDTH = COLS * TILE_SIZE
SCREEN_HEIGHT = ROWS * TILE_SIZE
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

# Element Types (characters in the map txt file)
ROAD = '.'
OBSTACLE = '#'
START = 'S'
END = 'E'
