import logging
from io import BytesIO
from pathlib import Path

import pikepdf
from pikepdf import Dictionary, String
from weasyprint import HTML

from resumegen.core.accessibility import AccessibilityReport, scan_accessibility
from resumegen.core.config import DocumentMetadata, ResumeData
from resumegen.core.exceptions import PdfError
from resumegen.core.html_rendering import (
    RenderError,
    _format_output_filename,
    _render_html,
)

logger = logging.getLogger(__name__)


def _html_to_pdf(
    html_content: str,
    base_url: Path,
    overwrite: bool = False,
) -> pikepdf.Pdf:
    """Converts HTML content to a PDF using WeasyPrint and returns
    a pikepdf.Pdf object for further manipulation."""
    try:
        document = HTML(string=html_content, base_url=base_url).render()
        pdf_bytes = document.write_pdf(pdf_tags=True, custom_metadata=True)
        if pdf_bytes is None:
            raise RenderError("PDF bytes are None.")
        return pikepdf.Pdf.open(BytesIO(pdf_bytes), allow_overwriting_input=overwrite)
    except Exception as e:
        raise RenderError(f"Failed to convert HTML into PDF: {e}") from e


def render_pdf(
    template_dir: Path,
    template_name: str,
    filename_template: str,
    output_dir: Path,
    resume_data: ResumeData,
    overwrite_existing: bool = False,
    scan_pdf_accessibility: bool = True,
) -> tuple[Path, AccessibilityReport | None]:
    # ruff: noqa: E501
    """
    Renders a PDF from HTML content using the specified Jinja2 template and WeasyPrint.

    Arguments:
        template_dir: Path to the directory containing Jinja2 templates.
        template_name: Name of the Jinja2 template file.
        filename_template: Template string for the output PDF filename.
        output_dir: Directory to save the generated PDF.
        resume_data: ResumeData object containing the data to render.
        overwrite_existing: Whether to overwrite an existing PDF file.
        scan_pdf_accessibility: Whether to scan the generated PDF for accessibility issues.
    Returns:
        A tuple containing the path to the generated PDF and an optional AccessibilityReport.
    """
    html_content = _render_html(template_dir, template_name, resume_data)
    output_filename = _format_output_filename(
        filename_template, resume_data.document_metadata
    )
    output_path = output_dir / output_filename
    pdf = _html_to_pdf(
        html_content,
        template_dir,
        overwrite_existing,
    )
    _pdf_xmp_metadata_injection(pdf, resume_data.document_metadata)
    if scan_pdf_accessibility:
        report: AccessibilityReport = scan_accessibility(pdf)
        pdf.save(output_path)
        return output_path, report
    else:
        pdf.save(output_path)
        return output_path, None


def _pdf_xmp_metadata_injection(
    pdf: pikepdf.Pdf, document_metadata: DocumentMetadata
) -> None:
    """Modifies the XMP metadate of the PDF since WeasyPrint can only set
    some metadata at render time.
    """
    try:
        with pdf.open_metadata() as meta:
            logger.debug("Original PDF metadata: %s", meta)
            meta["dc:title"] = document_metadata.title
            meta["dc:language"] = document_metadata.language  # type: ignore default always set through model
            meta["xmpRights:Owner"] = document_metadata.author
            meta["dc:subject"] = (
                ", ".join(document_metadata.keywords)
                if document_metadata.keywords
                else ""
            )
            meta["dc:creator"] = [document_metadata.author]
            meta["xmp:CreatorTool"] = "ResumeGen v1"
            meta["pdf:keywords"] = (
                ", ".join(document_metadata.keywords)
                if document_metadata.keywords
                else ""
            )
            meta["pdfuaid:part"] = "1"
            pdf.Root.lang = String(document_metadata.language)  # type: ignore default always set through model
            pdf.Root.MarkInfo = Dictionary(Marked=True)
            pdf.Root.ViewerPreferences = Dictionary(DisplayDocTitle=True)
            logger.debug("Updated PDF metadata: %s", meta)
    except Exception as e:
        raise PdfError(f"Failed to inject metadata into PDF: {e}") from e
