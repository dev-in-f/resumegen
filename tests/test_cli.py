import logging
from unittest.mock import MagicMock, patch

import litellm
import pydantic
import pytest
from click.testing import CliRunner

from resumegen._core.exceptions import PdfError, RenderError
from resumegen.cli import _override_logging_options, app

runner = CliRunner()

MINIMAL_CONFIG_YAML = """\
template_dir: "templates"
"""


class TestLoggingOverrides:
    def test_logging_level_cli_overrides(self):
        logging.getLogger("resumegen.cli").setLevel(logging.WARNING)
        _override_logging_options("INFO", None)
        assert logging.getLogger("resumegen.cli").getEffectiveLevel() == logging.INFO

    def test_logging_file_cli_overrides(self, tmp_path):
        log_file = tmp_path / "test.log"
        _override_logging_options(None, log_file)
        logger = logging.getLogger("resumegen.cli")
        logger.info("Test message")
        with open(log_file) as f:
            content = f.read()
        assert "Test message" in content

    def test_logging_removes_handler_set_previously(self, tmp_path):
        log_file1 = tmp_path / "test1.log"
        log_file2 = tmp_path / "test2.log"
        _override_logging_options(None, log_file1)
        logger = logging.getLogger("resumegen.cli")
        logger.info("Message 1")
        _override_logging_options(None, log_file2)
        logger.info("Message 2")
        with open(log_file1) as f1, open(log_file2) as f2:
            content1 = f1.read()
            content2 = f2.read()
        assert "Message 1" in content1
        assert "Message 2" in content2

    def test_logging_overrides_verbose(self):
        logging.getLogger("resumegen.cli").setLevel(logging.WARNING)
        _override_logging_options(None, None, verbose=True)
        assert logging.getLogger("resumegen.cli").getEffectiveLevel() == logging.DEBUG


