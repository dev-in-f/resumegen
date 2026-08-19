import os

import yaml

from resumegen.cli import app
from resumegen.config import RESUMEGEN_DATA_DIR, RESUMEGEN_DEFAULT_CONFIG_PATH, Config


def install_default_config():
    if not os.path.exists(RESUMEGEN_DATA_DIR):
        os.makedirs(RESUMEGEN_DATA_DIR)
    config_path = RESUMEGEN_DEFAULT_CONFIG_PATH
    if not os.path.exists(config_path):
        print(f"Creating default config at {config_path}")
        default_config = Config().model_dump(mode="json")
        with open(config_path, "w") as f:
            yaml.dump(default_config, f)


def main():
    install_default_config()
    app()


if __name__ == "__main__":
    main()
