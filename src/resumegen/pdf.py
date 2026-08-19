import logging
from importlib import resources
from io import BytesIO
from pathlib import Path

import pikepdf
from pikepdf import Dictionary, String
from weasyprint import HTML

from resumegen.accessibility import AccessibilityReport, scan_accessibility
from resumegen.config import DocumentMetadata, ResumeData
from resumegen.renderer import render_html, render_output_filename


def _html_to_pdf(
    html_content: str,
    base_url: Path,
    overwrite: bool = False,
) -> pikepdf.Pdf:
    document = HTML(string=html_content, base_url=base_url).render()
    pdf_bytes = document.write_pdf(pdf_tags=True, custom_metadata=True)
    if pdf_bytes is None:
        raise ValueError("Failed to generate PDF from HTML content.")
    return pikepdf.Pdf.open(BytesIO(pdf_bytes), allow_overwriting_input=overwrite)


def render_pdf(
    template_dir: Path,
    template_name: str,
    filename_template: str,
    output_dir: Path,
    resume_data: ResumeData,
    overwrite_existing: bool = False,
    scan_pdf_accessibility: bool = True,
) -> tuple[Path, AccessibilityReport | None]:
    html_content = render_html(template_dir, template_name, resume_data)
    output_filename = render_output_filename(
        filename_template, resume_data.document_metadata
    )
    output_path = output_dir / output_filename
    with resources.path("resumegen", "templates") as fspath:
        pdf = _html_to_pdf(
            html_content,
            fspath,
            overwrite_existing,
        )
    pdf_xmp_metadata_injection(pdf, resume_data.document_metadata)
    if scan_pdf_accessibility:
        report: AccessibilityReport = scan_accessibility(pdf)
        pdf.save(output_path)
        return output_path, report
    else:
        pdf.save(output_path)
        return output_path, None


def pdf_xmp_metadata_injection(
    pdf: pikepdf.Pdf, document_metadata: DocumentMetadata
) -> None:
    logging.debug(f"Original PDF metadata: {pdf.open_metadata()}")
    with pdf.open_metadata() as meta:
        meta["dc:title"] = document_metadata.title
        meta["dc:language"] = document_metadata.language  # type: ignore default always set through model
        meta["xmpRights:Owner"] = document_metadata.author
        meta["dc:subject"] = (
            ", ".join(document_metadata.keywords) if document_metadata.keywords else ""
        )
        meta["dc:creator"] = [document_metadata.author]
        meta["xmp:CreatorTool"] = "ResumeGen v1"
        meta["pdf:keywords"] = (
            ", ".join(document_metadata.keywords) if document_metadata.keywords else ""
        )
        meta["pdfuaid:part"] = "1"
    pdf.Root.lang = String(document_metadata.language)  # type: ignore default always set through model
    pdf.Root.MarkInfo = Dictionary(Marked=True)
    pdf.Root.ViewerPreferences = Dictionary(DisplayDocTitle=True)
    logging.debug(f"Updated PDF metadata: {pdf.open_metadata()}")
