from pathlib import Path
from unittest.mock import MagicMock, patch

import pikepdf
import pytest

from resumegen.config import Config, DocumentMetadata
from resumegen.pdf import pdf_xmp_metadata_injection, render_pdf


class TestPdfXmpMetadataInjection:
    def test_sets_metadata(self, blank_pdf, minimal_document_metadata):
        pdf_xmp_metadata_injection(blank_pdf, minimal_document_metadata)
        with blank_pdf.open_metadata() as meta:
            assert meta["dc:title"] == minimal_document_metadata.title
            assert meta["dc:language"] == minimal_document_metadata.language
            assert meta["xmpRights:Owner"] == minimal_document_metadata.author
            assert meta["dc:subject"] == "python, engineer"
            assert meta["pdf:keywords"] == "python, engineer"
            assert meta["xmp:CreatorTool"] == "ResumeGen v1"
            assert meta["pdfuaid:part"] == "1"
            assert meta["dc:creator"] == [minimal_document_metadata.author]

    def test_sets_root_data(self, blank_pdf, minimal_document_metadata):
        pdf_xmp_metadata_injection(blank_pdf, minimal_document_metadata)
        assert str(blank_pdf.Root.lang) == minimal_document_metadata.language
        assert bool(blank_pdf.Root.MarkInfo.Marked)
        assert bool(blank_pdf.Root.ViewerPreferences.DisplayDocTitle)

    def test_empty_keywords_produces_empty_string(self, blank_pdf):
        meta = DocumentMetadata(title="T", author="A", keywords=[])
        pdf_xmp_metadata_injection(blank_pdf, meta)
        with blank_pdf.open_metadata() as xmp:
            assert xmp["dc:subject"] == ""
            assert xmp["pdf:keywords"] == ""

    def test_single_keyword(self, blank_pdf):
        meta = DocumentMetadata(title="T", author="A", keywords=["python"])
        pdf_xmp_metadata_injection(blank_pdf, meta)
        with blank_pdf.open_metadata() as xmp:
            assert xmp["dc:subject"] == "python"
            assert xmp["pdf:keywords"] == "python"

    def test_multiple_keywords_joined_with_comma(self, blank_pdf):
        meta = DocumentMetadata(title="T", author="A", keywords=["a", "b", "c"])
        pdf_xmp_metadata_injection(blank_pdf, meta)
        with blank_pdf.open_metadata() as xmp:
            assert xmp["dc:subject"] == "a, b, c"


class TestRenderPdf:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.config = Config(
            output_dir=tmp_path,
            template_dir=Path(__file__).parent / "fixtures",
            template_name="test_template.html.j2",
        )

    def test_creates_output_file(self, minimal_resume_data):
        output_path, _ = render_pdf(
            self.config.template_dir,
            self.config.template_name,
            self.config.output_filename,
            self.config.output_dir,
            minimal_resume_data,
            scan_pdf_accessibility=False,
        )

        assert output_path.exists()

    def test_returns_pdf_in_output_dir(self, minimal_resume_data):
        output_path, _ = render_pdf(
            self.config.template_dir,
            self.config.template_name,
            self.config.output_filename,
            self.config.output_dir,
            minimal_resume_data,
            scan_pdf_accessibility=False,
        )
        assert output_path.parent == self.config.output_dir
        assert output_path.suffix == ".pdf"

    def test_output_is_valid_pdf(self, minimal_resume_data):
        output_path, _ = render_pdf(
            self.config.template_dir,
            self.config.template_name,
            self.config.output_filename,
            self.config.output_dir,
            minimal_resume_data,
            scan_pdf_accessibility=False,
        )
        with pikepdf.open(output_path) as pdf:
            assert len(pdf.pages) >= 1

    def test_metadata_written_to_output_pdf(self, minimal_resume_data):
        output_path, _ = render_pdf(
            self.config.template_dir,
            self.config.template_name,
            self.config.output_filename,
            self.config.output_dir,
            minimal_resume_data,
            scan_pdf_accessibility=False,
        )
        with pikepdf.open(output_path) as pdf, pdf.open_metadata() as meta:
            assert meta["dc:title"] == minimal_resume_data.document_metadata.title
            assert meta["dc:language"] == minimal_resume_data.document_metadata.language
            assert (
                meta["xmpRights:Owner"] == minimal_resume_data.document_metadata.author
            )
            assert meta["dc:subject"] == "python, engineer"
            assert meta["pdf:keywords"] == "python, engineer"
            assert meta["xmp:CreatorTool"] == "ResumeGen v1"
            assert meta["pdfuaid:part"] == "1"

    def test_runs_accessibility_scan_by_default(self, minimal_resume_data):
        with patch("resumegen.pdf.scan_accessibility") as mock_scan:
            _, report = render_pdf(
                self.config.template_dir,
                self.config.template_name,
                self.config.output_filename,
                self.config.output_dir,
                minimal_resume_data,
            )
        mock_scan.assert_called_once()
        assert report is not None

    def test_skips_accessibility_scan_when_disabled(self, minimal_resume_data):
        with patch("resumegen.pdf.scan_accessibility") as mock_scan:
            render_pdf(
                self.config.template_dir,
                self.config.template_name,
                self.config.output_filename,
                self.config.output_dir,
                minimal_resume_data,
                scan_pdf_accessibility=False,
            )
        mock_scan.assert_not_called()

    def test_raises_when_weasyprint_returns_none(self, minimal_resume_data):
        mock_doc = MagicMock()
        mock_doc.write_pdf.return_value = None
        with patch("resumegen.pdf.HTML") as mock_html:
            mock_html.return_value.render.return_value = mock_doc
            with pytest.raises(ValueError, match="Failed to generate PDF"):
                render_pdf(
                    self.config.template_dir,
                    self.config.template_name,
                    self.config.output_filename,
                    self.config.output_dir,
                    minimal_resume_data,
                    scan_pdf_accessibility=False,
                )

    def test_does_not_create_file_on_error(self, minimal_resume_data):
        mock_doc = MagicMock()
        mock_doc.write_pdf.return_value = None
        with patch("resumegen.pdf.HTML") as mock_html:
            mock_html.return_value.render.return_value = mock_doc
            with pytest.raises(ValueError):
                output_path, _ = render_pdf(
                    self.config.template_dir,
                    self.config.template_name,
                    self.config.output_filename,
                    self.config.output_dir,
                    minimal_resume_data,
                    scan_pdf_accessibility=False,
                )

        assert list(self.config.output_dir.iterdir()) == []

    # def test_passes_base_url_to_weasyprint(self, minimal_resume_data):
    #     buf = BytesIO()
    #     pikepdf.new().save(buf)
    #     mock_doc = MagicMock()
    #     mock_doc.write_pdf.return_value = buf.getvalue()
    #     with patch("resumegen.pdf.HTML") as mock_html:
    #         mock_html.return_value.render.return_value = mock_doc
    #         render_pdf(
    #             self.config.template_dir,
    #             self.config.template_name,
    #             self.config.output_filename,
    #             self.config.output_dir,
    #             minimal_resume_data,
    #             scan_pdf_accessibility=False,
    #         )
    #     call_kwargs = mock_html.call_args.kwargs
    #     assert call_kwargs["base_url"] == str(Path(pdf_module.__file__).parent)
