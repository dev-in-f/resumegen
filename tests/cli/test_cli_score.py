from unittest.mock import patch

from click.testing import CliRunner

from resumegen.cli import app

runner = CliRunner()


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
