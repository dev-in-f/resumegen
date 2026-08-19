from datetime import datetime
from pathlib import Path

import pytest
from freezegun import freeze_time

from resumegen._core.config import Config
from resumegen._core.exceptions import RenderError
from resumegen._core.formatting import _format_output_filename
from resumegen._core.html_rendering import (
    _render_html_from_template,
    render_html,
)


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
        filename = _format_output_filename(
            self.config.output_filename, minimal_document_metadata
        )
        expected_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        assert filename == f"jane_doe_resume_{expected_date}.pdf"

    @freeze_time("2026-01-01")
    def test_render_filename_custom_template(self, minimal_document_metadata):
        self.config.output_filename = "{title}_{author}.pdf"
        filename = _format_output_filename(
            self.config.output_filename, minimal_document_metadata
        )
        assert filename == "resume_jane_doe.pdf"

    def test_render_html(self, minimal_resume_data):
        html = _render_html_from_template(
            self.config.template_dir, self.config.template_name, minimal_resume_data
        )
        assert "Jane Doe" in html
        assert "Acme Co." in html
        assert "Python" in html
        assert "</div>" in html

    def test_render_html_raises(self, minimal_resume_data):
        with pytest.raises(RenderError):
            _render_html_from_template(
                self.config.template_dir,
                "non_existent_template.html.j2",
                minimal_resume_data,
            )

    def test_output_html(self, minimal_resume_data, tmp_path):
        output_path = render_html(
            minimal_resume_data,
            self.config.output_dir,
            self.config.output_filename,
            self.config.template_name,
            self.config.template_dir,
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
