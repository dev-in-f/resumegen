import pytest

from resumegen.pdf import html_to_pdf


class TestPDFRenderer:
    def test_valid(self, tmp_path):
        full_output_path = tmp_path / "output.pdf"
        html_content = "<html><body><h1>Test PDF</h1></body></html>"
        result_path = html_to_pdf(html_content, full_output_path, base_url="")
        assert result_path.exists()
        assert result_path.suffix == ".pdf"

    def test_warns_on_non_pdf_suffix(self, tmp_path):
        full_output_path = tmp_path / "output.txt"
        html_content = "<html><body><h1>Test PDF</h1></body></html>"
        with pytest.warns(
            UserWarning, match="Output path should have a .pdf extension"
        ):
            result_path = html_to_pdf(html_content, full_output_path, base_url="")
            assert result_path.exists()
            assert result_path.suffix == ".pdf"
