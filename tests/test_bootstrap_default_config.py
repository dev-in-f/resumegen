from unittest.mock import patch

from resumegen.__main__ import install_default_config
from resumegen.__main__ import main as main_entrypoint


class TestInstallDefaultConfig:
    def test_creates_data_dir_if_missing(self, tmp_path, monkeypatch):
        data_dir = tmp_path / "data"
        config_path = tmp_path / "config.yaml"
        monkeypatch.setattr("resumegen.__main__.RESUMEGEN_DATA_DIR", data_dir)
        monkeypatch.setattr(
            "resumegen.__main__.RESUMEGEN_DEFAULT_CONFIG_PATH", config_path
        )
        install_default_config()
        assert data_dir.exists()

    def test_creates_default_config_if_missing(self, tmp_path, monkeypatch):
        data_dir = tmp_path / "data"
        config_path = tmp_path / "config.yaml"
        monkeypatch.setattr("resumegen.__main__.RESUMEGEN_DATA_DIR", data_dir)
        monkeypatch.setattr(
            "resumegen.__main__.RESUMEGEN_DEFAULT_CONFIG_PATH", config_path
        )
        install_default_config()
        assert config_path.exists()

    def test_does_not_overwrite_existing_config(self, tmp_path, monkeypatch):
        data_dir = tmp_path / "data"
        config_path = tmp_path / "config.yaml"
        config_path.write_text("existing: content\n")
        monkeypatch.setattr("resumegen.__main__.RESUMEGEN_DATA_DIR", data_dir)
        monkeypatch.setattr(
            "resumegen.__main__.RESUMEGEN_DEFAULT_CONFIG_PATH", config_path
        )
        install_default_config()
        assert config_path.read_text() == "existing: content\n"

    def test_skips_data_dir_creation_if_already_exists(self, tmp_path, monkeypatch):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        config_path = tmp_path / "config.yaml"
        monkeypatch.setattr("resumegen.__main__.RESUMEGEN_DATA_DIR", data_dir)
        monkeypatch.setattr(
            "resumegen.__main__.RESUMEGEN_DEFAULT_CONFIG_PATH", config_path
        )
        install_default_config()
        assert data_dir.is_dir()


class TestMainEntrypoint:
    def test_calls_app(self, tmp_path, monkeypatch):
        monkeypatch.setattr("resumegen.__main__.RESUMEGEN_DATA_DIR", tmp_path / "data")
        monkeypatch.setattr(
            "resumegen.__main__.RESUMEGEN_DEFAULT_CONFIG_PATH", tmp_path / "cfg.yaml"
        )
        with patch("resumegen.__main__.app") as mock_app:
            main_entrypoint()
        mock_app.assert_called_once()

    def test_install_runs_before_app(self, tmp_path, monkeypatch):
        data_dir = tmp_path / "data"
        config_path = tmp_path / "cfg.yaml"
        monkeypatch.setattr("resumegen.__main__.RESUMEGEN_DATA_DIR", data_dir)
        monkeypatch.setattr(
            "resumegen.__main__.RESUMEGEN_DEFAULT_CONFIG_PATH", config_path
        )
        with patch("resumegen.__main__.app"):
            main_entrypoint()
        assert config_path.exists()
