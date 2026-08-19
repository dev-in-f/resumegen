from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from resumegen.cli import app
from resumegen.config import Config, OutputConfig

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def test_command_args(complete_test_setup):
    env = complete_test_setup
    return [
        "--data",
        str(env["data_file"]),
        "--output-dir",
        str(env["output_dir"]),
        "--template-dir",
        str(env["templates_dir"]),
    ]


@pytest.fixture
def complete_test_setup(tmp_path):
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    template_file = templates_dir / "template.html.j2"
    template_file.write_text((FIXTURES_DIR / "test_template.html.j2").read_text())

    data_file = tmp_path / "resume_data.yaml"
    data_file.write_text((FIXTURES_DIR / "test_resume_data.yaml").read_text())

    return {
        "tmp_path": tmp_path,
        "data_file": data_file,
        "templates_dir": templates_dir,
        "output_dir": output_dir,
        "template_file": template_file,
    }


def test_cli_no_args(runner):
    result = runner.invoke(app)
    assert result.exit_code == 2
    assert "Missing command" in result.output


def test_default_command_rejects_args(runner):
    result = runner.invoke(app, ["default", "--config", "test.yaml"])
    assert result.exit_code == 2
    assert "No such option" in result.output


def test_generate_no_args_abort(runner):
    with patch("resumegen.cli.typer.confirm", return_value=False):
        result = runner.invoke(app, ["generate"])

    assert result.exit_code == 1
    assert "Aborting" in result.output


def test_default_command(runner, complete_test_setup):
    env = complete_test_setup
    templates_dir = env["templates_dir"]
    data_file = env["data_file"]
    output_dir = env["output_dir"]

    with patch(
        "resumegen.cli.AppConfig",
        lambda **kwargs: Config(
            template_dir=templates_dir,
            data_file=data_file,
            output_config=OutputConfig(output_dir=output_dir),
            **kwargs,
        ),
    ):
        result = runner.invoke(app, ["default"])
    assert result.exit_code == 0


def test_confirm_default_no_args(runner):
    with (
        patch("resumegen.cli.typer.confirm", return_value=True),
        patch("resumegen.cli.default") as mock_default,
    ):
        result = runner.invoke(app, ["generate"])

        mock_default.assert_called_once()
    assert result.exit_code == 0


def test_log_file_arg_creates_log_file(runner, tmp_path, test_command_args):
    log_file = tmp_path / "test.log"

    result = runner.invoke(
        app,
        [
            "generate",
            *test_command_args,
            "--log-file",
            str(log_file),
        ],
    )

    assert result.exit_code == 0
    assert log_file.exists()
    assert log_file.stat().st_size > 0


def test_log_file_config_creates_log_file(runner, tmp_path, test_command_args):
    log_file = tmp_path / "config.log"
    app_config_text = f"""
        logging_config:
            file: {log_file}
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(app_config_text)
    assert not log_file.exists()
    result = runner.invoke(
        app,
        [
            "generate",
            "-c",
            str(config_file),
            *test_command_args,
        ],
    )

    assert result.exit_code == 0
    assert log_file.exists()
    assert log_file.stat().st_size > 0


def test_generate_creates_pdf_in_tmp(runner, test_command_args):
    with patch("resumegen.cli.render_pdf") as mock_pdf:
        mock_pdf.return_value = Path("/tmp/output.pdf")

        result = runner.invoke(
            app,
            [
                "generate",
                *test_command_args,
            ],
        )

    assert result.exit_code == 0
    mock_pdf.assert_called_once()
    assert mock_pdf.call_args.kwargs["scan_pdf_accessibility"] is True


def test_generate_html_only_in_tmp(runner, test_command_args):

    with (
        patch("resumegen.cli.output_html") as mock_html,
        patch("resumegen.cli.render_pdf") as mock_pdf,
    ):
        result = runner.invoke(
            app,
            [
                "generate",
                *test_command_args,
                "--html",
            ],
        )

    assert result.exit_code == 0
    mock_html.assert_called_once()
    mock_pdf.assert_not_called()


def test_generate_with_force_flag(runner, test_command_args):
    with patch("resumegen.cli.render_pdf") as mock_pdf:
        mock_pdf.return_value = Path("/tmp/output.pdf")

        result = runner.invoke(
            app,
            [
                "generate",
                *test_command_args,
                "--force",
            ],
        )

    assert result.exit_code == 0

    app_config = mock_pdf.call_args[0][0]
    assert app_config.output_config.overwrite is True


def test_generate_with_custom_template(runner, tmp_path, test_command_args):
    custom_template = tmp_path / "custom.html.j2"
    custom_template.write_text("<html><body>Custom</body></html>")

    with patch("resumegen.cli.render_pdf") as mock_pdf:
        mock_pdf.return_value = Path("/tmp/output.pdf")

        result = runner.invoke(
            app,
            [
                "generate",
                *test_command_args,
                "--template",
                str(custom_template),
            ],
        )

    assert result.exit_code == 0, f"Failed: {result.output}"
    mock_pdf.assert_called_once()


def test_generate_to_custom_output_dir(runner, complete_test_setup):
    env = complete_test_setup

    custom_output = env["tmp_path"] / "custom_output"
    custom_output.mkdir()

    with patch("resumegen.cli.render_pdf") as mock_pdf:
        mock_pdf.return_value = custom_output / "resume.pdf"

        result = runner.invoke(
            app,
            [
                "generate",
                "--data",
                str(env["data_file"]),
                "--output-dir",
                str(custom_output),
                "--template-dir",
                str(env["templates_dir"]),
            ],
        )

    assert result.exit_code == 0, f"Failed: {result.output}"

    # Verify output dir passed via app config matches the custom directory
    app_config = mock_pdf.call_args[0][0]
    assert app_config.output_config.output_dir == custom_output.resolve()


def test_cli_validates_nonexistent_data_file(runner, complete_test_setup):
    env = complete_test_setup

    result = runner.invoke(
        app,
        [
            "generate",
            "--data",
            str(env["tmp_path"] / "nonexistent.yaml"),
            "--output-dir",
            str(env["output_dir"]),
            "--template-dir",
            str(env["templates_dir"]),
        ],
    )

    # Typer validation should fail
    assert result.exit_code != 0
