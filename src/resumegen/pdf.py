import logging
import warnings
from pathlib import Path

from weasyprint import HTML


def html_to_pdf(html_content: str, full_output_path: Path, base_url: str):
    if full_output_path.suffix.lower() != ".pdf":
        warnings.warn(
            "Output path should have a .pdf extension, appending .pdf", stacklevel=2
        )
        full_output_path = full_output_path.with_suffix(".pdf")
    document = HTML(string=html_content, base_url=base_url).render()
    document.write_pdf(full_output_path, pdf_tags=True, custom_metadata=True)
    logging.info(f"PDF generated successfully at {full_output_path}")
    return full_output_path