@pytest.fixture
def config_file(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text(MINIMAL_CONFIG_YAML)
    return p


class TestRenderCommand:
    @patch("resumegen.cli.render_pdf")
    def test_renders_pdf_by_default(
        self, mock_render, data_file, config_file, output_dir
    ):
        mock_render.return_value = (output_dir / "resume.pdf", None)
        result = runner.invoke(
            app,
            [
                "render",
                str(data_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0
        mock_render.assert_called_once()

    @patch("resumegen.cli.render_html")
    def test_renders_html_when_flag_set(
        self, mock_html, data_file, config_file, output_dir
    ):
        mock_html.return_value = output_dir / "resume.html"
        result = runner.invoke(
            app,
            [
                "render",
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
                "render",
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
                "render",
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
        resume_data_arg = call_kwargs.args[0]
        assert resume_data_arg.document_metadata.author == "Jane Doe"
        mock_render.assert_called_once()

    @patch("resumegen.cli.render_pdf")
    def test_cli_title_overrides_data_file(
        self, mock_render, data_file, config_file, output_dir
    ):
        mock_render.return_value = (output_dir / "resume.pdf", None)
        result = runner.invoke(
            app,
            [
                "render",
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
                "render",
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
        call_args = mock_render.call_args.args
        assert call_args[5] is True

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
                "render",
                str(data_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--template-dir",
                str(template_dir),
                "--template-name",
                "custom.html.j2",
            ],
        )
        assert result.exit_code == 0
        call_args = mock_render.call_args.args
        assert call_args[3] == "custom.html.j2"
        assert call_args[4] == template_dir

    @patch("resumegen.cli.render_pdf")
    def test_no_report_print_when_report_is_none(
        self, mock_render, data_file, config_file, output_dir
    ):
        mock_render.return_value = (output_dir / "resume.pdf", None)
        result = runner.invoke(
            app,
            [
                "render",
                str(data_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0

    def test_report_printed_when_report_is_not_none(
        self, data_file, config_file, output_dir
    ):
        class DummyReport:
            def get_report_string(self):
                return "Accessibility report content"

        with patch(
            "resumegen.cli.render_pdf",
            return_value=(output_dir / "resume.pdf", DummyReport()),
        ):
            result = runner.invoke(
                app,
                [
                    "render",
                    str(data_file),
                    "--config",
                    str(config_file),
                    "--output-dir",
                    str(output_dir),
                ],
            )
            assert result.exit_code == 0
            assert "Accessibility report:" in result.output

    def test_invalid_data_file_exits_with_code_1(
        self, tmp_path, config_file, output_dir
    ):
        bad = tmp_path / "bad.yaml"
        bad.write_text("not_a_valid_field: true\n")
        result = runner.invoke(
            app,
            [
                "render",
                str(bad),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
            ],
        )
        assert result.exit_code == 1

    @patch("resumegen.cli.render_pdf")
    def test_output_template_forwarded_to_render(
        self, mock_render, data_file, config_file, output_dir
    ):
        mock_render.return_value = (output_dir / "resume.pdf", None)
        result = runner.invoke(
            app,
            [
                "render",
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

    def test_validation_error_exits_with_code_1(self, tmp_path, config_file):
        bad_data = tmp_path / "bad_data.yaml"
        bad_data.write_text("invalid_field: true\n")
        result = runner.invoke(
            app,
            [
                "render",
                str(bad_data),
                "--config",
                str(config_file),
            ],
        )
        assert result.exit_code == 1
        assert "Data model validation failed" in result.output

    def test_pdf_error_exits_with_code_1(self, tmp_path, config_file, data_file):
        with patch("resumegen.cli.render_pdf", side_effect=PdfError("PDF error")):
            result = runner.invoke(
                app,
                [
                    "render",
                    str(data_file),
                    "--config",
                    str(config_file),
                ],
            )
            assert result.exit_code == 1
            assert "PDF manipulation failed" in result.output

    def test_render_error_exits_with_code_1(self, tmp_path, config_file, data_file):
        with patch("resumegen.cli.render_pdf", side_effect=RenderError("Render error")):
            result = runner.invoke(
                app,
                [
                    "render",
                    str(data_file),
                    "--config",
                    str(config_file),
                ],
            )
            assert result.exit_code == 1
            assert "Rendering failed" in result.output

    def test_unexpected_exception_exits_with_code_1(
        self, tmp_path, config_file, data_file
    ):
        with patch("resumegen.cli.render_pdf", side_effect=RuntimeError("Unexpected")):
            result = runner.invoke(
                app,
                [
                    "render",
                    str(data_file),
                    "--config",
                    str(config_file),
                ],
            )
            assert result.exit_code == 1
            assert "Unexpected error" in result.output


class TestTailorCommand:
    @patch("resumegen.cli.tailor_resume")
    def test_basic_tailor_call(
        self,
        mock_tailor,
        master_data_file,
        job_description_file,
        config_file,
        output_dir,
    ):
        mock_tailor.return_value = output_dir / "tailored.yaml"
        result = runner.invoke(
            app,
            [
                "tailor",
                str(master_data_file),
                str(job_description_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--model",
                "gpt-4o",
            ],
        )
        assert result.exit_code == 0
        mock_tailor.assert_called_once()

    @patch("resumegen.cli.tailor_resume")
    def test_track_cost_flag_forwarded(
        self,
        mock_tailor,
        master_data_file,
        job_description_file,
        config_file,
        output_dir,
    ):
        mock_tailor.return_value = output_dir / "tailored.yaml"
        result = runner.invoke(
            app,
            [
                "tailor",
                str(master_data_file),
                str(job_description_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--model",
                "gpt-4o",
                "--track-cost",
            ],
        )
        assert result.exit_code == 0
        _, kwargs = mock_tailor.call_args
        call_args = mock_tailor.call_args.args
        assert call_args[4] is True

    @patch("resumegen.cli.tailor_resume")
    def test_save_flag_forwarded(
        self,
        mock_tailor,
        master_data_file,
        job_description_file,
        config_file,
        output_dir,
    ):
        mock_tailor.return_value = "raw yaml content"
        result = runner.invoke(
            app,
            [
                "tailor",
                str(master_data_file),
                str(job_description_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--model",
                "gpt-4o",
                "--no-save",
            ],
        )
        assert result.exit_code == 0
        call_args = mock_tailor.call_args.args
        assert call_args[5] is False

    @patch("resumegen.cli.tailor_resume")
    def test_job_title_forwarded(
        self,
        mock_tailor,
        master_data_file,
        job_description_file,
        config_file,
        output_dir,
    ):
        mock_tailor.return_value = output_dir / "tailored.yaml"
        result = runner.invoke(
            app,
            [
                "tailor",
                str(master_data_file),
                str(job_description_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--model",
                "gpt-4o",
                "--job-title",
                "Senior Engineer",
            ],
        )
        assert result.exit_code == 0
        call_args = mock_tailor.call_args.args
        assert call_args[6] == "Senior Engineer"

    @patch("resumegen.cli.tailor_resume")
    def test_output_filename_forwarded(
        self,
        mock_tailor,
        master_data_file,
        job_description_file,
        config_file,
        output_dir,
    ):
        mock_tailor.return_value = output_dir / "tailored.yaml"
        result = runner.invoke(
            app,
            [
                "tailor",
                str(master_data_file),
                str(job_description_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--model",
                "gpt-4o",
                "-o",
                "custom_{date}.yaml",
            ],
        )
        assert result.exit_code == 0
        call_args = mock_tailor.call_args.args
        assert call_args[8] == "custom_{date}.yaml"

    @patch("resumegen.cli.tailor_resume")
    def test_base_url_forwarded(
        self,
        mock_tailor,
        master_data_file,
        job_description_file,
        config_file,
        output_dir,
    ):
        mock_tailor.return_value = output_dir / "tailored.yaml"
        result = runner.invoke(
            app,
            [
                "tailor",
                str(master_data_file),
                str(job_description_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--model",
                "mymodel",
                "--base-url",
                "http://localhost:11434",
            ],
        )
        assert result.exit_code == 0
        call_args = mock_tailor.call_args.args
        assert call_args[7] == "http://localhost:11434"

    @patch("resumegen.cli.tailor_resume")
    def test_exits_with_code_1_on_exception(
        self,
        mock_tailor,
        master_data_file,
        job_description_file,
        config_file,
        output_dir,
    ):
        mock_tailor.side_effect = RuntimeError("tailoring failed")
        result = runner.invoke(
            app,
            [
                "tailor",
                str(master_data_file),
                str(job_description_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--model",
                "gpt-4o",
            ],
        )
        assert result.exit_code == 1

    @patch("resumegen.cli.tailor_resume")
    def test_model_from_config_used_when_not_on_cli(
        self, mock_tailor, master_data_file, job_description_file, tmp_path, output_dir
    ):
        config = tmp_path / "config_with_model.yaml"
        config.write_text("model: gpt-3.5-turbo\n")
        mock_tailor.return_value = output_dir / "tailored.yaml"
        result = runner.invoke(
            app,
            [
                "tailor",
                str(master_data_file),
                str(job_description_file),
                "--config",
                str(config),
                "--output-dir",
                str(output_dir),
            ],
            env={"RESUMEGEN_MODEL": ""},
        )
        assert result.exit_code == 0
        call_args = mock_tailor.call_args.args
        assert call_args[3] == "gpt-3.5-turbo"

    def test_validation_error_exits_with_code_1(
        self, master_data_file, job_description_file, config_file, output_dir
    ):
        with patch(
            "resumegen.cli.tailor_resume",
            side_effect=pydantic.ValidationError("Validation failed", []),
        ):
            result = runner.invoke(
                app,
                [
                    "tailor",
                    str(master_data_file),
                    str(job_description_file),
                    "--config",
                    str(config_file),
                    "--output-dir",
                    str(output_dir),
                    "--model",
                    "gpt-4o",
                ],
            )
            assert result.exit_code == 1
            assert "Validation failed" in result.output

    def test_value_error_exits_with_code_1(
        self,
        master_data_file,
        job_description_file,
        config_file,
        output_dir,
        monkeypatch,
    ):
        monkeypatch.setenv("RESUMEGEN_MODEL", "")
        result = runner.invoke(
            app,
            [
                "tailor",
                str(master_data_file),
                str(job_description_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--model",
                "",
            ],
        )
        assert result.exit_code == 1
        assert "Tailoring failed:" in result.output

    def test_bad_request_error_exits_with_code_1(
        self, master_data_file, job_description_file, config_file, output_dir
    ):
        with patch(
            "resumegen.cli.tailor_resume",
            side_effect=litellm.BadRequestError("Bad request", "model", "provider"),
        ):
            result = runner.invoke(
                app,
                [
                    "tailor",
                    str(master_data_file),
                    str(job_description_file),
                    "--config",
                    str(config_file),
                    "--output-dir",
                    str(output_dir),
                    "--model",
                    "gpt-4o",
                ],
            )
            assert result.exit_code == 1
            assert "Bad request" in result.output

    def test_timeout_error_exits_with_code_1(
        self, master_data_file, job_description_file, config_file, output_dir
    ):
        with patch(
            "resumegen.cli.tailor_resume",
            side_effect=litellm.Timeout("Request timed out", "model", "provider"),
        ):
            result = runner.invoke(
                app,
                [
                    "tailor",
                    str(master_data_file),
                    str(job_description_file),
                    "--config",
                    str(config_file),
                    "--output-dir",
                    str(output_dir),
                    "--model",
                    "gpt-4o",
                ],
            )
            assert result.exit_code == 1
            assert "request timed out" in result.output

    def test_rate_limit_error_exits_with_code_1(
        self, master_data_file, job_description_file, config_file, output_dir
    ):
        with patch(
            "resumegen.cli.tailor_resume",
            side_effect=litellm.RateLimitError(
                "Rate limit exceeded", "model", "provider"
            ),
        ):
            result = runner.invoke(
                app,
                [
                    "tailor",
                    str(master_data_file),
                    str(job_description_file),
                    "--config",
                    str(config_file),
                    "--output-dir",
                    str(output_dir),
                    "--model",
                    "gpt-4o",
                ],
            )
            assert result.exit_code == 1
            assert "rate limit exceeded" in result.output

    def test_budget_exceeded_error_exits_with_code_1(
        self, master_data_file, job_description_file, config_file, output_dir
    ):
        with patch(
            "resumegen.cli.tailor_resume",
            side_effect=litellm.BudgetExceededError(10, 1, "Budget exceeded"),
        ):
            result = runner.invoke(
                app,
                [
                    "tailor",
                    str(master_data_file),
                    str(job_description_file),
                    "--config",
                    str(config_file),
                    "--output-dir",
                    str(output_dir),
                    "--model",
                    "gpt-4o",
                ],
            )
            assert result.exit_code == 1
            assert "budget exceeded" in result.output

    def test_api_error_exits_with_code_1(
        self, master_data_file, job_description_file, config_file, output_dir
    ):
        with patch(
            "resumegen.cli.tailor_resume",
            side_effect=litellm.APIError(
                500, "API error occurred", "provider", "model"
            ),
        ):
            result = runner.invoke(
                app,
                [
                    "tailor",
                    str(master_data_file),
                    str(job_description_file),
                    "--config",
                    str(config_file),
                    "--output-dir",
                    str(output_dir),
                    "--model",
                    "gpt-4o",
                ],
            )
            assert result.exit_code == 1
            assert "API error" in result.output

    def test_exception_exits_with_code_1(
        self, master_data_file, job_description_file, config_file, output_dir
    ):
        with patch(
            "resumegen.cli.tailor_resume", side_effect=RuntimeError("Unexpected error")
        ):
            result = runner.invoke(
                app,
                [
                    "tailor",
                    str(master_data_file),
                    str(job_description_file),
                    "--config",
                    str(config_file),
                    "--output-dir",
                    str(output_dir),
                    "--model",
                    "gpt-4o",
                ],
            )
            assert result.exit_code == 1
            assert "Unexpected error" in result.output


class TestScanPdfCommand:
    @patch("resumegen.cli.scan_accessibility")
    @patch("resumegen.cli.pikepdf.open")
    def test_scan_pdf_command(self, mock_pikepdf_open, mock_scan, tmp_path):
        mock_pikepdf_open.return_value.__enter__.return_value = MagicMock()
        mock_scan.return_value.get_report_string.return_value = (
            "Accessibility report content"
        )
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n%EOF")
        result = runner.invoke(
            app,
            [
                "scan-pdf",
                str(pdf_file),
            ],
        )
        assert result.exit_code == 0
        mock_scan.assert_called_once()
        assert "Accessibility report content" in result.output

    def test_scan_pdf_command_exits_with_code_1_on_exception(self, tmp_path):
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n%EOF")
        with (
            patch(
                "resumegen.cli.scan_accessibility",
                side_effect=RuntimeError("Scan failed"),
            ),
            patch("resumegen.cli.pikepdf.open") as mock_pikepdf_open,
        ):
            mock_pikepdf_open.return_value.__enter__.return_value = MagicMock()
            result = runner.invoke(
                app,
                [
                    "scan-pdf",
                    str(pdf_file),
                ],
            )
            assert result.exit_code == 1
            assert "Scan failed" in result.output

    def test_scan_pdf_command_exits_with_code_1_on_pdf_error(self, tmp_path):
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n%EOF")
        with (
            patch(
                "resumegen.cli.scan_accessibility", side_effect=PdfError("PDF error")
            ),
            patch("resumegen.cli.pikepdf.open") as mock_pikepdf_open,
        ):
            mock_pikepdf_open.return_value.__enter__.return_value = MagicMock()
            result = runner.invoke(
                app,
                [
                    "scan-pdf",
                    str(pdf_file),
                ],
            )
            assert result.exit_code == 1
            assert "PDF accessibility scan failed" in result.output
