import logging
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from resumegen.config import AppConfig, DocumentConfig, DocumentMeta


def render_html(document_config: DocumentConfig, app_config: AppConfig) -> str:
    env = Environment(loader=FileSystemLoader(app_config.template_dir))
    template = env.get_template(document_config.template_filename.name)
    html = template.render(
        **{**document_config.model_dump(), **app_config.model_dump()}
    )
    logging.debug(f"Rendered HTML content:\n{html}")
    return html


def _sanitize_metadata(metadata: DocumentMeta) -> dict[str, str]:
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


def render_output_filename(
    document_config: DocumentConfig, app_config: AppConfig
) -> str:
    """Renders the output filename based on the template and document metadata.
    Supports placeholders matching DocumentMeta attributes."""
    output_filename = app_config.output_config.output_filename
    metadata = _sanitize_metadata(document_config.document_metadata)
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.debug(f"Rendering output filename with template: {output_filename}")
    return output_filename.format(**metadata, date=date_str)


def output_html(document_config: DocumentConfig, app_config: AppConfig) -> str:
    html_content = render_html(document_config, app_config)
    output_filename = render_output_filename(document_config, app_config)
    output_path = app_config.output_config.output_dir / output_filename
    output_path = output_path.with_suffix(".html")
    logging.info(f"Saving HTML to {output_path}")
    with open(output_path, "w") as f:
        f.write(html_content)
    return str(output_path)
