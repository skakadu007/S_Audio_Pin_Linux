import json
import os
from pathlib import Path
from typing import Optional
from ..models.audio import RecordingConfig

CONFIG_DIR = Path.home() / ".config" / "s_audio_pin"
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_RECORDINGS_DIR = str(Path.home() / "Recordings" / "S_Audio_Pin")


class SettingsManager:
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_FILE
        self.config_dir = self.config_path.parent
        self._config: Optional[RecordingConfig] = None
        self.load()

    def load(self) -> RecordingConfig:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._config = RecordingConfig.from_dict(data)
                    return self._config
            except Exception as e:
                print(f"[Settings] Error loading config from {self.config_path}: {e}")

        # Default fallback
        self._config = RecordingConfig(output_dir=DEFAULT_RECORDINGS_DIR)
        self.save()
        return self._config

    def save(self, config: Optional[RecordingConfig] = None) -> bool:
        if config is not None:
            self._config = config
        elif self._config is None:
            self._config = RecordingConfig(output_dir=DEFAULT_RECORDINGS_DIR)

        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            # Ensure recordings dir exists too
            Path(self._config.output_dir).mkdir(parents=True, exist_ok=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[Settings] Error saving config to {self.config_path}: {e}")
            return False

    @property
    def config(self) -> RecordingConfig:
        if self._config is None:
            return self.load()
        return self._config

    @config.setter
    def config(self, val: RecordingConfig):
        self.save(val)


# Global singleton instance
settings_manager = SettingsManager()
