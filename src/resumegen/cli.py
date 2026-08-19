import logging
import os
from pathlib import Path

import click
import litellm
import pikepdf
from pydantic import ValidationError

from resumegen import (
    Config,
    DocumentMetadata,
    PdfError,
    RenderError,
    ResumeData,
    render_html,
    render_pdf,
    scan_accessibility,
    tailor_resume,
)
from resumegen._bootstrap import bootstrap
from resumegen._core.config import (
    RESUMEGEN_DEFAULT_CONFIG_PATH,
    load_yaml_to_data_model,
)
from resumegen._core.logging import color_message, setup_logging

bootstrap()
logger = logging.getLogger(__name__)
setup_logging(logger)


def common_options(f) -> click.Command:
    f = click.option(
        "--log-level",
        envvar="RESUMEGEN_LOG_LEVEL",
        default=None,
        help="Logging level (e.g., INFO, DEBUG).",
    )(f)
    f = click.option(
        "--log-file",
        envvar="RESUMEGEN_LOG_FILE",
        default=None,
        type=click.Path(path_type=Path),
        help="Path to the log file.",
    )(f)
    f = click.option(
        "--output-dir",
        default=None,
        type=click.Path(exists=False, file_okay=False, dir_okay=True, path_type=Path),
        help="Directory to save the generated data.",
    )(f)
    f = click.option(
        "-c",
        "--config",
        "config_path",
        default=RESUMEGEN_DEFAULT_CONFIG_PATH,
        type=click.Path(exists=True, dir_okay=False, path_type=Path),
        show_default=False,
        help="Path to the configuration file. "
        "Defaults to ~/.config/resumegen/config.yaml",
    )(f)
    return f


def _override_logging_options(log_level: str | None, log_file: Path | None):
    logger = logging.getLogger(__name__)
    if log_level:
        logger.setLevel(log_level)
    if log_file:
        for handler in list(logger.handlers):
            if isinstance(handler, logging.FileHandler):
                logger.removeHandler(handler)
                handler.close()
        logger.addHandler(logging.FileHandler(log_file))


@click.command()
@common_options
@click.argument(
    "data_file",
    type=click.Path(path_type=Path, dir_okay=False, exists=True),
    default="-",
)
@click.option(
    "--html",
    "html_only",
    is_flag=True,
    default=False,
    help="Render HTML only, no PDF generation.",
)
@click.option("--output-template", type=str, help="Template for the output filename.")
@click.option(
    "--force",
    "-f",
    "overwrite_existing",
    type=bool,
    is_flag=True,
    default=False,
    help="Overwrite existing files.",
)
@click.option(
    "--template-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    help="Directory containing the templates.",
)
@click.option(
    "--template-name",
    type=str,
    help="Name of the template relative to "
    "the template directory to use for rendering.",
)
@click.option("document_author", "--author", type=str, help="Author of the document.")
@click.option("document_title", "--title", type=str, help="Title of the document.")
def render(
    data_file: Path,
    log_level: str | None,
    log_file: Path | None,
    output_dir: Path | None,
    output_template: str | None,
    overwrite_existing: bool,
    template_dir: Path | None,
    template_name: str | None,
    document_author: str | None,
    document_title: str | None,
    html_only: bool,
    config_path: Path,
):
    """
    data_file reads from stdin or takes a file path
    """
    _override_logging_options(log_level, log_file)
    try:
        config_data = load_yaml_to_data_model(config_path, Config)

        click.echo(color_message("⚙️  Configuration loaded successfully!", "green"))
        logger.debug("Configuration data: %s", config_data)

        resume_data = load_yaml_to_data_model(data_file, ResumeData)

        click.echo(color_message("🗄️  Resume data loaded successfully!", "green"))
        logger.debug("Resume data loaded: %s", resume_data)

        document_metadata = DocumentMetadata(
            author=document_author or resume_data.document_metadata.author,
            title=document_title or resume_data.document_metadata.title,
            language=resume_data.document_metadata.language,
            description=resume_data.document_metadata.description,
            keywords=resume_data.document_metadata.keywords,
        )

        logger.debug("Document Metadata object: %s", document_metadata)

        working_template_dir = template_dir or config_data.template_dir
        working_template_name = template_name or config_data.template_name
        working_output_dir = output_dir or config_data.output_dir
        working_output_filename = output_template or config_data.output_filename

        if html_only:
            click.echo(color_message("🖨️  Rendering HTML only...", "cyan"))
            output = render_html(
                resume_data,
                working_output_dir,
                working_output_filename,
                working_template_name,
                working_template_dir,
            )
            click.echo(
                color_message(
                    "👻  HTML generated at: "
                    f"{output.resolve() if isinstance(output, Path) else output}",
                    "green",
                )
            )
        else:
            click.echo(color_message("🖨️  Rendering PDF...", "cyan"))
            output, report = render_pdf(
                resume_data,
                working_output_dir,
                working_output_filename,
                working_template_name,
                working_template_dir,
                overwrite_existing or config_data.overwrite_existing,
            )
            click.echo(
                color_message(f"👻  PDF generated at: {output.resolve()}", "green")
            )
            if report:
                click.echo("🦾  Accessibility report:")
                click.echo(report.get_report_string())

    except ValidationError as e:
        logger.error(f"Data model validation failed: {e}")
        logger.error(
            "Ensure your data and configuration files match the expected schema."
        )
        raise click.exceptions.Exit(code=1) from e
    except RenderError as e:
        logger.error("Rendering failed: %s", e)
        raise click.exceptions.Exit(code=1) from e
    except PdfError as e:
        logger.error("PDF manipulation failed: %s", e)
        raise click.exceptions.Exit(code=1) from e
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise click.exceptions.Exit(code=1) from e


