import csv
from pathlib import Path
from typing import List, Tuple

Grid = List[List[int]]
GridPos = Tuple[int, int]


class MatrixLoader:
    ROAD = 0
    BLOCK = 1
    STORE = 2
    HOUSE = 3
    TRAP = 4
    WATER = 5
    BRIDGE = 6
    ROUNDABOUT = 7

    WALKABLE = {ROAD, STORE, HOUSE, TRAP, BRIDGE, ROUNDABOUT}

    def __init__(self, cols: int = 48, rows: int = 32):
        self.cols = cols
        self.rows = rows

    def load_csv(self, path: str | Path) -> Grid:
        path = Path(path)

        if not path.exists():
            return self.create_demo_matrix()

        grid: Grid = []

        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)

            for row in reader:
                if not row:
                    continue

                parsed_row = []

                for cell in row:
                    try:
                        parsed_row.append(int(str(cell).strip()))
                    except Exception:
                        parsed_row.append(1)

                grid.append(parsed_row)

        return self.normalize_grid(grid)

    def normalize_grid(self, grid: Grid) -> Grid:
        normalized: Grid = []

        for y in range(self.rows):
            row = list(grid[y]) if y < len(grid) else []

            if len(row) < self.cols:
                row += [1] * (self.cols - len(row))
            elif len(row) > self.cols:
                row = row[:self.cols]

            normalized.append(row)

        return normalized

    def save_csv(self, path: str | Path, grid: Grid) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        grid = self.normalize_grid(grid)

        with path.open("w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerows(grid)

    def create_demo_matrix(self) -> Grid:
        grid: Grid = [[1 for _ in range(self.cols)] for _ in range(self.rows)]

        def road_h(y: int, x1: int, x2: int, code: int = 0):
            for x in range(max(0, x1), min(self.cols, x2 + 1)):
                grid[y][x] = code

        def road_v(x: int, y1: int, y2: int, code: int = 0):
            for y in range(max(0, y1), min(self.rows, y2 + 1)):
                grid[y][x] = code

        road_h(5, 2, 44)
        road_h(10, 4, 44)
        road_h(16, 2, 43)
        road_h(22, 4, 45)
        road_h(27, 3, 43)

        road_v(4, 3, 28)
        road_v(12, 5, 27)
        road_v(22, 5, 27)
        road_v(34, 5, 27)
        road_v(44, 5, 27)

        for x, y in [(6, 5), (18, 10), (31, 16), (40, 22)]:
            grid[y][x] = self.STORE

        for x, y in [(10, 22), (22, 27), (36, 27), (44, 10)]:
            grid[y][x] = self.HOUSE

        for x, y in [(12, 16), (22, 10), (34, 22), (44, 16)]:
            grid[y][x] = self.TRAP

        return grid

    def extract_positions(self, grid: Grid, tile_code: int) -> list[GridPos]:
        positions = []

        for y, row in enumerate(grid):
            for x, value in enumerate(row):
                if value == tile_code:
                    positions.append((x, y))

        return positions

    def blocked_positions(self, grid: Grid) -> set[GridPos]:
        blocked = set()

        for y, row in enumerate(grid):
            for x, value in enumerate(row):
                if value not in self.WALKABLE:
                    blocked.add((x, y))

        return blocked
