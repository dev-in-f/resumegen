from unittest.mock import patch

from click.testing import CliRunner

from resumegen._core.exceptions import PdfError, RenderError
from resumegen.cli import app

runner = CliRunner()


class TestRenderCommand:
    @patch("resumegen._cli.render.render_pdf")
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

    @patch("resumegen._cli.render.render_html")
    def test_renders_html_when_flag_set(
        self, mock_html, data_file, config_file, output_dir
    ):
        mock_html.return_value = ("<html></html>", output_dir / "resume.html")
        result = runner.invoke(
            app,
            [
                "render",
                str(data_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--html-only",
            ],
        )
        assert result.exit_code == 0
        mock_html.assert_called_once()

    @patch("resumegen._cli.render.render_pdf")
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

    @patch("resumegen._cli.render.render_pdf")
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

    @patch("resumegen._cli.render.render_pdf")
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

    @patch("resumegen._cli.render.render_pdf")
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
        _, _kwargs = mock_render.call_args
        call_args = mock_render.call_args.args
        assert call_args[5] is True

    @patch("resumegen._cli.render.render_pdf")
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

    @patch("resumegen._cli.render.render_pdf")
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
            "resumegen._cli.render.render_pdf",
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

    @patch("resumegen._cli.render.render_pdf")
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

    @patch("resumegen._cli.render.render_pdf")
    def test_output_template_with_dir_nests_under_output_dir(
        self, mock_render, data_file, config_file, output_dir, tmp_path
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
                "{title}/my_{author}.pdf",
            ],
        )
        assert result.exit_code == 0
        call_args = mock_render.call_args.args
        assert call_args[1] == output_dir
        assert call_args[2] == "{title}/my_{author}.pdf"

    @patch("resumegen._cli.render.render_html")
    def test_html_only_no_interactive_save_prints_content_and_saves(
        self, mock_html, data_file, config_file, output_dir
    ):
        saved_path = output_dir / "resume.html"
        mock_html.return_value = ("<html>hi</html>", saved_path)
        result = runner.invoke(
            app,
            [
                "render",
                str(data_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--html-only",
                "--no-interactive",
                "--save",
            ],
        )
        assert result.exit_code == 0
        assert mock_html.call_args.args[5] is True  # save_to_file
        assert result.output.strip() == "<html>hi</html>"

    @patch("resumegen._cli.render.render_html")
    def test_html_only_no_interactive_no_save_prints_content_only(
        self, mock_html, data_file, config_file, output_dir
    ):
        mock_html.return_value = ("<html>hi</html>", None)
        result = runner.invoke(
            app,
            [
                "render",
                str(data_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--html-only",
                "--no-interactive",
                "--no-save",
            ],
        )
        assert result.exit_code == 0
        assert mock_html.call_args.args[5] is False  # save_to_file
        assert result.output.strip() == "<html>hi</html>"

    @patch("resumegen._cli.render.render_html")
    def test_html_only_interactive_no_save_prints_decorated_content(
        self, mock_html, data_file, config_file, output_dir
    ):
        mock_html.return_value = ("<html>hi</html>", None)
        result = runner.invoke(
            app,
            [
                "render",
                str(data_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--html-only",
                "--no-save",
            ],
        )
        assert result.exit_code == 0
        assert "<html>hi</html>" in result.output
        assert "Rendered HTML" in result.output

    @patch("resumegen._cli.render.render_pdf")
    def test_pdf_no_interactive_prints_bare_path(
        self, mock_render, data_file, config_file, output_dir
    ):
        output_path = output_dir / "resume.pdf"
        mock_render.return_value = (output_path, None)
        result = runner.invoke(
            app,
            [
                "render",
                str(data_file),
                "--config",
                str(config_file),
                "--output-dir",
                str(output_dir),
                "--no-interactive",
            ],
        )
        assert result.exit_code == 0
        assert result.output.strip() == str(output_path.resolve())

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
        with patch(
            "resumegen._cli.render.render_pdf", side_effect=PdfError("PDF error")
        ):
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
        with patch(
            "resumegen._cli.render.render_pdf", side_effect=RenderError("Render error")
        ):
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
        with patch(
            "resumegen._cli.render.render_pdf", side_effect=RuntimeError("Unexpected")
        ):
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
