from importlib import resources
from pathlib import Path

from resumegen.config import Config, ResumeData, load_yaml_to_data_model


def load_test_data() -> tuple[Config, ResumeData]:
    config = load_yaml_to_data_model(
        Path(__package__).parent / "examples" / "config.yaml", Config
    )
    resume_data = load_yaml_to_data_model(
        Path(__package__).parent / "examples" / "resume-data.yaml", ResumeData
    )
    with resources.path("resumegen", "templates") as template_dir:
        config.template_dir = template_dir
        return resume_data, config
