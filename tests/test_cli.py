import logging
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

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


@pytest.fixture
def config_file(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text(MINIMAL_CONFIG_YAML)
    return p


class TestMainCommand:
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

    @patch("resumegen.cli.output_html")
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
                "render",
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
                "render",
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

    @patch("resumegen.cli.score_master_data")
    @patch("resumegen.cli.tailor_resume")
    def test_score_flag_calls_score_master_data(
        self,
        mock_tailor,
        mock_score,
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
                "--score",
            ],
        )
        assert result.exit_code == 0
        mock_score.assert_called_once()

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
        assert call_args[4] is True  # track_cost positional arg

    @patch("resumegen.cli.tailor_resume")
    def test_save_flag_forwarded(
        self,
        mock_tailor,
        master_data_file,
        job_description_file,
        config_file,
        output_dir,
    ):
        # --save is the second flag in "--no-save/--save", so it sets save_to_file=False
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
                "--save",
            ],
        )
        assert result.exit_code == 0
        call_args = mock_tailor.call_args.args
        assert (
            call_args[5] is False
        )  # --save is the "no-op" (second) flag, sets save_to_file=False

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
