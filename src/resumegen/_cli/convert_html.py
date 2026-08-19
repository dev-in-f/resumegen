import logging
from pathlib import Path

import click

from resumegen._cli.shared import (
    _load_yaml_to_data_model,
    _override_logging_options,
    _split_output_path,
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
    "--assets-dir",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, path_type=Path),
    default=None,
    help="Directory for resolving relative paths in the HTML file, "
    "i.e. stylesheets, images, etc. "
    "If not provided, the template directory from the config file or"
    " the directory of the HTML file will be used.",
)
@click.option(
    "-o",
    "--output-name",
    type=str,
    default=None,
    help="Output filename for the generated PDF. May include a directory "
    "(e.g. 'out/resume.pdf'), which is created if it doesn't exist and "
    "takes precedence over --output-dir. Uses the input filename if not provided.",
)
def convert_html(
    html_file: Path,
    config_path: Path,
    assets_dir: Path | None,
    output_dir: Path | None,
    log_level: str | None,
    log_file: Path | None,
    verbose: bool,
    output_name: str | None,
    overwrite_existing: bool,
):
    """Convert an existing HTML file to a PDF."""
    _override_logging_options(log_level, log_file, verbose)
    try:
        config = _load_yaml_to_data_model(config_path, Config)
        if not assets_dir:
            assets_dir = config.template_dir or html_file.parent
        embedded_dir, output_name = _split_output_path(output_name, output_dir)
        working_output_dir = embedded_dir or output_dir or config.output_dir
        render_pdf_from_html(
            html_file,
            assets_dir,
            working_output_dir,
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
