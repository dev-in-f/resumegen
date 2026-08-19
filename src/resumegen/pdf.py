import logging
from io import BytesIO
from pathlib import Path

import pikepdf
from pikepdf import Dictionary, String
from weasyprint import HTML

from resumegen.config import DocumentMeta


def html_to_pdf(
    html_content: str,
    base_url: str,
    output_file: Path,
    meta: DocumentMeta,
    overwrite: bool = False,
) -> None:
    document = HTML(string=html_content, base_url=base_url).render()
    pdf_bytes = document.write_pdf(pdf_tags=True, custom_metadata=True)
    if pdf_bytes is None:
        raise ValueError("Failed to generate PDF from HTML content.")
    with pikepdf.open(BytesIO(pdf_bytes), allow_overwriting_input=overwrite) as pdf:
        pdf_xmp_metadata_injection(pdf, meta)
        pdf.save(output_file)


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
