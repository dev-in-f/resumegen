import os
from pathlib import Path

import dotenv
import yaml

from resumegen._core.config import (
    RESUMEGEN_DATA_DIR,
    RESUMEGEN_DEFAULT_CONFIG_PATH,
    Config,
)


def _install_default_config():
    if not Path(RESUMEGEN_DATA_DIR).exists():
        Path(RESUMEGEN_DATA_DIR).mkdir(parents=True, exist_ok=True)
    config_path = RESUMEGEN_DEFAULT_CONFIG_PATH
    if not Path(config_path).exists():
        default_config = Config().model_dump(mode="json")
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)
        with Path(config_path).open("w") as f:
            yaml.dump(default_config, f)


def bootstrap():
    env_path = os.getenv("RESUMEGEN_ENV_PATH", ".env")
    dotenv.load_dotenv(env_path)
    _install_default_config()
