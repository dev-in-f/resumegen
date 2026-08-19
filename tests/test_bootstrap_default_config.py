from unittest.mock import patch

import pytest

from resumegen._bootstrap import _install_default_config as install_default_config
from resumegen._bootstrap import bootstrap


@pytest.fixture
def bootstrap_paths(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    config_path = tmp_path / "config.yaml"
    monkeypatch.setattr("resumegen._bootstrap.RESUMEGEN_DATA_DIR", data_dir)
    monkeypatch.setattr(
        "resumegen._bootstrap.RESUMEGEN_DEFAULT_CONFIG_PATH", config_path
    )
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


class TestBootstrap:
    @patch("resumegen._bootstrap.dotenv.load_dotenv")
    @patch("resumegen._bootstrap._install_default_config")
    def test_bootstrap_calls_load_dotenv_and_install_default_config(
        self, mock_install_default_config, mock_load_dotenv
    ):
        bootstrap()
        mock_load_dotenv.assert_called_once_with(".env")
        mock_install_default_config.assert_called_once()