@click.command()
@common_options
@click.argument(
    "master_data_file",
    type=click.Path(path_type=Path, dir_okay=False, exists=True),
)
@click.argument(
    "job_description_file",
    type=click.Path(path_type=Path, dir_okay=False, exists=True),
)
@click.option(
    "--model",
    type=str,
    help="Language model to use for tailoring the resume. "
    "Required to be set via an environment variable, "
    "in the config file, or as a command-line option.",
    envvar="RESUMEGEN_MODEL",
)
@click.option(
    "--base-url",
    type=str,
    help="Base URL for the language model API. "
    "Required for generic models. "
    "Check the litellm documentation for details on how to set this up.",
    envvar="RESUMEGEN_BASE_URL",
)
@click.option(
    "--track-cost",
    is_flag=True,
    default=False,
    help="Track the cost of API calls to the language model. ",
)
@click.option(
    "--job-title",
    type=str,
    help="Job title used in the output filename."
    " If not provided, the first line of the job description will be used.",
)
@click.option(
    "--save/--no-save",
    "save_to_file",
    is_flag=True,
    default=True,
    help="Save the tailored data to a file. "
    "If not set, the tailored data will be returned as a string.",
)
@click.option(
    "--output",
    "-o",
    "output_filename",
    type=str,
    help="Override the default output filename. "
    "Setting this will override the '--save' option. "
    "Setting this will ignore the job title and "
    "job description for filename generation."
    "The filename can use the placeholders {date}, {job_title}, "
    "{model}, and {first_line} for dynamic content. "
    "For example: 'tailored_resume_{job_title}_{date}.yaml'.",
)
def tailor(
    master_data_file: Path,
    job_description_file: Path,
    job_title: str | None,
    model: str | None,
    base_url: str | None,
    track_cost: bool,
    save_to_file: bool,
    log_level: str | None,
    log_file: Path | None,
    output_dir: Path | None,
    config_path: Path,
    output_filename: str | None = None,
):
    _override_logging_options(log_level, log_file)
    try:
        app_config = load_yaml_to_data_model(config_path, Config)
        logger.debug("Configuration loaded.")
        tailor_model = model or app_config.model or os.getenv("RESUMEGEN_MODEL", "")
        result = tailor_resume(
            master_data_file,
            job_description_file,
            output_dir or app_config.output_dir,
            tailor_model,
            track_cost,
            save_to_file,
            job_title,
            base_url or app_config.base_url,
            output_filename,
        )
        if save_to_file:
            click.echo(color_message(f"💾  Tailored data saved to: {result}", "green"))
        else:
            click.echo(result)
    except ValidationError as e:
        logger.error(f"Data model validation failed: {e}")
        logger.error(
            "Ensure your data and configuration files match the expected schema."
        )
        raise click.exceptions.Exit(code=1) from e
    except ValueError as e:
        logger.error(f"Tailoring failed: {e}")
        raise click.exceptions.Exit(code=1) from e
    except litellm.BadRequestError as e:  # type: ignore
        logger.error(f"Language model request failed: {e}")
        raise click.exceptions.Exit(code=1) from e
    except litellm.Timeout as e:  # type: ignore
        logger.error(f"Language model request timed out: {e}")
        raise click.exceptions.Exit(code=1) from e
    except litellm.RateLimitError as e:  # type: ignore
        logger.error(f"Language model rate limit exceeded: {e}")
        raise click.exceptions.Exit(code=1) from e
    except litellm.BudgetExceededError as e:  # type: ignore
        logger.error(f"Language model budget exceeded: {e}")
        raise click.exceptions.Exit(code=1) from e
    except litellm.APIError as e:  # type: ignore
        logger.error(f"Language model API error: {e}")
        raise click.exceptions.Exit(code=1) from e
    except Exception as e:
        logger.exception(f"Tailoring failed with the following error: {e}")
        raise click.exceptions.Exit(code=1) from e


@click.command()
@click.argument(
    "pdf_file",
    type=click.Path(path_type=Path, dir_okay=False, exists=True),
)
def scan_pdf(pdf_file):
    """
    Scan a PDF for accessibility issues.
    """
    try:
        click.echo(
            color_message("🦾  Scanning PDF for accessibility issues...", "cyan")
        )
        with pikepdf.open(pdf_file) as pdf:
            report = scan_accessibility(pdf)
        click.echo(report.get_report_string())
    except PdfError as e:
        logger.error(f"PDF accessibility scan failed: {e}")
        raise click.exceptions.Exit(code=1) from e
    except Exception as e:
        logger.exception(f"Unexpected error during PDF scan: {e}")
        raise click.exceptions.Exit(code=1) from e


app = click.Group(commands={"render": render, "tailor": tailor, "scan-pdf": scan_pdf})

if __name__ == "__main__":  # pragma no cover
    app()
