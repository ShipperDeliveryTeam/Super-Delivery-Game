from pathlib import Path

from src.gameplay.auto.maps.map_profile import AutoMapProfile


PROJECT_ROOT = Path(__file__).resolve().parents[4]


MAP2_PROFILE = AutoMapProfile(
    map_id=2,
    name="Map 2 - Snow",
    difficulty="MEDIUM",

    tmx_path=PROJECT_ROOT / "maps" / "auto" / "map2" / "map2_auto.tmx",
    image_path=PROJECT_ROOT / "assets" / "images" / "map" / "map2.png",

    order_count=2,
    capacity=2,
    deadline_seconds=200.0,
    traffic_delay_seconds=3.0,

    allow_diagonal=True,
    has_roundabout=True,
    has_hidden_block=False,
    has_random_traffic=True,

    description="Map 2 trung bình: map tuyết, cầu, sông, vòng xuyến, chi phí di chuyển cao hơn.",
)
