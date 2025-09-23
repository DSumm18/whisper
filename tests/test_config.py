from app.config import AppConfig, load_config, save_config


def test_load_creates_default(tmp_path):
    path = tmp_path / "config.yaml"
    config = load_config(path)
    assert isinstance(config, AppConfig)
    assert path.exists()
    assert config.audio.sample_rate == 16_000


def test_save_roundtrip(tmp_path):
    path = tmp_path / "config.yaml"
    config = AppConfig.default()
    config.audio.sample_rate = 44_100
    save_config(config, path)
    loaded = load_config(path)
    assert loaded.audio.sample_rate == 44_100
    assert loaded.transcription.language == "en"
