from unittest.mock import patch

import litellm
import pydantic
from click.testing import CliRunner

from resumegen.cli import app

runner = CliRunner()


class TestTailorCommand:
    @patch("resumegen._cli.tailor.tailor_resume")
    def test_basic_tailor_call(
        self,
        mock_tailor,
        master_data_file,
        job_description_file,
        config_file,
        output_dir,
    ):
        mock_tailor.return_value = ("raw yaml content", output_dir / "tailored.yaml")
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

    @patch("resumegen._cli.tailor.tailor_resume")
    def test_track_cost_flag_forwarded(
        self,
        mock_tailor,
        master_data_file,
        job_description_file,
        config_file,
        output_dir,
    ):
        mock_tailor.return_value = ("raw yaml content", output_dir / "tailored.yaml")
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
        _, _kwargs = mock_tailor.call_args
        call_args = mock_tailor.call_args.args
        assert call_args[6] is True

    @patch("resumegen._cli.tailor.tailor_resume")
    def test_save_flag_forwarded(
        self,
        mock_tailor,
        master_data_file,
        job_description_file,
        config_file,
        output_dir,
    ):
        mock_tailor.return_value = ("raw yaml content", None)
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
        assert call_args[7] is False

    @patch("resumegen._cli.tailor.tailor_resume")
    def test_job_title_forwarded(
        self,
        mock_tailor,
        master_data_file,
        job_description_file,
        config_file,
        output_dir,
    ):
        mock_tailor.return_value = ("raw yaml content", output_dir / "tailored.yaml")
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
        assert call_args[5] == "Senior Engineer"

    @patch("resumegen._cli.tailor.tailor_resume")
    def test_output_filename_forwarded(
        self,
        mock_tailor,
        master_data_file,
        job_description_file,
        config_file,
        output_dir,
    ):
        mock_tailor.return_value = ("raw yaml content", output_dir / "tailored.yaml")
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

    @patch("resumegen._cli.tailor.tailor_resume")
    def test_output_template_with_dir_nests_under_output_dir(
        self,
        mock_tailor,
        master_data_file,
        job_description_file,
        config_file,
        output_dir,
        tmp_path,
    ):
        mock_tailor.return_value = ("raw yaml content", output_dir / "tailored.yaml")
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
                "--output-template",
                "{job_title}/custom_{date}.yaml",
            ],
        )
        assert result.exit_code == 0
        call_args = mock_tailor.call_args.args
        assert call_args[2] == output_dir
        assert call_args[8] == "{job_title}/custom_{date}.yaml"

    @patch("resumegen._cli.tailor.tailor_resume")
    def test_no_interactive_save_prints_content_and_saves(
        self,
        mock_tailor,
        master_data_file,
        job_description_file,
        config_file,
        output_dir,
    ):
        mock_tailor.return_value = ("raw yaml content", output_dir / "tailored.yaml")
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
                "--no-interactive",
                "--save",
            ],
        )
        assert result.exit_code == 0
        assert mock_tailor.call_args.args[7] is True  # save_to_file
        assert result.output.strip() == "raw yaml content"

    @patch("resumegen._cli.tailor.tailor_resume")
    def test_no_interactive_no_save_prints_content_only(
        self,
        mock_tailor,
        master_data_file,
        job_description_file,
        config_file,
        output_dir,
    ):
        mock_tailor.return_value = ("raw yaml content", None)
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
                "--no-interactive",
                "--no-save",
            ],
        )
        assert result.exit_code == 0
        assert mock_tailor.call_args.args[7] is False  # save_to_file
        assert result.output.strip() == "raw yaml content"

    @patch("resumegen._cli.tailor.tailor_resume")
    def test_feedback_flag_forwarded_and_rationale_printed(
        self,
        mock_tailor,
        master_data_file,
        job_description_file,
        config_file,
        output_dir,
    ):
        mock_tailor.return_value = (
            "name: Jane\n# picked this because of X\nrole: Engineer\n",
            output_dir / "tailored.yaml",
        )
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
                "--feedback",
            ],
        )
        assert result.exit_code == 0
        call_args = mock_tailor.call_args.args
        assert call_args[10] is True
        assert "Tailoring rationale" in result.output
        assert "picked this because of X" in result.output

    @patch("resumegen._cli.tailor.tailor_resume")
    def test_no_feedback_flag_omits_rationale_output(
        self,
        mock_tailor,
        master_data_file,
        job_description_file,
        config_file,
        output_dir,
    ):
        mock_tailor.return_value = ("raw yaml content", output_dir / "tailored.yaml")
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
        call_args = mock_tailor.call_args.args
        assert call_args[10] is False
        assert "Tailoring rationale" not in result.output

    @patch("resumegen._cli.tailor.tailor_resume")
    def test_base_url_forwarded(
        self,
        mock_tailor,
        master_data_file,
        job_description_file,
        config_file,
        output_dir,
    ):
        mock_tailor.return_value = ("raw yaml content", output_dir / "tailored.yaml")
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
        assert call_args[4] == "http://localhost:11434"

    @patch("resumegen._cli.tailor.tailor_resume")
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

    @patch("resumegen._cli.tailor.tailor_resume")
    def test_model_from_config_used_when_not_on_cli(
        self, mock_tailor, master_data_file, job_description_file, tmp_path, output_dir
    ):
        config = tmp_path / "config_with_model.yaml"
        config.write_text("model: gpt-3.5-turbo\n")
        mock_tailor.return_value = ("raw yaml content", output_dir / "tailored.yaml")
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
            "resumegen._cli.tailor.tailor_resume",
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

    def test_bad_request_error_exits_with_code_1(
        self, master_data_file, job_description_file, config_file, output_dir
    ):
        with patch(
            "resumegen._cli.tailor.tailor_resume",
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
            "resumegen._cli.tailor.tailor_resume",
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
            "resumegen._cli.tailor.tailor_resume",
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
            "resumegen._cli.tailor.tailor_resume",
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
            "resumegen._cli.tailor.tailor_resume",
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
            "resumegen._cli.tailor.tailor_resume",
            side_effect=RuntimeError("Unexpected error"),
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
