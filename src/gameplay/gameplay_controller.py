from __future__ import annotations

from src.core.constants import NPC_COLORS, PLAYER_COLOR, TILE_SIZE
from src.systems.asset_paths import get_npc_sprite_paths, get_player_sprite_paths
from src.entities.directional_shipper import DirectionalShipper
from src.gameplay.auto.algorithm_groups import get_algorithms_by_group


class GameplayControllerMixin:
    def _play_mode_npc_algorithms(self) -> list[str]:
        group_id = int(getattr(self.settings, "selected_algorithm_group_id", 1))
        algorithms = get_algorithms_by_group(group_id)

        return algorithms or get_algorithms_by_group(1)

    def _create_shipper_objects(self) -> None:
        player_sprites = self.sprite_loader.load_directional_set(
            get_player_sprite_paths(),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=PLAYER_COLOR,
            label="P",
        )

        self.player = DirectionalShipper("Player", self.player_spawn, player_sprites, TILE_SIZE)
        self.player.allow_diagonal = self._allow_diagonal_movement()
        self.player.configure_roundabout(
            self._roundabout_center(),
            self._roundabout_ring(),
            self._roundabout_connections(),
        )

        self.npc_shippers = []
        default_positions = [(8, 8), (14, 10), (20, 12)]
        algorithms = self._play_mode_npc_algorithms()

        for i in range(3):
            npc_sprites = self.sprite_loader.load_directional_set(
                get_npc_sprite_paths(i + 1),
                size=(TILE_SIZE, TILE_SIZE),
                fallback_color=NPC_COLORS[i % len(NPC_COLORS)],
                label=str(i + 1),
            )

            raw_pos = self.npc_spawns[i] if i < len(self.npc_spawns) else default_positions[i]
            pos = self._nearest_walkable(raw_pos)

            algorithm = algorithms[i % len(algorithms)]
            npc = DirectionalShipper(algorithm, pos, npc_sprites, TILE_SIZE)
            npc.algorithm = algorithm
            npc.allow_diagonal = self._allow_diagonal_movement()
            npc.configure_roundabout(
                self._roundabout_center(),
                self._roundabout_ring(),
                self._roundabout_connections(),
            )
            self.npc_shippers.append(npc)
