from datetime import datetime
from pathlib import Path

import pytest
from freezegun import freeze_time

from resumegen.config import Config, DocumentMetadata
from resumegen.renderer import (
    RenderError,
    _render_html,
    _sanitize_metadata,
    output_html,
    render_output_filename,
)


class TestSanitizeMetadata:
    def test_strings_lowercased_and_spaces_replaced(self):
        meta = DocumentMetadata(
            title="My Cool Resume", author="Jane Doe", language="en-US"
        )
        result = _sanitize_metadata(meta)
        assert result["title"] == "my_cool_resume"
        assert result["author"] == "jane_doe"
        assert result["language"] == "en-us"

    def test_keywords_sanitized_and_joined_with_underscore(self):
        meta = DocumentMetadata(title="T", author="A", keywords=["Python", "ML"])
        result = _sanitize_metadata(meta)
        assert result["keywords"] == "python_ml"

    def test_single_keyword(self):
        meta = DocumentMetadata(title="T", author="A", keywords=["python"])
        result = _sanitize_metadata(meta)
        assert result["keywords"] == "python"

    def test_empty_keywords_produces_empty_string(self):
        meta = DocumentMetadata(title="T", author="A", keywords=[])
        result = _sanitize_metadata(meta)
        assert result["keywords"] == ""

    def test_none_description_preserved(self):
        meta = DocumentMetadata(title="T", author="A")
        result = _sanitize_metadata(meta)
        assert result["description"] is None

    def test_description_sanitized_when_set(self):
        meta = DocumentMetadata(title="T", author="A", description="Senior Engineer")
        result = _sanitize_metadata(meta)
        assert result["description"] == "senior_engineer"


class TestJinjaRenderer:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path, fixtures_dir):
        self.config = Config(
            output_dir=Path(tmp_path) / "output",
            template_dir=fixtures_dir,
            template_name="test_template.html.j2",
        )

    @freeze_time("2026-01-01")
    def test_render_filename(self, minimal_document_metadata):
        filename = render_output_filename(
            self.config.output_filename, minimal_document_metadata
        )
        expected_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        assert filename == f"jane_doe_resume_{expected_date}.pdf"

    @freeze_time("2026-01-01")
    def test_render_filename_custom_template(self, minimal_document_metadata):
        self.config.output_filename = "{title}_{author}.pdf"
        filename = render_output_filename(
            self.config.output_filename, minimal_document_metadata
        )
        assert filename == "resume_jane_doe.pdf"

    def test_render_html(self, minimal_resume_data):
        html = _render_html(
            self.config.template_dir, self.config.template_name, minimal_resume_data
        )
        assert "Jane Doe" in html
        assert "Acme Co." in html
        assert "Python" in html
        assert "</div>" in html

    def test_render_html_raises(self, minimal_resume_data):
        with pytest.raises(RenderError):
            _render_html(
                self.config.template_dir,
                "non_existent_template.html.j2",
                minimal_resume_data,
            )

    def test_output_html(self, minimal_resume_data, tmp_path):
        output_path = output_html(
            self.config.template_dir,
            self.config.template_name,
            minimal_resume_data,
            self.config.output_filename,
            self.config.output_dir,
        )
        assert Path(output_path).exists()
        assert Path(output_path).suffix == ".html"
        Path(output_path).relative_to(tmp_path)
        with open(output_path) as f:
            content = f.read()
            assert "Jane Doe" in content
            assert "Acme Co." in content
            assert "Python" in content
            assert "</div>" in content
