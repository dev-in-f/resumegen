from unittest.mock import patch

import pytest

from resumegen.__init__ import install_default_config
from resumegen.__init__ import main as main_entrypoint


@pytest.fixture
def bootstrap_paths(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    config_path = tmp_path / "config.yaml"
    monkeypatch.setattr("resumegen.__init__.RESUMEGEN_DATA_DIR", data_dir)
    monkeypatch.setattr("resumegen.__init__.RESUMEGEN_DEFAULT_CONFIG_PATH", config_path)
    return data_dir, config_path


class TestInstallDefaultConfig:
    def test_creates_data_dir_if_missing(self, bootstrap_paths):
        data_dir, _ = bootstrap_paths
        install_default_config()
        assert data_dir.exists()

    def test_creates_default_config_if_missing(self, bootstrap_paths):
        _, config_path = bootstrap_paths
        install_default_config()
        assert config_path.exists()

    def test_does_not_overwrite_existing_config(self, bootstrap_paths):
        _, config_path = bootstrap_paths
        config_path.write_text("existing: content\n")
        install_default_config()
        assert config_path.read_text() == "existing: content\n"

    def test_skips_data_dir_creation_if_already_exists(self, bootstrap_paths):
        data_dir, _ = bootstrap_paths
        data_dir.mkdir()
        install_default_config()
        assert data_dir.is_dir()


class TestMainEntrypoint:
    def test_calls_app(self, bootstrap_paths):
        with patch("resumegen.__init__.app") as mock_app:
            main_entrypoint()
        mock_app.assert_called_once()

    def test_install_runs_before_app(self, bootstrap_paths):
        _, config_path = bootstrap_paths
        with patch("resumegen.__init__.app"):
            main_entrypoint()
        assert config_path.exists()
