from unittest.mock import patch

import pytest
from click.testing import CliRunner

from resumegen._core.exceptions import RenderError
from resumegen.cli import app

runner = CliRunner()


@pytest.fixture
def html_file(tmp_path):
    p = tmp_path / "resume.html"
    p.write_text("<html><body><p>Jane Doe</p></body></html>")
    return p


@pytest.fixture
def template_dir(tmp_path):
    d = tmp_path / "tpl"
    d.mkdir()
    return d


@pytest.fixture
def convert_config_file(tmp_path, template_dir):
    (tmp_path / "cfg_out").mkdir()
    p = tmp_path / "convert_config.yaml"
    p.write_text(f"template_dir: {template_dir}\noutput_dir: {tmp_path / 'cfg_out'}\n")
    return p


class TestConvertHtmlCommand:
    @patch("resumegen._cli.convert_html.render_pdf_from_html")
    def test_interactive_prints_decorated_path(
        self, mock_render, html_file, convert_config_file, output_dir
    ):
        output_path = output_dir / "resume.pdf"
        mock_render.return_value = output_path
        result = runner.invoke(
            app,
            [
                "convert-html",
                str(html_file),
                "--config",
                str(convert_config_file),
                "--output-dir",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0
        assert "Configuration loaded successfully" in result.output
        assert f"PDF generated at: {output_path.resolve()}" in result.output

    @patch("resumegen._cli.convert_html.render_pdf_from_html")
    def test_no_interactive_prints_bare_path(
        self, mock_render, html_file, convert_config_file, output_dir
    ):
        output_path = output_dir / "resume.pdf"
        mock_render.return_value = output_path
        result = runner.invoke(
            app,
            [
                "convert-html",
                str(html_file),
                "--config",
                str(convert_config_file),
                "--output-dir",
                str(output_dir),
                "--no-interactive",
            ],
        )
        assert result.exit_code == 0
        assert result.output.strip() == str(output_path.resolve())

    @patch("resumegen._cli.convert_html.render_pdf_from_html")
    def test_assets_dir_defaults_to_config_template_dir(
        self, mock_render, html_file, convert_config_file, template_dir, output_dir
    ):
        mock_render.return_value = output_dir / "resume.pdf"
        result = runner.invoke(
            app,
            [
                "convert-html",
                str(html_file),
                "--config",
                str(convert_config_file),
                "--output-dir",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0
        assert mock_render.call_args.args[1] == template_dir

    @patch("resumegen._cli.convert_html.render_pdf_from_html")
    def test_assets_dir_option_forwarded(
        self, mock_render, html_file, convert_config_file, tmp_path, output_dir
    ):
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        mock_render.return_value = output_dir / "resume.pdf"
        result = runner.invoke(
            app,
            [
                "convert-html",
                str(html_file),
                "--config",
                str(convert_config_file),
                "--output-dir",
                str(output_dir),
                "--assets-dir",
                str(assets_dir),
            ],
        )
        assert result.exit_code == 0
        assert mock_render.call_args.args[1] == assets_dir

    @patch("resumegen._cli.convert_html.render_pdf_from_html")
    def test_output_dir_and_name_forwarded(
        self, mock_render, html_file, convert_config_file, output_dir
    ):
        mock_render.return_value = output_dir / "custom.pdf"
        result = runner.invoke(
            app,
            [
                "convert-html",
                str(html_file),
                "--config",
                str(convert_config_file),
                "--output-dir",
                str(output_dir),
                "-o",
                "custom.pdf",
                "--force",
            ],
        )
        assert result.exit_code == 0
        call_args = mock_render.call_args.args
        assert call_args[0] == html_file
        assert call_args[2] == output_dir
        assert call_args[3] == "custom.pdf"
        assert call_args[4] is True

    @patch("resumegen._cli.convert_html.render_pdf_from_html")
    def test_output_name_with_dir_takes_precedence_over_output_dir(
        self, mock_render, html_file, convert_config_file, tmp_path, output_dir
    ):
        mock_render.return_value = tmp_path / "nested" / "custom.pdf"
        result = runner.invoke(
            app,
            [
                "convert-html",
                str(html_file),
                "--config",
                str(convert_config_file),
                "--output-dir",
                str(output_dir),
                "-o",
                str(tmp_path / "nested" / "custom.pdf"),
            ],
        )
        assert result.exit_code == 0
        call_args = mock_render.call_args.args
        assert call_args[2] == tmp_path / "nested"
        assert call_args[3] == "custom.pdf"

    @patch("resumegen._cli.convert_html.render_pdf_from_html")
    def test_output_dir_falls_back_to_config(
        self, mock_render, html_file, convert_config_file, tmp_path
    ):
        mock_render.return_value = tmp_path / "cfg_out" / "resume.pdf"
        result = runner.invoke(
            app,
            [
                "convert-html",
                str(html_file),
                "--config",
                str(convert_config_file),
            ],
        )
        assert result.exit_code == 0
        assert mock_render.call_args.args[2] == tmp_path / "cfg_out"
        assert mock_render.call_args.args[3] is None

    @pytest.mark.parametrize(
        ("error", "message"),
        [
            (FileExistsError("exists"), "File already exists"),
            (RenderError("bad render"), "Rendering error occurred"),
            (RuntimeError("boom"), "Unexpected error occurred during rendering"),
        ],
    )
    def test_errors_exit_with_code_1(
        self, error, message, html_file, convert_config_file, output_dir
    ):
        with patch(
            "resumegen._cli.convert_html.render_pdf_from_html", side_effect=error
        ):
            result = runner.invoke(
                app,
                [
                    "convert-html",
                    str(html_file),
                    "--config",
                    str(convert_config_file),
                    "--output-dir",
                    str(output_dir),
                ],
            )
        assert result.exit_code == 1
        assert message in result.output
