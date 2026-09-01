import logging
from pathlib import Path

import click
import pikepdf

from resumegen._cli.shared import _override_logging_options, logging_options
from resumegen._core.accessibility import scan_accessibility
from resumegen._core.exceptions import PdfError
from resumegen._core.logging import Spinner

logger = logging.getLogger("resumegen.cli")


@click.command()
@logging_options
@click.argument(
    "pdf_file",
    type=click.Path(path_type=Path, dir_okay=False, exists=True),
)
def scan_pdf(
    pdf_file: Path, log_level: str | None, log_file: Path | None, verbose: bool
):
    """Scan a PDF for accessibility issues."""
    _override_logging_options(log_level, log_file, verbose)
    try:
        with (
            Spinner("🦾  Scanning PDF for accessibility issues..."),
            pikepdf.open(pdf_file) as pdf,
        ):
            report = scan_accessibility(pdf)
        click.echo(report.get_report_string())
    except PdfError as e:
        logger.exception("PDF accessibility scan failed.")
        raise click.exceptions.Exit(code=1) from e
    except Exception as e:
        logger.exception("Unexpected error during PDF scan.")
        raise click.exceptions.Exit(code=1) from e
