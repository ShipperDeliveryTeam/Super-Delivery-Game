"""
Super Delivery Game - Main Entry Point
--------------------------------------
File chạy chính của đồ án game shipper AI.

Cách chạy:
    python game.py

Yêu cầu project có cấu trúc:
    game.py
    src/
        core/
        maps/
        entities/
        ai/
        gameplay/
        ui/
        systems/
        utils/
    assets/

File này ưu tiên gọi GameManager trong src/core/game_manager.py.
Các phần xử lý map, AI, entities, gameplay, ui, systems sẽ được GameManager điều phối.
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
ASSETS_DIR = PROJECT_ROOT / "assets"


# Đảm bảo Python tìm được package src khi chạy trực tiếp bằng: python game.py
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


SUPPORTED_ALGORITHMS = [
    "BFS",
    "ASTAR",
    "BEAM",
    "PARTIAL_OBSERVATION",
    "Q_LEARNING",
]


DEFAULT_MAP_ID = 1
DEFAULT_ALGORITHM = "ASTAR"


def check_project_structure() -> list[str]:
    """
    Kiểm tra nhanh các thư mục quan trọng.
    Hàm này không chặn game chạy, chỉ cảnh báo để dễ sửa lỗi khi ghép project.
    """
    warnings: list[str] = []

    required_dirs = [
        SRC_DIR,
        SRC_DIR / "core",
        SRC_DIR / "maps",
        SRC_DIR / "entities",
        SRC_DIR / "ai",
        SRC_DIR / "gameplay",
        SRC_DIR / "ui",
        SRC_DIR / "systems",
        SRC_DIR / "utils",
        ASSETS_DIR,
    ]

    for folder in required_dirs:
        if not folder.exists():
            warnings.append(f"Thiếu thư mục: {folder.relative_to(PROJECT_ROOT)}")

    required_files = [
        SRC_DIR / "core" / "game_manager.py",
        SRC_DIR / "core" / "settings.py",
        SRC_DIR / "core" / "game_state.py",
    ]

    for file_path in required_files:
        if not file_path.exists():
            warnings.append(f"Thiếu file: {file_path.relative_to(PROJECT_ROOT)}")

    return warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="Super Delivery Game",
        description="Chạy game đồ án AI: shipper giao hàng bằng thuật toán tìm kiếm.",
    )

    parser.add_argument(
        "--map",
        type=int,
        default=DEFAULT_MAP_ID,
        choices=[1, 2, 3, 4],
        help="Chọn map ban đầu: 1, 2, 3 hoặc 4.",
    )

    parser.add_argument(
        "--algorithm",
        type=str,
        default=DEFAULT_ALGORITHM,
        choices=SUPPORTED_ALGORITHMS,
        help="Chọn thuật toán mặc định.",
    )

    parser.add_argument(
        "--no-sound",
        action="store_true",
        help="Tắt âm thanh khi khởi động game.",
    )

    parser.add_argument(
        "--show-grid",
        action="store_true",
        help="Bật hiển thị lưới khi khởi động game.",
    )

    parser.add_argument(
        "--show-path",
        action="store_true",
        help="Bật gợi ý đường đi khi khởi động game.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Bật chế độ debug để in lỗi chi tiết.",
    )

    return parser.parse_args()


def apply_startup_options(game: object, args: argparse.Namespace) -> None:
    """
    Gán cấu hình khởi động cho GameManager nếu các thuộc tính tồn tại.
    Viết kiểu an toàn để không làm vỡ code nếu GameManager của bạn thay đổi tên biến.
    """

    candidate_settings = []

    if hasattr(game, "settings"):
        candidate_settings.append(getattr(game, "settings"))

    if hasattr(game, "config"):
        candidate_settings.append(getattr(game, "config"))

    # Một số bản GameManager có thể lưu trực tiếp trên object game.
    candidate_settings.append(game)

    for settings in candidate_settings:
        for attr_name in ["selected_map", "selected_map_id", "map_id", "current_map_id"]:
            if hasattr(settings, attr_name):
                setattr(settings, attr_name, args.map)

        for attr_name in ["selected_algorithm", "algorithm", "current_algorithm"]:
            if hasattr(settings, attr_name):
                setattr(settings, attr_name, args.algorithm)

        for attr_name in ["sound_enabled", "enable_sound", "music_enabled"]:
            if hasattr(settings, attr_name):
                setattr(settings, attr_name, not args.no_sound)

        for attr_name in ["show_grid", "grid_enabled", "debug_grid"]:
            if hasattr(settings, attr_name):
                setattr(settings, attr_name, args.show_grid)

        for attr_name in ["show_path", "path_hint_enabled", "guide_enabled"]:
            if hasattr(settings, attr_name):
                setattr(settings, attr_name, args.show_path)

        for attr_name in ["debug", "debug_mode", "is_debug"]:
            if hasattr(settings, attr_name):
                setattr(settings, attr_name, args.debug)


def import_game_manager():
    """
    Import GameManager từ src/core/game_manager.py.
    Tách riêng hàm này để báo lỗi rõ hơn nếu project chưa ghép đủ file.
    """
    try:
        from src.core.game_manager import GameManager
        return GameManager
    except ModuleNotFoundError as exc:
        print("\n[ERROR] Không import được GameManager.")
        print("Hãy kiểm tra bạn đã copy đầy đủ thư mục src/core vào project chưa.")
        print(f"Chi tiết lỗi: {exc}\n")
        raise
    except Exception as exc:
        print("\n[ERROR] File src/core/game_manager.py có lỗi khi import.")
        print(f"Chi tiết lỗi: {exc}\n")
        raise


def main() -> int:
    args = parse_args()

    os.chdir(PROJECT_ROOT)

    warnings = check_project_structure()
    if warnings:
        print("\n[CẢNH BÁO CẤU TRÚC PROJECT]")
        for warning in warnings:
            print(f"- {warning}")
        print("Game vẫn sẽ thử chạy tiếp nếu các file cần thiết đã có.\n")

    try:
        GameManager = import_game_manager()
        game = GameManager()
        apply_startup_options(game, args)

        print("Super Delivery Game đang chạy...")
        print(f"Map khởi động: Map {args.map}")
        print(f"Thuật toán mặc định: {args.algorithm}")

        game.run()
        return 0

    except KeyboardInterrupt:
        print("\nĐã thoát game bằng bàn phím.")
        return 0

    except Exception as exc:
        print("\n[ERROR] Game bị lỗi khi chạy.")
        print(f"Lỗi: {exc}")

        if args.debug:
            print("\n[DEBUG TRACEBACK]")
            traceback.print_exc()
        else:
            print("\nGợi ý: chạy lại bằng lệnh sau để xem lỗi chi tiết:")
            print("python game.py --debug")

        return 1

    finally:
        try:
            import pygame
            pygame.quit()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
