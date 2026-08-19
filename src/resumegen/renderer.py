import logging
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from resumegen.config import AppConfig, DocumentConfig


def _render_html(document_config: DocumentConfig, app_config: AppConfig) -> str:
    env = Environment(loader=FileSystemLoader(app_config.template_dir))
    template = env.get_template(document_config.template_path.name)
    return template.render(
        **{**document_config.model_dump(), **app_config.model_dump()}
    )


def _render_filename(document_config: DocumentConfig, app_config: AppConfig) -> str:
    output_filename_template = app_config.output_config.output_filename
    name = document_config.document_metadata.title.replace(" ", "_").lower()
    date_str = datetime.now().strftime("%Y%m%d")
    logging.debug(
        f"Rendering output filename with template: {output_filename_template}"
        f", name: {name}, date: {date_str}"
    )
    return output_filename_template.format(name=name, date=date_str)


def output_html(document_config: DocumentConfig, app_config: AppConfig) -> str:
    html_content = _render_html(document_config, app_config)
    output_filename = _render_filename(document_config, app_config)
    # ensure output file extension is .html
    output_path = app_config.output_config.output_dir / output_filename
    if output_path.suffix.lower() != ".html":
        output_path = output_path.with_suffix(".html")
    logging.debug(f"Saving HTML resume to {output_path}")
    with open(output_path, "w") as f:
        f.write(html_content)
    return str(output_path)
