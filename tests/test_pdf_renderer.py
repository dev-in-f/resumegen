from io import BytesIO
from unittest.mock import MagicMock, patch

import pikepdf
import pytest

from resumegen.config import DocumentMeta
from resumegen.pdf import html_to_pdf, pdf_xmp_metadata_injection


@pytest.fixture
def sample_meta():
    return DocumentMeta(
        title="Test Resume",
        author="Jane Doe",
        language="en-US",
        keywords=["python", "engineer"],
    )


@pytest.fixture
def blank_pdf():
    pdf = pikepdf.new()
    page = pikepdf.Page(
        pikepdf.Dictionary(
            Type=pikepdf.Name("/Page"),
            MediaBox=[0, 0, 612, 792],
        )
    )
    pdf.pages.append(page)
    return pdf


SIMPLE_HTML = "<html><body><h1>Test</h1></body></html>"


class TestPdfXmpMetadataInjection:
    def test_sets_metadata(self, blank_pdf, sample_meta):
        pdf_xmp_metadata_injection(blank_pdf, sample_meta)
        with blank_pdf.open_metadata() as meta:
            assert meta["dc:title"] == sample_meta.title
            assert meta["dc:language"] == sample_meta.language
            assert meta["xmpRights:Owner"] == sample_meta.author
            assert meta["dc:subject"] == "python, engineer"
            assert meta["pdf:keywords"] == "python, engineer"
            assert meta["xmp:CreatorTool"] == "ResumeGen v1"
            assert meta["pdfuaid:part"] == "1"

    def test_sets_root_data(self, blank_pdf, sample_meta):
        pdf_xmp_metadata_injection(blank_pdf, sample_meta)
        assert str(blank_pdf.Root.lang) == sample_meta.language
        assert bool(blank_pdf.Root.MarkInfo.Marked)
        assert bool(blank_pdf.Root.ViewerPreferences.DisplayDocTitle)

    def test_empty_keywords_produces_empty_string(self, blank_pdf):
        meta = DocumentMeta(title="T", author="A", keywords=[])
        pdf_xmp_metadata_injection(blank_pdf, meta)
        with blank_pdf.open_metadata() as xmp:
            assert xmp["dc:subject"] == ""
            assert xmp["pdf:keywords"] == ""

    def test_multiple_keywords_joined_with_comma(self, blank_pdf):
        meta = DocumentMeta(title="T", author="A", keywords=["a", "b", "c"])
        pdf_xmp_metadata_injection(blank_pdf, meta)
        with blank_pdf.open_metadata() as xmp:
            assert xmp["dc:subject"] == "a, b, c"


class TestHtmlToPdf:
    def test_creates_output_file(self, tmp_path, sample_meta):
        output = tmp_path / "resume.pdf"
        html_to_pdf(SIMPLE_HTML, "", output, sample_meta)
        assert output.exists()

    def test_output_is_valid_pdf(self, tmp_path, sample_meta):
        output = tmp_path / "resume.pdf"
        html_to_pdf(SIMPLE_HTML, "", output, sample_meta)
        with pikepdf.open(output) as pdf:
            assert len(pdf.pages) >= 1

    def test_metadata_written_to_output_pdf(self, tmp_path, sample_meta):
        output = tmp_path / "resume.pdf"
        html_to_pdf(SIMPLE_HTML, "", output, sample_meta)
        with pikepdf.open(output) as pdf, pdf.open_metadata() as meta:
            assert meta["dc:title"] == sample_meta.title
            assert meta["xmp:CreatorTool"] == "ResumeGen v1"

    def test_raises_when_weasyprint_returns_none(self, tmp_path, sample_meta):
        output = tmp_path / "resume.pdf"
        mock_doc = MagicMock()
        mock_doc.write_pdf.return_value = None
        with patch("resumegen.pdf.HTML") as mock_html:
            mock_html.return_value.render.return_value = mock_doc
            with pytest.raises(ValueError, match="Failed to generate PDF"):
                html_to_pdf(SIMPLE_HTML, "", output, sample_meta)

    def test_does_not_create_file_on_error(self, tmp_path, sample_meta):
        output = tmp_path / "resume.pdf"
        mock_doc = MagicMock()
        mock_doc.write_pdf.return_value = None
        with patch("resumegen.pdf.HTML") as mock_html:
            mock_html.return_value.render.return_value = mock_doc
            with pytest.raises(ValueError):
                html_to_pdf(SIMPLE_HTML, "", output, sample_meta)
        assert not output.exists()

    def test_passes_base_url_to_weasyprint(self, tmp_path, sample_meta):
        output = tmp_path / "resume.pdf"
        pdf_bytes = pikepdf.new()
        buf = BytesIO()
        pdf_bytes.save(buf)
        mock_doc = MagicMock()
        mock_doc.write_pdf.return_value = buf.getvalue()
        with patch("resumegen.pdf.HTML") as mock_html:
            mock_html.return_value.render.return_value = mock_doc
            html_to_pdf(SIMPLE_HTML, "/some/base/url", output, sample_meta)
        mock_html.assert_called_once_with(string=SIMPLE_HTML, base_url="/some/base/url")
