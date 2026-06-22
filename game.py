import argparse
from pathlib import Path
import sys
import traceback


PROJECT_ROOT = Path(__file__).resolve().parent
LOCAL_VENDOR_DIR = PROJECT_ROOT / ".vendor"

if LOCAL_VENDOR_DIR.is_dir():
    sys.path.insert(0, str(LOCAL_VENDOR_DIR))


def parse_args():
    parser = argparse.ArgumentParser(description="Super Delivery Game")
    parser.add_argument("--map", type=int, default=None)
    parser.add_argument("--algorithm", type=str, default=None)
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")

    args = parse_args()

    try:
        from src.core.game_manager import GameManager
        from src.core.settings import GameSettings

        settings = GameSettings()

        if args.map is not None:
            settings.set_map(args.map)

        if args.algorithm is not None:
            settings.set_algorithm(args.algorithm)

        settings.debug = args.debug

        game = GameManager(settings=settings, debug=args.debug)
        game.run()
        return 0

    except Exception as exc:
        print()
        print("[ERROR] Game bị lỗi khi chạy.")
        print(f"Lỗi: {exc}")

        if args.debug:
            print()
            print("[DEBUG TRACEBACK]")
            traceback.print_exc()
        else:
            print()
            print("Gợi ý: chạy lại bằng lệnh sau để xem lỗi chi tiết:")
            print("python game.py --debug")

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
