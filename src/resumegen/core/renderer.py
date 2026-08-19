import logging
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from resumegen.core.config import DocumentMetadata, ResumeData
from resumegen.core.exceptions import RenderError

logger = logging.getLogger(__name__)


def _render_html(
    template_dir: Path,
    template_name: str,
    resume_data: ResumeData,
) -> str:
    """
    Renders resume data into HTML using the specified Jinja2 template.

    Arguments:
        template_dir: Path to the directory containing Jinja2 templates.
        template_name: Name of the Jinja2 template file.
        resume_data: ResumeData object containing the data to render.
    Returns:
        Rendered HTML as a string.
    Raises:
        RenderError: If rendering fails due to template issues or data problems.
    """
    try:
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_name)
        html = template.render(
            **{
                "document_metadata": resume_data.document_metadata.model_dump(),
                "resume_data": resume_data.model_dump(),
            }
        )
        logger.debug("Rendered HTML content:\n%s", html)
        return html
    except Exception as e:
        raise RenderError(f"Failed to render HTML: {e}") from e


def _sanitize_metadata(metadata: DocumentMetadata) -> dict[str, str]:
    """Normalizes DocumentMetadata values for filename rendering."""
    metadata_dict = metadata.model_dump()
    for key, value in metadata_dict.items():
        if isinstance(value, str):
            sanitized = value.lower().replace(" ", "_")
            metadata_dict[key] = sanitized
        if isinstance(value, list):
            metadata_dict[key] = [str(v).lower().replace(" ", "_") for v in value]
            metadata_dict[key] = "_".join(metadata_dict[key])
    logger.debug("Sanitized metadata: %s", metadata_dict)
    return metadata_dict


def render_output_filename(filename_template: str, metadata: DocumentMetadata) -> str:
    """
    Renders the output filename based on the template and document metadata.
    Supports placeholders matching DocumentMeta attributes.

    Arguments:
        filename_template: A string template for the filename.
        metadata: DocumentMetadata object containing the metadata
                  for rendering the filename.

    Returns:
        Rendered output filename as a string.
    """
    output_filename = filename_template
    clean_metadata = _sanitize_metadata(metadata)
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logger.debug("Rendering output filename with template: %s", output_filename)
    return output_filename.format(**clean_metadata, date=date_str)


def output_html(
    template_dir: Path,
    template_name: str,
    resume_data: ResumeData,
    filename_template: str,
    output_dir: Path,
) -> Path:
    """
    Renders the given ResumeData into HTML
    and saves it to the specified output directory.

    Arguments:
        template_dir: Path to the directory containing Jinja2 templates.
        template_name: Name of the Jinja2 template file.
        resume_data: ResumeData object containing the data to render.
        filename_template: Template for the output filename.
        output_dir: Directory to save the rendered file.

    Returns:
        Path to the saved HTML file.
    """
    html_content = _render_html(template_dir, template_name, resume_data)
    output_filename = render_output_filename(
        filename_template, resume_data.document_metadata
    )
    output_path = output_dir / output_filename
    output_path = output_path.with_suffix(".html")
    with open(output_path, "w") as f:
        f.write(html_content)
    logger.debug("Saved HTML content to: %s", output_path)
    return output_path
