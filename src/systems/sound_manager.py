from __future__ import annotations

from pathlib import Path

# pyrefly: ignore [missing-import]
import pygame

from src.systems.asset_paths import SOUNDS_DIR


EFFECT_VOLUME = 0.45
BACKGROUND_VOLUME = 0.55
EFFECT_VOLUMES = {
    "delivery": 0.85,
}


class SoundManager:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = bool(enabled)
        self.available = False
        self.effects: dict[str, pygame.mixer.Sound] = {}
        self.background_loaded = False

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.available = True
        except Exception as exc:
            print(f"[WARN] Khong khoi tao duoc audio mixer: {exc}")

    def load(self) -> None:
        if not self.available:
            return

        self.effects = {
            "pickup": self._load_effect("pickup", "pickup.mp3"),
            "delivery": self._load_effect("delivery", "delivery.mp3"),
            "trap": self._load_effect("trap", "trap.mp3"),
            "win": self._load_effect("win", "win.wav"),
            "gameover": self._load_effect("gameover", "gameover.mp3"),
        }
        self.effects = {name: sound for name, sound in self.effects.items() if sound is not None}
        self._load_background("background_music.mp3")

    def _effect_volume(self, name: str) -> float:
        return EFFECT_VOLUMES.get(name, EFFECT_VOLUME)

    def _load_effect(self, name: str, filename: str):
        path = Path(SOUNDS_DIR) / filename
        if not path.exists():
            print(f"[WARN] Khong tim thay sound effect: {path}")
            return None

        try:
            sound = pygame.mixer.Sound(str(path))
            sound.set_volume(self._effect_volume(name))
            return sound
        except Exception as exc:
            print(f"[WARN] Khong load duoc sound effect {filename}: {exc}")
            return None

    def _load_background(self, filename: str) -> None:
        path = Path(SOUNDS_DIR) / filename
        if not path.exists():
            print(f"[WARN] Khong tim thay background music: {path}")
            return

        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(BACKGROUND_VOLUME)
            self.background_loaded = True
        except Exception as exc:
            print(f"[WARN] Khong load duoc background music {filename}: {exc}")

    def play_background(self) -> None:
        if self.available and self.enabled and self.background_loaded:
            pygame.mixer.music.play(-1)

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled)

        if not self.available:
            return

        if self.enabled:
            if self.background_loaded and not pygame.mixer.music.get_busy():
                pygame.mixer.music.set_volume(BACKGROUND_VOLUME)
                pygame.mixer.music.play(-1)
            else:
                pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()

    def play_effect(self, name: str) -> None:
        if not self.available or not self.enabled:
            return

        sound = self.effects.get(name)
        if sound is not None:
            sound.set_volume(self._effect_volume(name))
            sound.play()

    def stop(self) -> None:
        if self.available:
            pygame.mixer.music.stop()
