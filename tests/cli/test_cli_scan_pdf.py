from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from resumegen._core.exceptions import PdfError
from resumegen.cli import app

runner = CliRunner()


class TestScanPdfCommand:
    @patch("resumegen._cli.scan_pdf.scan_accessibility")
    @patch("resumegen._cli.scan_pdf.pikepdf.open")
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
                "resumegen._cli.scan_pdf.scan_accessibility",
                side_effect=RuntimeError("Scan failed"),
            ),
            patch("resumegen._cli.scan_pdf.pikepdf.open") as mock_pikepdf_open,
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
                "resumegen._cli.scan_pdf.scan_accessibility",
                side_effect=PdfError("PDF error"),
            ),
            patch("resumegen._cli.scan_pdf.pikepdf.open") as mock_pikepdf_open,
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
