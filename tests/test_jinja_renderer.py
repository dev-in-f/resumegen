from datetime import datetime
from pathlib import Path

import pytest
from freezegun import freeze_time

from resumegen.config import DocumentMeta
from resumegen.renderer import (
    _sanitize_metadata,
    output_html,
    render_html,
    render_output_filename,
)
from tests.setup_data import load_test_data, set_outputs_to_temp_dir


@pytest.fixture(scope="session")
def test_data():
    return load_test_data()


class TestSanitizeMetadata:
    def test_strings_lowercased_and_spaces_replaced(self):
        meta = DocumentMeta(title="My Cool Resume", author="Jane Doe", language="en-US")
        result = _sanitize_metadata(meta)
        assert result["title"] == "my_cool_resume"
        assert result["author"] == "jane_doe"
        assert result["language"] == "en-us"

    def test_keywords_sanitized_and_joined_with_underscore(self):
        meta = DocumentMeta(title="T", author="A", keywords=["Python", "ML"])
        result = _sanitize_metadata(meta)
        assert result["keywords"] == "python_ml"

    def test_single_keyword(self):
        meta = DocumentMeta(title="T", author="A", keywords=["python"])
        result = _sanitize_metadata(meta)
        assert result["keywords"] == "python"

    def test_empty_keywords_produces_empty_string(self):
        meta = DocumentMeta(title="T", author="A", keywords=[])
        result = _sanitize_metadata(meta)
        assert result["keywords"] == ""

    def test_none_description_preserved(self):
        meta = DocumentMeta(title="T", author="A")
        result = _sanitize_metadata(meta)
        assert result["description"] is None

    def test_description_sanitized_when_set(self):
        meta = DocumentMeta(title="T", author="A", description="Senior Engineer")
        result = _sanitize_metadata(meta)
        assert result["description"] == "senior_engineer"


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

    @freeze_time("2026-01-01")
    def test_render_filename_custom_template(self):
        app_config = self.app_config.model_copy(deep=True)
        app_config.output_config.output_filename = "{title}_{author}.pdf"
        filename = render_output_filename(self.document_config, app_config)
        assert filename == "jane_doe's_resume_jane_doe.pdf"

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
        assert Path(output_path).suffix == ".html"
        assert Path(output_path).is_relative_to(tmp_path)
        with open(output_path) as f:
            content = f.read()
            assert "Jane Doe" in content
            assert "Acme Co." in content
            assert "Python" in content
            assert "</div>" in content
