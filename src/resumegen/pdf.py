import logging
import warnings
from pathlib import Path

from weasyprint import HTML


def html_to_pdf(html_content: str, output_path: Path, base_url: str):
    if output_path.suffix.lower() != ".pdf":
        warnings.warn(
            "Output path should have a .pdf extension, appending .pdf", stacklevel=2
        )
        output_path = output_path.with_suffix(".pdf")
    document = HTML(string=html_content, base_url=base_url).render()
    document.write_pdf(output_path, pdf_tags=True, custom_metadata=True)
    logging.info(f"PDF generated successfully at {output_path}")
    return output_path
