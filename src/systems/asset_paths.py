from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = PROJECT_ROOT / "assets"

CHARACTERS_DIR = ASSETS_DIR / "characters"
PLAYER_DIR = CHARACTERS_DIR / "player"
NPC_DIR = CHARACTERS_DIR / "npc"

ICONS_DIR = ASSETS_DIR / "icons"
OLD_ICON_DIR = ASSETS_DIR / "icon"
MAPS_DIR = ASSETS_DIR / "maps"
IMAGES_DIR = ASSETS_DIR / "images"
UI_DIR = ASSETS_DIR / "ui"
SOUNDS_DIR = ASSETS_DIR / "sounds"


def first_existing(*paths: Path):
    for path in paths:
        if path and Path(path).exists():
            return Path(path)
    return None


def find_asset(folder: Path, names: list[str]):
    for name in names:
        path = folder / name
        if path.exists():
            return path
    return None


def find_asset_recursive(names: list[str]):
    folders = [
        UI_DIR,
        ICONS_DIR,
        ICONS_DIR / "button",
        OLD_ICON_DIR / "button",
        IMAGES_DIR,
        IMAGES_DIR / "ui",
        ASSETS_DIR,
    ]

    for folder in folders:
        for name in names:
            path = folder / name
            if path.exists():
                return path

    return None


def get_map_image_path(map_id: int):
    """
    Tìm ảnh nền thật của map.

    Bạn có thể đặt ảnh ở một trong các đường dẫn:
    - assets/images/map/map1.png
    - assets/images/map/map_1.png
    - assets/images/map_1.png
    - assets/images/map1.png
    - assets/maps/map_1.png
    - assets/maps/map1.png
    """
    return first_existing(
        MAPS_DIR / f"map_{map_id}.png",
        MAPS_DIR / f"map{map_id}.png",

        IMAGES_DIR / "map" / f"map{map_id}.png",
        IMAGES_DIR / "map" / f"map_{map_id}.png",

        IMAGES_DIR / f"map_{map_id}.png",
        IMAGES_DIR / f"map{map_id}.png",

        ASSETS_DIR / f"map_{map_id}.png",
        ASSETS_DIR / f"map{map_id}.png",
    )


def get_icon_path(name: str):
    candidates = {
        "store": ["store.png", "delivery_store.png", "shop.png"],
        "house": ["customer_house.png", "house.png", "home.png"],
        "money": ["money_100.png", "coin.png", "money.png"],
        "trap": ["trap.png", "hole.png"],

        "play": ["play_button.png", "PlayBtn.png", "Play.png", "play.png"],
        "sound_on": ["sound_on.png", "SoundOnBtn.png", "SoundOn.png", "volume_on.png", "speaker_on.png"],
        "sound_off": ["sound_off.png", "SoundOffBtn.png", "SoundOff.png", "volume_off.png", "speaker_off.png"],
        "menu": ["menu_button.png", "MenuBtn.png", "HomeBtn.png", "menu.png", "help.png", "settings.png"],
    }

    if name in candidates:
        return find_asset_recursive(candidates[name])

    return find_asset(ICONS_DIR, [f"{name}.png"])


def get_ui_asset_path(name: str):
    names = [name, name.lower(), name.upper(), name.capitalize()]

    candidates = []
    for n in names:
        candidates.extend([
            UI_DIR / n,
            IMAGES_DIR / "ui" / n,
            IMAGES_DIR / n,
            ASSETS_DIR / n,
            ICONS_DIR / n,
            ICONS_DIR / "button" / n,
            OLD_ICON_DIR / "button" / n,
        ])

    return first_existing(*candidates)


def get_player_sprite_paths():
    return {
        "side": first_existing(
            PLAYER_DIR / "shipper.png",
            PLAYER_DIR / "Shipper.png",
            PLAYER_DIR / "player_shipper.png",
            UI_DIR / "Shipper.png",
            UI_DIR / "shipper.png",
        ),
        "front": first_existing(
            PLAYER_DIR / "shipper_front_view.png",
            PLAYER_DIR / "Shipper_front_view.png",
            PLAYER_DIR / "player_front_view.png",
        ),
        "back": first_existing(
            PLAYER_DIR / "shipper_behind_view.png",
            PLAYER_DIR / "shipper_behind.view.png",
            PLAYER_DIR / "Shipper_behind_view.png",
            PLAYER_DIR / "player_behind_view.png",
        ),
    }


def get_npc_sprite_paths(npc_id: int):
    return {
        "side": find_asset(NPC_DIR, [f"npc_{npc_id}.png", f"npc{npc_id}.png"]),
        "front": find_asset(NPC_DIR, [f"npc_{npc_id}_front_view.png", f"npc{npc_id}_front_view.png"]),
        "back": find_asset(NPC_DIR, [f"npc_{npc_id}_behind_view.png", f"npc{npc_id}_behind_view.png"]),
    }
