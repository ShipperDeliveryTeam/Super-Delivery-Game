import argparse
import traceback


def parse_args():
    parser = argparse.ArgumentParser(description="Super Delivery Game")
    parser.add_argument("--map", type=int, default=None)
    parser.add_argument("--algorithm", type=str, default=None)
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


def main():
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


if __name__ == "__main__":
    main()
