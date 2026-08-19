from datetime import datetime
from pathlib import Path

import pytest
from freezegun import freeze_time

from resumegen.config import (
    AppConfig,
    DocumentConfig,
    load_yaml_config,
)
from resumegen.renderer import (
    _sanitize_metadata,
    output_html,
    render_html,
    render_output_filename,
)


@pytest.fixture(scope="session")
def test_data():
    return load_test_data()


def set_outputs_to_temp_dir(app_config: AppConfig, tmp_path: Path) -> AppConfig:
    new_app_config = app_config.model_copy(deep=True)
    new_app_config.output_config.output_dir = tmp_path
    return new_app_config


def load_test_data() -> tuple[DocumentConfig, AppConfig]:
    app_config = load_yaml_config(
        Path(__package__).parent / "config.example.yaml", AppConfig
    )
    document_config = load_yaml_config(
        Path(__package__).parent / "resume.example.yaml", DocumentConfig
    )
    app_config.template_dir = Path(__package__).parent / "templates"
    return document_config, app_config


class TestJinjaRenderer:
    @pytest.fixture(autouse=True)
    def setup(self, test_data):
        self.document_config, self.app_config = test_data

    def test_sanitize_metadata(self):
        sanitized = _sanitize_metadata(self.document_config.document_metadata)
        assert sanitized["title"] == "jane_doe's_resume"
        assert sanitized["author"] == "jane_doe"
        assert sanitized["keywords"] == "resume_cv"
        assert sanitized["language"] == "en-us"

    @freeze_time("2026-01-01")
    def test_render_filename(self):
        filename = render_output_filename(self.document_config, self.app_config)
        expected_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        assert filename == f"jane_doe_resume_{expected_date}.pdf"

    def test_render_html(self):
        html = render_html(self.document_config, self.app_config)
        assert "Jane Doe" in html
        assert "Acme Co." in html
        assert "Python" in html
        assert "</div>" in html

    def test_output_html(self, tmp_path):
        app_config = set_outputs_to_temp_dir(self.app_config, tmp_path)
        output_path = output_html(self.document_config, app_config)
        assert Path(output_path).exists()
        assert Path(output_path).is_relative_to(tmp_path)
        with open(output_path) as f:
            content = f.read()
            assert "Jane Doe" in content
            assert "Acme Co." in content
            assert "Python" in content
            assert "</div>" in content
