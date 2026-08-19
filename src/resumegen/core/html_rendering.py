import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from resumegen.core.config import ResumeData
from resumegen.core.exceptions import RenderError
from resumegen.core.formatting import _format_output_filename

logger = logging.getLogger(__name__)


def _render_html(
    template_dir: Path,
    template_name: str,
    resume_data: ResumeData,
) -> str:
    """
    Renders resume data into HTML using the specified Jinja2 template.
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
    output_filename = _format_output_filename(
        filename_template, resume_data.document_metadata
    )
    output_path = output_dir / output_filename
    output_path = output_path.with_suffix(".html")
    with open(output_path, "w") as f:
        f.write(html_content)
    logger.debug("Saved HTML content to: %s", output_path)
    return output_path
