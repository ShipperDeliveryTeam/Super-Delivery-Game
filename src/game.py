import pygame
import sys
from .config import *
from .algorithms.bfs import bfs

class Game:
    def __init__(self, map_file):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Shipper Delivery Game - BFS Map 1")
        self.clock = pygame.time.Clock()
        
        self.grid = []
        self.start_pos = None
        self.end_pos = None
        
        self.load_map(map_file)
        
        self.path = []
        self.visited = set()
        self.shipper_pos = self.start_pos
        self.path_index = 0
        
        self.is_running_algo = False
        self.is_animating = False
        
    def load_map(self, file_path):
        with open(file_path, 'r') as f:
            for r, line in enumerate(f):
                row = list(line.strip())
                self.grid.append(row)
                for c, char in enumerate(row):
                    if char == START:
                        self.start_pos = (r, c)
                    elif char == END:
                        self.end_pos = (r, c)
                        
    def draw_grid(self):
        for r in range(ROWS):
            for c in range(COLS):
                rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                
                # Default background
                pygame.draw.rect(self.screen, ROAD_COLOR, rect)
                
                if self.grid[r][c] == OBSTACLE:
                    pygame.draw.rect(self.screen, OBSTACLE_COLOR, rect)
                elif (r, c) in self.visited and not self.is_animating:
                    # Draw visited nodes
                    pygame.draw.rect(self.screen, VISITED_COLOR, rect)
                elif (r, c) in self.path and not self.is_animating:
                    # Draw path
                    pygame.draw.rect(self.screen, PATH_COLOR, rect)
                
                # Draw start and end
                if (r, c) == self.start_pos:
                    # Draw a border or background for start if needed
                    pass
                if (r, c) == self.end_pos:
                    pygame.draw.rect(self.screen, DESTINATION_COLOR, rect)
                
                # Grid lines
                pygame.draw.rect(self.screen, LIGHT_GRAY, rect, 1)

    def draw_shipper(self):
        if self.shipper_pos:
            r, c = self.shipper_pos
            rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(self.screen, SHIPPER_COLOR, rect)
            
    def run_algorithm(self):
        print("Running BFS...")
        self.path, self.visited = bfs(self.grid, self.start_pos, self.end_pos)
        if self.path:
            print(f"Path found! Length: {len(self.path)}")
            self.is_animating = True
        else:
            print("No path found!")
        self.is_running_algo = False
        
    def run(self):
        running = True
        anim_timer = 0
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and not self.is_running_algo and not self.is_animating:
                        self.is_running_algo = True
                        self.run_algorithm()
                        
            # Animation logic
            if self.is_animating:
                anim_timer += self.clock.get_time()
                if anim_timer > 100: # move every 100ms
                    anim_timer = 0
                    if self.path_index < len(self.path):
                        self.shipper_pos = self.path[self.path_index]
                        self.path_index += 1
                    else:
                        self.is_animating = False # Animation finished
                        
            self.screen.fill(BLACK)
            self.draw_grid()
            self.draw_shipper()
            
            pygame.display.flip()
            self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()
