from pathlib import Path

from src.gameplay.auto.maps.map_profile import AutoMapProfile


PROJECT_ROOT = Path(__file__).resolve().parents[4]


MAP1_PROFILE = AutoMapProfile(
    map_id=1,
    name="Map 1 - City",
    difficulty="EASY",

    tmx_path=PROJECT_ROOT / "maps" / "auto" / "map1" / "map1_auto.tmx",
    image_path=PROJECT_ROOT / "assets" / "images" / "map" / "map1.png",

    order_count=2,
    capacity=1,
    deadline_seconds=240.0,
    traffic_delay_seconds=2.0,

    allow_diagonal=False,
    has_roundabout=False,
    has_hidden_block=False,
    has_random_traffic=False,

    description="Map 1 dễ: thành phố sáng, đường lưới rõ, ít bất định.",
)
