from pathlib import Path

from src.gameplay.auto.maps.map_profile import AutoMapProfile


PROJECT_ROOT = Path(__file__).resolve().parents[4]


MAP3_PROFILE = AutoMapProfile(
    map_id=3,
    name="Map 3 - Autumn",
    difficulty="HARD",

    tmx_path=PROJECT_ROOT / "maps" / "auto" / "map3" / "map3_auto.tmx",
    image_path=PROJECT_ROOT / "assets" / "images" / "map" / "map3.png",

    order_count=6,
    capacity=3,
    deadline_seconds=160.0,
    traffic_delay_seconds=3.0,

    allow_diagonal=True,
    has_roundabout=True,
    has_hidden_block=True,
    has_random_traffic=True,

    description="Map 3 khó: mùa thu, nhiều đường chéo, nhiều giao lộ và nhiều lựa chọn tuyến.",
)