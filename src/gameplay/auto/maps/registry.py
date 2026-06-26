from __future__ import annotations

from src.gameplay.auto.maps.map1 import MAP1_PROFILE
from src.gameplay.auto.maps.map2 import MAP2_PROFILE
from src.gameplay.auto.maps.map3 import MAP3_PROFILE
from src.gameplay.auto.maps.map_profile import AutoMapProfile


AUTO_MAP_PROFILES: dict[int, AutoMapProfile] = {
    1: MAP1_PROFILE,
    2: MAP2_PROFILE,
    3: MAP3_PROFILE,
}


def get_auto_map_profile(map_id: int) -> AutoMapProfile:
    return AUTO_MAP_PROFILES.get(map_id, MAP1_PROFILE)


def get_all_auto_map_profiles() -> list[AutoMapProfile]:
    return list(AUTO_MAP_PROFILES.values())


def validate_auto_map_files() -> list[str]:
    errors: list[str] = []

    for profile in AUTO_MAP_PROFILES.values():
        if not profile.tmx_path.exists():
            errors.append(f"Missing TMX file for map {profile.map_id}: {profile.tmx_path}")

        if not profile.image_path.exists():
            errors.append(f"Missing image file for map {profile.map_id}: {profile.image_path}")

    return errors