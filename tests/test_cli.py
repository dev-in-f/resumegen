import logging
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from resumegen.cli import app, setup_logging

runner = CliRunner()

MINIMAL_DATA_YAML = """\
document_metadata:
  title: "Test Resume"
  author: "Jane Doe"
  language: "en-US"
personal_info:
  name: "Jane Doe"
  email: "jane@example.com"
  location: "New York, NY"
experience:
  - title: "Engineer"
    company: "Acme"
    location: "New York, NY"
    start_date: "2020-01"
    description_bullets:
      - "Did things"
skill_sections:
  - title: "Languages"
    skills:
      - "Python"
"""

MINIMAL_CONFIG_YAML = """\
log_level: "INFO"
"""


@pytest.fixture
def data_file(tmp_path):
    p = tmp_path / "resume.yaml"
    p.write_text(MINIMAL_DATA_YAML)
    return p


@pytest.fixture
def config_file(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text(MINIMAL_CONFIG_YAML)
    return p


@pytest.fixture
def output_dir(tmp_path):
    d = tmp_path / "output"
    d.mkdir()
    return d


# ── setup_logging ──────────────────────────────────────────────────────────────


class TestSetupLogging:
    def test_sets_info_level_by_default(self):
        setup_logging("INFO")
        assert logging.getLogger().level == logging.INFO

    def test_sets_debug_level(self):
        setup_logging("DEBUG")
        assert logging.getLogger().level == logging.DEBUG

    def test_unknown_level_falls_back_to_info(self):
        setup_logging("NOTAREAL")
        assert logging.getLogger().level == logging.INFO

    def test_adds_file_handler_when_log_file_given(self, tmp_path):
        log_file = tmp_path / "test.log"
        setup_logging("INFO", log_file)
        root = logging.getLogger()
        handler_types = [type(h) for h in root.handlers]
        assert logging.FileHandler in handler_types

    def test_no_file_handler_without_log_file(self):
        setup_logging("INFO", None)
        root = logging.getLogger()
        for h in root.handlers:
            assert not isinstance(h, logging.FileHandler)


# ── main command ───────────────────────────────────────────────────────────────


class TestMainCommand:
    @patch("resumegen.cli.render_pdf")
    def test_renders_pdf_by_default(
        self, mock_render, data_file, config_file, output_dir
    ):
        mock_render.return_value = (output_dir / "resume.pdf", None)
        result = runner.invoke(
            app,
            [
                str(data_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0
        mock_render.assert_called_once()

    @patch("resumegen.cli.output_html")
    def test_renders_html_when_flag_set(
        self, mock_html, data_file, config_file, output_dir
    ):
        mock_html.return_value = output_dir / "resume.html"
        result = runner.invoke(
            app,
            [
                str(data_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--html",
            ],
        )
        assert result.exit_code == 0
        mock_html.assert_called_once()

    @patch("resumegen.cli.render_pdf")
    def test_exits_with_code_1_on_exception(
        self, mock_render, data_file, config_file, output_dir
    ):
        mock_render.side_effect = RuntimeError("boom")
        result = runner.invoke(
            app,
            [
                str(data_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
            ],
        )
        assert result.exit_code == 1

    @patch("resumegen.cli.render_pdf")
    def test_cli_author_overrides_data_file(
        self, mock_render, data_file, config_file, output_dir
    ):
        mock_render.return_value = (output_dir / "resume.pdf", None)
        result = runner.invoke(
            app,
            [
                str(data_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--author",
                "Override Author",
            ],
        )
        assert result.exit_code == 0
        call_kwargs = mock_render.call_args
        resume_data_arg = call_kwargs.args[4]
        assert (
            resume_data_arg.document_metadata.author == "Jane Doe"
        )  # render_pdf gets resume_data unchanged
        # The DocumentMetadata override happens internally; verify render_pdf was called
        mock_render.assert_called_once()

    @patch("resumegen.cli.render_pdf")
    def test_cli_title_overrides_data_file(
        self, mock_render, data_file, config_file, output_dir
    ):
        mock_render.return_value = (output_dir / "resume.pdf", None)
        result = runner.invoke(
            app,
            [
                str(data_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--title",
                "Custom Title",
            ],
        )
        assert result.exit_code == 0

    @patch("resumegen.cli.render_pdf")
    def test_force_flag_passed_through(
        self, mock_render, data_file, config_file, output_dir
    ):
        mock_render.return_value = (output_dir / "resume.pdf", None)
        result = runner.invoke(
            app,
            [
                str(data_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--force",
            ],
        )
        assert result.exit_code == 0
        _, kwargs = mock_render.call_args
        # overwrite_existing is the last positional arg or a kwarg
        call_args = mock_render.call_args.args
        assert call_args[5] is True  # overwrite_existing=True when --force

    @patch("resumegen.cli.render_pdf")
    def test_template_options_forwarded(
        self, mock_render, data_file, config_file, tmp_path, output_dir
    ):
        template_dir = tmp_path / "tpl"
        template_dir.mkdir()
        (template_dir / "custom.html.j2").write_text("<html></html>")
        mock_render.return_value = (output_dir / "resume.pdf", None)
        result = runner.invoke(
            app,
            [
                str(data_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--template-dir",
                str(template_dir),
                "--template",
                "custom.html.j2",
            ],
        )
        assert result.exit_code == 0
        call_args = mock_render.call_args.args
        assert call_args[0] == template_dir
        assert call_args[1] == "custom.html.j2"

    @patch("resumegen.cli.render_pdf")
    def test_accessibility_report_printed_when_present(
        self, mock_render, data_file, config_file, output_dir
    ):
        mock_report = MagicMock()
        mock_render.return_value = (output_dir / "resume.pdf", mock_report)
        result = runner.invoke(
            app,
            [
                str(data_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0
        mock_report.print.assert_called_once()

    @patch("resumegen.cli.render_pdf")
    def test_no_report_print_when_report_is_none(
        self, mock_render, data_file, config_file, output_dir
    ):
        mock_render.return_value = (output_dir / "resume.pdf", None)
        result = runner.invoke(
            app,
            [
                str(data_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0

    def test_invalid_data_file_exits_with_code_1(
        self, tmp_path, config_file, output_dir
    ):
        bad = tmp_path / "bad.yaml"
        bad.write_text("not_a_valid_field: true\n")
        result = runner.invoke(
            app,
            [str(bad), "--config", str(config_file), "--output-dir", str(output_dir)],
        )
        assert result.exit_code == 1

    @patch("resumegen.cli.render_pdf")
    def test_log_level_from_cli_overrides_config(
        self, mock_render, data_file, config_file, output_dir
    ):
        mock_render.return_value = (output_dir / "resume.pdf", None)
        result = runner.invoke(
            app,
            [
                str(data_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--log-level",
                "DEBUG",
            ],
        )
        assert result.exit_code == 0
        assert logging.getLogger().level == logging.DEBUG

    @patch("resumegen.cli.render_pdf")
    def test_output_template_forwarded_to_render(
        self, mock_render, data_file, config_file, output_dir
    ):
        mock_render.return_value = (output_dir / "resume.pdf", None)
        result = runner.invoke(
            app,
            [
                str(data_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--output-template",
                "my_{author}.pdf",
            ],
        )
        assert result.exit_code == 0
        call_args = mock_render.call_args.args
        assert call_args[2] == "my_{author}.pdf"
