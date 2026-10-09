import logging
from pathlib import Path

import click

from resumegen._cli.shared import (
    _load_yaml_to_data_model,
    _output_base_dir,
    _override_logging_options,
    logging_options,
    render_options,
)
from resumegen._core.config import Config
from resumegen._core.exceptions import RenderError
from resumegen._core.logging import Spinner, color_message
from resumegen._core.pdf import render_pdf_from_html

logger = logging.getLogger("resumegen.cli")


@click.command()
@logging_options
@render_options
@click.option(
    "--interactive/--no-interactive",
    "interactive",
    is_flag=True,
    default=True,
    help="Print decorated status messages. With --no-interactive, only the "
    "output path is printed to stdout, for use in scripts/pipelines.",
)
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
    help="Output filename for the generated PDF. A bare filename is saved under "
    "the configured output directory (config file or RESUMEGEN_OUTPUT_DIR); a "
    "relative or absolute path (e.g. './resume.pdf', 'out/resume.pdf') is "
    "resolved against the current working directory instead. Missing "
    "directories are created. Uses the input filename if not provided.",
)
def render_html(
    html_file: Path,
    config_path: Path,
    assets_dir: Path | None,
    log_level: str | None,
    log_file: Path | None,
    verbose: bool,
    output_name: str | None,
    overwrite_existing: bool,
    interactive: bool = True,
):
    """Convert an existing HTML file to a PDF."""
    _override_logging_options(log_level, log_file, verbose)
    try:
        config = _load_yaml_to_data_model(config_path, Config)
        if interactive:
            click.echo(color_message("⚙️  Configuration loaded successfully!", "green"))
        if not assets_dir:
            assets_dir = config.template_dir or html_file.parent
        working_output_dir = _output_base_dir(output_name, config.output_dir)
        with Spinner(f"🖨️  Converting {html_file} to PDF...", enabled=interactive):
            output_path = render_pdf_from_html(
                html_file,
                assets_dir,
                working_output_dir,
                output_name,
                overwrite_existing,
            )
        if interactive:
            click.echo(
                color_message(f"👻  PDF generated at: {output_path.resolve()}", "green")
            )
        else:
            click.echo(str(output_path.resolve()))
    except FileExistsError as e:
        logger.exception("File already exists")
        raise click.exceptions.Exit(code=1) from e
    except RenderError as e:
        logger.exception("Rendering error occurred")
        raise click.exceptions.Exit(code=1) from e
    except Exception as e:
        logger.exception("Unexpected error occurred during rendering.")

        raise click.exceptions.Exit(code=1) from e
