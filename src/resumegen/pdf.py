import logging
from io import BytesIO
from pathlib import Path

import pikepdf
from pikepdf import Dictionary, String
from weasyprint import HTML

from resumegen.accessibility import AccessibilityReport, scan_accessibility
from resumegen.config import AppConfig, DocumentConfig, DocumentMeta
from resumegen.renderer import render_html, render_output_filename


def _html_to_pdf(
    html_content: str,
    base_url: str,
    overwrite: bool = False,
) -> pikepdf.Pdf:
    document = HTML(string=html_content, base_url=base_url).render()
    pdf_bytes = document.write_pdf(pdf_tags=True, custom_metadata=True)
    if pdf_bytes is None:
        raise ValueError("Failed to generate PDF from HTML content.")
    return pikepdf.Pdf.open(BytesIO(pdf_bytes), allow_overwriting_input=overwrite)


def render_pdf(
    app_config: AppConfig,
    document_config: DocumentConfig,
    scan_pdf_accessibility: bool = True,
) -> Path:
    html_content = render_html(document_config, app_config)
    output_filename = render_output_filename(document_config, app_config)
    output_path = app_config.output_config.output_dir / output_filename
    pdf = _html_to_pdf(
        html_content,
        base_url=str(Path(__file__).parent),
        overwrite=app_config.output_config.overwrite,
    )
    pdf_xmp_metadata_injection(pdf, document_config.document_metadata)
    if scan_pdf_accessibility:
        report: AccessibilityReport = scan_accessibility(pdf)
        logging.info("Accessibility scan completed. Report:")
        report.print()
    pdf.save(output_path)
    logging.info(f"PDF generated at: {output_path.resolve()}")
    return output_path


def pdf_xmp_metadata_injection(
    pdf: pikepdf.Pdf, document_metadata: DocumentMeta
) -> None:
    logging.debug(f"Original PDF metadata: {pdf.open_metadata()}")
    with pdf.open_metadata() as meta:
        meta["dc:title"] = document_metadata.title
        meta["dc:language"] = document_metadata.language
        meta["xmpRights:Owner"] = document_metadata.author
        meta["dc:subject"] = ", ".join(document_metadata.keywords)
        meta["dc:creator"] = [document_metadata.author]
        meta["xmp:CreatorTool"] = "ResumeGen v1"
        meta["pdf:keywords"] = ", ".join(document_metadata.keywords)
        meta["pdfuaid:part"] = "1"
    pdf.Root.lang = String(document_metadata.language)
    pdf.Root.MarkInfo = Dictionary(Marked=True)
    pdf.Root.ViewerPreferences = Dictionary(DisplayDocTitle=True)
    logging.debug(f"Updated PDF metadata: {pdf.open_metadata()}")
