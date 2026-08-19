import logging
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from resumegen.config import AppConfig, DocumentConfig, DocumentMeta


def _render_html(document_config: DocumentConfig, app_config: AppConfig) -> str:
    env = Environment(loader=FileSystemLoader(app_config.template_dir))
    template = env.get_template(document_config.template_path.name)
    return template.render(
        **{**document_config.model_dump(), **app_config.model_dump()}
    )


def _sanitize_metadata(metadata: DocumentMeta) -> dict[str, str | list[str]]:
    """Normalize metadata values for filename rendering."""
    metadata_dict = metadata.model_dump()
    for key, value in metadata_dict.items():
        if isinstance(value, str):
            sanitized = value.lower().replace(" ", "_")
            metadata_dict[key] = sanitized
    return metadata_dict


def _render_filename(document_config: DocumentConfig, app_config: AppConfig) -> str:
    """Renders the output filename based on the template and document metadata.
    Supports placeholders matching DocumentMeta attributes."""
    output_filename_template = app_config.output_config.output_filename
    metadata = _sanitize_metadata(document_config.document_metadata)

    if "keywords" in metadata and isinstance(metadata["keywords"], list):
        metadata["keywords"] = "_".join(metadata["keywords"]).lower().replace(" ", "_")

    date_str = datetime.now().strftime("%Y%m%d")
    logging.debug(
        f"Rendering output filename with template: {output_filename_template}"
    )
    return output_filename_template.format(**metadata, date=date_str)


def output_html(document_config: DocumentConfig, app_config: AppConfig) -> str:
    html_content = _render_html(document_config, app_config)
    output_filename = _render_filename(document_config, app_config)
    output_path = app_config.output_config.output_dir / output_filename
    if output_path.suffix.lower() != ".html":
        output_path = output_path.with_suffix(".html")
    logging.debug(f"Saving HTML resume to {output_path}")
    with open(output_path, "w") as f:
        f.write(html_content)
    return str(output_path)
