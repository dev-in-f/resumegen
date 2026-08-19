import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from resumegen._core.config import ResumeData
from resumegen._core.exceptions import RenderError
from resumegen._core.formatting import _format_output_filename

logger = logging.getLogger(__name__)


def _render_html_from_template(
    template_dir: Path,
    template_name: str,
    resume_data: ResumeData,
) -> str:
    """Renders resume data into HTML using the specified Jinja2 template."""
    try:
        env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
        template = env.get_template(template_name)
        html = template.render(
            document_metadata=resume_data.document_metadata.model_dump(),
            resume_data=resume_data.model_dump(),
        )
        logger.debug("Rendered HTML content:\n%s", html)
    except Exception as e:
        raise RenderError(f"Failed to render HTML: {e}") from e
    else:
        return html


def render_html(
    resume_data: ResumeData,
    output_dir: Path,
    filename_template: str,
    template_name: str,
    template_dir: Path,
    save_to_file: bool = True,
    override_existing: bool = False,
) -> Path | str:
    """Renders the given ResumeData into HTML
    and saves it to the specified output directory or returns the content.

    Arguments:
        resume_data: ResumeData object containing the data to render.
        output_dir: Directory to save the rendered file.
        filename_template: Template for the output filename.
        template_name: Name of the Jinja2 template file.
        template_dir: Path to the directory containing Jinja2 templates.
        save_to_file: If True, saves the rendered HTML to a file;
        otherwise, returns the HTML content.
        override_existing: If True, overrides existing files with the same name.

    Returns:
        Path to the saved HTML file or the HTML content.

    """
    html_content = _render_html_from_template(template_dir, template_name, resume_data)
    if not save_to_file:
        return html_content
    output_filename = _format_output_filename(
        filename_template, resume_data.document_metadata
    )
    output_path = output_dir / output_filename
    output_path = output_path.with_suffix(".html")
    if output_path.exists() and not override_existing:
        raise FileExistsError(f"File already exists: {output_path}")
    with output_path.open("w") as f:
        f.write(html_content)
    logger.debug("Saved HTML content to: %s", output_path)
    return output_path
