import os

import dotenv
import yaml

from resumegen._core.config import (
    RESUMEGEN_DATA_DIR,
    RESUMEGEN_DEFAULT_CONFIG_PATH,
    Config,
)


def _install_default_config():
    if not os.path.exists(RESUMEGEN_DATA_DIR):
        os.makedirs(RESUMEGEN_DATA_DIR)
    config_path = RESUMEGEN_DEFAULT_CONFIG_PATH
    if not os.path.exists(config_path):
        print(f"Creating default config at {config_path}")
        default_config = Config().model_dump(mode="json")
        with open(config_path, "w") as f:
            yaml.dump(default_config, f)


def bootstrap():
    env_path = os.getenv("RESUMEGEN_ENV_PATH", ".env")
    dotenv.load_dotenv(env_path)
    _install_default_config()
