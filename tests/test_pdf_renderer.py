from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pikepdf
import pytest

from resumegen import pdf as pdf_module
from resumegen.config import Config, DocumentConfig, DocumentMeta, OutputConfig
from resumegen.pdf import pdf_xmp_metadata_injection, render_pdf


@pytest.fixture
def sample_meta():
    return DocumentMeta(
        title="Test Resume",
        author="Jane Doe",
        language="en-US",
        keywords=["python", "engineer"],
    )


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
            assert meta["dc:creator"] == [sample_meta.author]

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

    def test_single_keyword(self, blank_pdf):
        meta = DocumentMeta(title="T", author="A", keywords=["python"])
        pdf_xmp_metadata_injection(blank_pdf, meta)
        with blank_pdf.open_metadata() as xmp:
            assert xmp["dc:subject"] == "python"
            assert xmp["pdf:keywords"] == "python"

    def test_multiple_keywords_joined_with_comma(self, blank_pdf):
        meta = DocumentMeta(title="T", author="A", keywords=["a", "b", "c"])
        pdf_xmp_metadata_injection(blank_pdf, meta)
        with blank_pdf.open_metadata() as xmp:
            assert xmp["dc:subject"] == "a, b, c"


class TestRenderPdf:
    @pytest.fixture
    def app_config(self, template_dir, tmp_path):
        return Config(
            template_dir=template_dir,
            output_config=OutputConfig(output_dir=tmp_path / "output"),
        )

    @pytest.fixture
    def document_config(self, sample_meta, minimal_resume_data):
        return DocumentConfig(
            document_metadata=sample_meta,
            resume_data=minimal_resume_data,
        )

    def test_creates_output_file(self, app_config, document_config):
        output_path = render_pdf(
            app_config, document_config, scan_pdf_accessibility=False
        )
        assert output_path.exists()

    def test_returns_pdf_in_output_dir(self, app_config, document_config):
        output_path = render_pdf(
            app_config, document_config, scan_pdf_accessibility=False
        )
        assert output_path.parent == app_config.output_config.output_dir
        assert output_path.suffix == ".pdf"

    def test_output_is_valid_pdf(self, app_config, document_config):
        output_path = render_pdf(
            app_config, document_config, scan_pdf_accessibility=False
        )
        with pikepdf.open(output_path) as pdf:
            assert len(pdf.pages) >= 1

    def test_metadata_written_to_output_pdf(
        self, app_config, document_config, sample_meta
    ):
        output_path = render_pdf(
            app_config, document_config, scan_pdf_accessibility=False
        )
        with pikepdf.open(output_path) as pdf, pdf.open_metadata() as meta:
            assert meta["dc:title"] == sample_meta.title
            assert meta["dc:language"] == sample_meta.language
            assert meta["xmpRights:Owner"] == sample_meta.author
            assert meta["dc:subject"] == "python, engineer"
            assert meta["pdf:keywords"] == "python, engineer"
            assert meta["xmp:CreatorTool"] == "ResumeGen v1"
            assert meta["pdfuaid:part"] == "1"

    def test_runs_accessibility_scan_by_default(self, app_config, document_config):
        with patch("resumegen.pdf.scan_accessibility") as mock_scan:
            render_pdf(app_config, document_config)
        mock_scan.assert_called_once()
        mock_scan.return_value.print.assert_called_once()

    def test_skips_accessibility_scan_when_disabled(self, app_config, document_config):
        with patch("resumegen.pdf.scan_accessibility") as mock_scan:
            render_pdf(app_config, document_config, scan_pdf_accessibility=False)
        mock_scan.assert_not_called()

    def test_raises_when_weasyprint_returns_none(self, app_config, document_config):
        mock_doc = MagicMock()
        mock_doc.write_pdf.return_value = None
        with patch("resumegen.pdf.HTML") as mock_html:
            mock_html.return_value.render.return_value = mock_doc
            with pytest.raises(ValueError, match="Failed to generate PDF"):
                render_pdf(app_config, document_config)

    def test_does_not_create_file_on_error(self, app_config, document_config):
        mock_doc = MagicMock()
        mock_doc.write_pdf.return_value = None
        with patch("resumegen.pdf.HTML") as mock_html:
            mock_html.return_value.render.return_value = mock_doc
            with pytest.raises(ValueError):
                render_pdf(app_config, document_config)
        assert list(app_config.output_config.output_dir.iterdir()) == []

    def test_passes_base_url_to_weasyprint(self, app_config, document_config):
        buf = BytesIO()
        pikepdf.new().save(buf)
        mock_doc = MagicMock()
        mock_doc.write_pdf.return_value = buf.getvalue()
        with patch("resumegen.pdf.HTML") as mock_html:
            mock_html.return_value.render.return_value = mock_doc
            render_pdf(app_config, document_config, scan_pdf_accessibility=False)
        call_kwargs = mock_html.call_args.kwargs
        assert call_kwargs["base_url"] == str(Path(pdf_module.__file__).parent)
