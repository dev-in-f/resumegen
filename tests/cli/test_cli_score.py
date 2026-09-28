from unittest.mock import patch

import litellm
import pytest
from click.testing import CliRunner

from resumegen.cli import app

runner = CliRunner()

VALID_SCORE_YAML = """\
score: 85
strengths:
  - Strong Python experience
gaps:
  - No Kubernetes experience
"""


class TestScoreCommand:
    @patch("resumegen._cli.score.score_master_data")
    def test_exits_with_code_1_when_no_model(
        self, mock_score, master_data_file, job_description_file, config_file
    ):
        result = runner.invoke(
            app,
            [
                "score",
                str(master_data_file),
                str(job_description_file),
                "--config",
                str(config_file),
            ],
            env={"RESUMEGEN_MODEL": ""},
        )
        assert result.exit_code == 1
        assert "No model specified" in result.output
        mock_score.assert_not_called()

    @patch("resumegen._cli.score.score_master_data")
    def test_prints_score_report(
        self, mock_score, master_data_file, job_description_file, config_file
    ):
        mock_score.return_value = VALID_SCORE_YAML
        result = runner.invoke(
            app,
            [
                "score",
                str(master_data_file),
                str(job_description_file),
                "--config",
                str(config_file),
                "--model",
                "gpt-4o",
            ],
        )
        assert result.exit_code == 0
        assert "85" in result.output
        assert "Strong Python experience" in result.output
        assert "No Kubernetes experience" in result.output

    @patch("resumegen._cli.score.score_master_data")
    def test_arguments_forwarded(
        self, mock_score, master_data_file, job_description_file, config_file
    ):
        mock_score.return_value = VALID_SCORE_YAML
        result = runner.invoke(
            app,
            [
                "score",
                str(job_description_file),
                str(master_data_file),
                "--config",
                str(config_file),
                "--model",
                "mymodel",
                "--base-url",
                "http://localhost:11434",
                "--max-tokens",
                "1234",
                "--track-cost",
            ],
        )
        assert result.exit_code == 0
        call_args = mock_score.call_args
        assert call_args.args[0] == master_data_file.read_text()
        assert call_args.args[1] == job_description_file.read_text()
        assert call_args.kwargs["model"] == "mymodel"
        assert call_args.kwargs["base_url"] == "http://localhost:11434"
        assert call_args.kwargs["max_tokens"] == 1234
        assert call_args.kwargs["track_cost"] is True

    @patch("resumegen._cli.score.score_master_data")
    def test_model_and_base_url_from_config_used_when_not_on_cli(
        self, mock_score, master_data_file, job_description_file, tmp_path
    ):
        config = tmp_path / "config_with_model.yaml"
        config.write_text("model: gpt-3.5-turbo\nbase_url: http://cfg.example\n")
        mock_score.return_value = VALID_SCORE_YAML
        result = runner.invoke(
            app,
            [
                "score",
                str(master_data_file),
                str(job_description_file),
                "--config",
                str(config),
            ],
            env={"RESUMEGEN_MODEL": "", "RESUMEGEN_BASE_URL": ""},
        )
        assert result.exit_code == 0
        assert mock_score.call_args.kwargs["model"] == "gpt-3.5-turbo"
        assert mock_score.call_args.kwargs["base_url"] == "http://cfg.example"

    @patch("resumegen._cli.score.score_master_data")
    def test_invalid_score_report_exits_with_code_1(
        self, mock_score, master_data_file, job_description_file, config_file
    ):
        mock_score.return_value = "score: 150\n"
        result = runner.invoke(
            app,
            [
                "score",
                str(master_data_file),
                str(job_description_file),
                "--config",
                str(config_file),
                "--model",
                "gpt-4o",
            ],
        )
        assert result.exit_code == 1
        assert "Data model validation failed" in result.output

    @pytest.mark.parametrize(
        ("error", "message"),
        [
            (
                litellm.BadRequestError("Bad request", "model", "provider"),
                "bad request",
            ),
            (litellm.Timeout("Request timed out", "model", "provider"), "timed out"),
            (
                litellm.RateLimitError("Rate limit exceeded", "model", "provider"),
                "rate limit exceeded",
            ),
            (
                litellm.BudgetExceededError(10, 1, "Budget exceeded"),
                "budget exceeded",
            ),
            (
                litellm.APIError(500, "API error occurred", "provider", "model"),
                "Language model API error",
            ),
            (RuntimeError("boom"), "Unexpected error during scoring"),
        ],
    )
    def test_errors_exit_with_code_1(
        self, error, message, master_data_file, job_description_file, config_file
    ):
        with patch("resumegen._cli.score.score_master_data", side_effect=error):
            result = runner.invoke(
                app,
                [
                    "score",
                    str(master_data_file),
                    str(job_description_file),
                    "--config",
                    str(config_file),
                    "--model",
                    "gpt-4o",
                ],
            )
        assert result.exit_code == 1
        assert message in result.output
