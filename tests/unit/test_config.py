import json
from pathlib import Path

from s_audio_pin.config.settings import SettingsManager, get_config_dir
from s_audio_pin.models.audio import RecordingConfig, get_default_recordings_dir


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

    mgr2 = SettingsManager(config_path=config_file)
    assert mgr2.config.format == "wav"
    assert mgr2.config.mode == "multi_stem"
    assert mgr2.config.bitrate == "256k"


def test_no_hardcoded_user_path(monkeypatch):
    monkeypatch.setenv("HOME", "/home/example_user")
    default_dir = get_default_recordings_dir()
    assert "s_linux" not in default_dir
    assert default_dir == "/home/example_user/Recordings/S_Audio_Pin"
    assert RecordingConfig().output_dir == "/home/example_user/Recordings/S_Audio_Pin"


def test_xdg_config_home_resolution(tmp_path, monkeypatch):
    custom_xdg = tmp_path / "custom_xdg"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(custom_xdg))
    assert get_config_dir() == custom_xdg / "s-audio-pin"

    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "fake_home"))
    assert get_config_dir() == tmp_path / "fake_home" / ".config" / "s-audio-pin"


def test_legacy_config_migration(tmp_path, monkeypatch):
    fake_home = tmp_path / "home"
    legacy_dir = fake_home / ".config" / "s_audio_pin"
    legacy_dir.mkdir(parents=True)
    legacy_file = legacy_dir / "config.json"
    legacy_rec = tmp_path / "legacy_rec"
    legacy_file.write_text(
        json.dumps({"format": "flac", "bitrate": "192k", "output_dir": str(legacy_rec)}),
        encoding="utf-8",
    )

    xdg_dir = tmp_path / "xdg"
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_dir))

    mgr = SettingsManager()
    assert mgr.config.format == "flac"
    assert mgr.config.bitrate == "192k"
    assert (xdg_dir / "s-audio-pin" / "config.json").exists()


def test_recording_config_clone():
    orig = RecordingConfig(format="mp3", bitrate="320k", mode="single_mix", sample_rate=48000)
    cloned = orig.clone(format="ogg", bitrate=None, mode="multi_stem")
    assert cloned.format == "ogg"
    assert cloned.bitrate == "320k"
    assert cloned.mode == "multi_stem"
    assert orig.format == "mp3"
    assert orig.mode == "single_mix"


def test_flatpak_localized_xdg_music_dir(tmp_path, monkeypatch):
    import sys

    fake_home = tmp_path / "home"
    fake_xdg = tmp_path / "xdg"
    fake_home.mkdir()
    fake_xdg.mkdir()
    (fake_xdg / "user-dirs.dirs").write_text(
        '# Localized XDG dirs\nXDG_MUSIC_DIR="$HOME/Музика"\n',
        encoding="utf-8",
    )

    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(fake_xdg))
    monkeypatch.delenv("XDG_MUSIC_DIR", raising=False)
    monkeypatch.setitem(sys.modules, "gi", None)

    orig_exists = Path.exists

    def fake_exists(self):
        if str(self) == "/.flatpak-info":
            return True
        return orig_exists(self)

    monkeypatch.setattr(Path, "exists", fake_exists)
    assert get_default_recordings_dir() == str(fake_home / "Музика" / "S_Audio_Pin")
