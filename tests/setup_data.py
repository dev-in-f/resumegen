from pathlib import Path

from resumegen.config import Config, DocumentConfig, load_yaml_to_data_model


def set_outputs_to_temp_dir(app_config: Config, tmp_path: Path) -> Config:
    new_app_config = app_config.model_copy(deep=True)
    new_app_config.output_config.output_dir = tmp_path
    return new_app_config


def load_test_data() -> tuple[DocumentConfig, Config]:
    app_config = load_yaml_to_data_model(
        Path(__package__).parent / "examples" / "config.example.yaml", Config
    )
    document_config = load_yaml_to_data_model(
        Path(__package__).parent / "examples" / "resume.example.yaml", DocumentConfig
    )
    app_config.template_dir = Path(__package__).parent / "templates"
    return document_config, app_config
