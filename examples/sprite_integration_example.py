from __future__ import annotations

import sys
from pathlib import Path

# Allow running this file from examples/ without installing the package.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pygame

from src.entities.directional_shipper import DirectionalShipper
from src.systems.asset_paths import PLAYER_SPRITES, npc_sprites
from src.systems.sprite_loader import SpriteLoader

TILE_SIZE = 32
GRID_COLS = 24
GRID_ROWS = 16
SCREEN_WIDTH = GRID_COLS * TILE_SIZE
SCREEN_HEIGHT = GRID_ROWS * TILE_SIZE


def build_demo_grid():
    grid = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
    for x in range(5, 18):
        grid[7][x] = 1
    grid[7][11] = 0
    grid[7][12] = 0
    return grid


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Super Delivery - Sprite Integration Demo")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 13)

    grid = build_demo_grid()
    loader = SpriteLoader(tile_size=TILE_SIZE)

    player = DirectionalShipper(
        entity_id="PLAYER",
        position=(2, 2),
        sprites=loader.load_directional_sprites(PLAYER_SPRITES, fallback_color=(60, 140, 240)),
        tile_size=TILE_SIZE,
        speed_pixels=180,
    )

    npcs = []
    start_positions = [(20, 2), (20, 13), (2, 13), (12, 4)]
    npc_paths = [
        [(20, 2), (18, 2), (16, 2), (14, 2), (12, 2), (12, 6), (12, 8), (12, 12)],
        [(20, 13), (18, 13), (16, 13), (14, 13), (12, 13), (12, 12), (12, 8), (12, 6)],
        [(2, 13), (4, 13), (6, 13), (8, 13), (10, 13), (11, 8), (11, 6), (11, 4)],
        [(12, 4), (12, 5), (12, 6), (12, 8), (12, 10), (12, 12), (15, 12), (18, 12)],
    ]

    for i in range(1, 5):
        npc = DirectionalShipper(
            entity_id=f"NPC_{i}",
            position=start_positions[i - 1],
            sprites=loader.load_directional_sprites(npc_sprites(i), fallback_color=(180, 90, 230)),
            tile_size=TILE_SIZE,
            speed_pixels=90 + i * 10,
        )
        npc.set_path(npc_paths[i - 1])
        npcs.append(npc)

    def is_walkable(pos):
        x, y = pos
        if x < 0 or y < 0 or x >= GRID_COLS or y >= GRID_ROWS:
            return False
        return grid[y][x] == 0

    running = True
    while running:
        dt = clock.tick(60) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_w, pygame.K_UP):
                    player.move_one_tile(0, -1, is_walkable)
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    player.move_one_tile(0, 1, is_walkable)
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    player.move_one_tile(-1, 0, is_walkable)
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    player.move_one_tile(1, 0, is_walkable)

        for npc in npcs:
            npc.update(dt)
            if not npc.path and npc.target is None:
                npc.set_path(list(reversed(npc_paths[int(npc.entity_id[-1]) - 1])))
                npc_paths[int(npc.entity_id[-1]) - 1].reverse()

        screen.fill((36, 140, 72))

        for y in range(GRID_ROWS):
            for x in range(GRID_COLS):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if grid[y][x] == 1:
                    pygame.draw.rect(screen, (70, 80, 70), rect)
                else:
                    pygame.draw.rect(screen, (92, 92, 92), rect)
                pygame.draw.rect(screen, (40, 40, 40), rect, 1)

        for npc in npcs:
            npc.draw(screen, font)
        player.draw(screen, font)

        hint = font.render("WASD / Arrow: move player | ESC: quit", True, (255, 255, 255))
        screen.blit(hint, (8, 8))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
