from pathlib import Path

from resumegen.config import AppConfig, DocumentConfig, load_yaml_config


def set_outputs_to_temp_dir(app_config: AppConfig, tmp_path: Path) -> AppConfig:
    new_app_config = app_config.model_copy(deep=True)
    new_app_config.output_config.output_dir = tmp_path
    return new_app_config


def load_test_data() -> tuple[DocumentConfig, AppConfig]:
    app_config = load_yaml_config(
        Path(__package__).parent / "examples" / "config.example.yaml", AppConfig
    )
    document_config = load_yaml_config(
        Path(__package__).parent / "examples" / "resume.example.yaml", DocumentConfig
    )
    app_config.template_dir = Path(__package__).parent / "templates"
    return document_config, app_config
