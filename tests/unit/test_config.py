import pytest
from pathlib import Path
from src.config.settings import SettingsManager
from src.models.audio import RecordingConfig


def test_config_defaults(tmp_path):
    config_file = tmp_path / "test_config.json"
    mgr = SettingsManager(config_path=config_file)
    cfg = mgr.config
    assert cfg.format == "mp3"
    assert cfg.bitrate == "320k"
    assert cfg.mode == "single_mix"
    assert config_file.exists()


def test_config_save_and_reload(tmp_path):
    config_file = tmp_path / "test_config.json"
    mgr = SettingsManager(config_path=config_file)
    new_cfg = RecordingConfig(
        format="wav",
        bitrate="256k",
        mode="multi_stem",
        output_dir=str(tmp_path / "recordings"),
    )
    assert mgr.save(new_cfg) is True

    # Reload from fresh manager
    mgr2 = SettingsManager(config_path=config_file)
    assert mgr2.config.format == "wav"
    assert mgr2.config.mode == "multi_stem"
    assert mgr2.config.bitrate == "256k"
