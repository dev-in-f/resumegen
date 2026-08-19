import logging
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from resumegen.config import DocumentMetadata, ResumeData


def render_html(
    template_dir: Path,
    template_name: str,
    document_metadata: DocumentMetadata,
    resume_data: ResumeData,
) -> str:
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_name)
    html = template.render(
        **{
            "document_metadata": document_metadata.model_dump(),
            "resume_data": resume_data.model_dump(),
        }
    )
    logging.debug(f"Rendered HTML content:\n{html}")
    return html


def _sanitize_metadata(metadata: DocumentMetadata) -> dict[str, str]:
    """Normalize metadata values for filename rendering."""
    metadata_dict = metadata.model_dump()
    for key, value in metadata_dict.items():
        if isinstance(value, str):
            sanitized = value.lower().replace(" ", "_")
            metadata_dict[key] = sanitized
        if isinstance(value, list):
            metadata_dict[key] = [str(v).lower().replace(" ", "_") for v in value]
            metadata_dict[key] = "_".join(metadata_dict[key])
    return metadata_dict


def render_output_filename(filename_template: str, metadata: DocumentMetadata) -> str:
    """Renders the output filename based on the template and document metadata.
    Supports placeholders matching DocumentMeta attributes."""
    output_filename = filename_template
    clean_metadata = _sanitize_metadata(metadata)
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.debug(f"Rendering output filename with template: {output_filename}")
    return output_filename.format(**clean_metadata, date=date_str)


def output_html(
    template_dir: Path,
    template_name: str,
    document_metadata: DocumentMetadata,
    resume_data: ResumeData,
    filename_template: str,
    output_dir: Path,
) -> Path:
    html_content = render_html(
        template_dir, template_name, document_metadata, resume_data
    )
    output_filename = render_output_filename(filename_template, document_metadata)
    output_path = output_dir / output_filename
    output_path = output_path.with_suffix(".html")
    with open(output_path, "w") as f:
        f.write(html_content)
    return output_path
