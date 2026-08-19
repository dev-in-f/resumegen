import logging
from pathlib import Path

import click

from resumegen._cli.shared import (
    _load_yaml_to_data_model,
    _override_logging_options,
    logging_options,
    render_options,
)
from resumegen._core.config import Config
from resumegen._core.exceptions import RenderError
from resumegen._core.pdf import render_pdf_from_html

logger = logging.getLogger("resumegen.cli")


@click.command()
@logging_options
@render_options
@click.argument(
    "html_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--base-url",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, path_type=Path),
    default=None,
    help="Base URL for resolving relative paths in the HTML file, "
    "i.e. stylesheets, images, etc. "
    "If not provided, the template directory from the config file or"
    " the directory of the HTML file will be used.",
)
@click.option(
    "-o",
    "--output-name",
    type=str,
    default=None,
    help="Output filename for the generated PDF. "
    "Uses the input filename if not provided.",
)
def render_html(
    html_file: Path,
    config_path: Path,
    base_url: Path | None,
    output_dir: Path | None,
    log_level: str | None,
    log_file: Path | None,
    verbose: bool,
    output_name: str | None,
    overwrite_existing: bool,
):
    _override_logging_options(log_level, log_file, verbose)
    try:
        config = _load_yaml_to_data_model(config_path, Config)
        if not base_url:
            base_url = config.template_dir or html_file.parent
        if not output_dir:
            output_dir = config.output_dir
        render_pdf_from_html(
            html_file,
            base_url,
            output_dir,
            output_name,
            overwrite_existing,
        )
    except FileExistsError as e:
        logger.exception("File already exists")
        raise click.exceptions.Exit(code=1) from e
    except RenderError as e:
        logger.exception("Rendering error occurred")
        raise click.exceptions.Exit(code=1) from e
    except Exception as e:
        logger.exception("Unexpected error occurred during rendering.")

        raise click.exceptions.Exit(code=1) from e
