import json
import logging
import os
from pathlib import Path
from typing import Optional
from ..models.audio import RecordingConfig, get_default_recordings_dir

logger = logging.getLogger("s_audio_pin.settings")


def get_config_dir() -> Path:
    """Returns XDG-compliant configuration directory for s-audio-pin."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME", "").strip()
    base = Path(xdg_config).expanduser() if xdg_config else (Path.home() / ".config")
    return base / "s-audio-pin"


def get_legacy_config_file() -> Path:
    """Legacy v0.1 configuration path (~/.config/s_audio_pin/config.json)."""
    return Path.home() / ".config" / "s_audio_pin" / "config.json"


CONFIG_DIR = get_config_dir()
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_RECORDINGS_DIR = get_default_recordings_dir()


class SettingsManager:
    def __init__(self, config_path: Optional[Path] = None):
        self._explicit_path = config_path is not None
        self.config_path = Path(config_path) if config_path else (get_config_dir() / "config.json")
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
                logger.warning("Error loading config from %s: %s", self.config_path, e)

        # Migrate legacy config (~/.config/s_audio_pin/config.json) when using default XDG path
        if not self._explicit_path:
            legacy_file = get_legacy_config_file()
            if legacy_file != self.config_path and legacy_file.exists():
                try:
                    with open(legacy_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self._config = RecordingConfig.from_dict(data)
                        logger.info("Migrated legacy config from %s to %s", legacy_file, self.config_path)
                        self.save(self._config)
                        return self._config
                except Exception as e:
                    logger.warning("Error migrating legacy config from %s: %s", legacy_file, e)

        # Default fallback
        self._config = RecordingConfig(output_dir=get_default_recordings_dir())
        self.save()
        return self._config

    def save(self, config: Optional[RecordingConfig] = None) -> bool:
        if config is not None:
            self._config = config
        elif self._config is None:
            self._config = RecordingConfig(output_dir=get_default_recordings_dir())

        # Normalize output_dir
        try:
            resolved_out = Path(self._config.output_dir).expanduser()
            self._config.output_dir = str(resolved_out)
        except Exception:
            resolved_out = Path(get_default_recordings_dir())
            self._config.output_dir = str(resolved_out)

        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            resolved_out.mkdir(parents=True, exist_ok=True)
            if not os.access(resolved_out, os.W_OK):
                raise PermissionError(f"Output directory is not writable: {resolved_out}")

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except OSError as e:
            logger.error("Error saving config or creating recordings dir (%s): %s", self.config_path, e)
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
