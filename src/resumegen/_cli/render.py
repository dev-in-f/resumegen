import logging
from pathlib import Path

import click
from pydantic import ValidationError

from resumegen._cli.shared import (
    _load_yaml_to_data_model,
    _override_logging_options,
    logging_options,
    render_options,
)
from resumegen._core.config import (
    Config,
    DocumentMetadata,
    ResumeData,
)
from resumegen._core.exceptions import PdfError, RenderError
from resumegen._core.html_rendering import render_html
from resumegen._core.logging import color_message
from resumegen._core.pdf import render_pdf

logger = logging.getLogger("resumegen.cli")


@click.command()
@render_options
@logging_options
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
@click.option(
    "-o",
    "--output",
    "output_filename_template",
    type=str,
    help="Template for the output filename. "
    "Supported placeholders: {date}, {author}, {title}, {language},"
    " {description}, {keywords}. (Matches DocumentMetadata)",
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
@click.option(
    "--save-html/--no-save-html",
    "save_to_file",
    is_flag=True,
    default=True,
    help="Save the rendered HTML to a file."
    "If not set, the rendered HTML will be output to stdout.",
)
@click.option("document_author", "--author", type=str, help="Author of the document.")
@click.option("document_title", "--title", type=str, help="Title of the document.")
def render(
    data_file: Path,
    log_level: str | None,
    log_file: Path | None,
    verbose: bool,
    output_dir: Path | None,
    output_filename_template: str | None,
    overwrite_existing: bool,
    template_dir: Path | None,
    template_name: str | None,
    document_author: str | None,
    document_title: str | None,
    html_only: bool,
    config_path: Path,
    save_to_file: bool = True,
):
    """Render a resume from a YAML data file into a PDF using a Jinja2 template.
    DATA_FILE reads from stdin or takes a file path
    """
    _override_logging_options(log_level, log_file, verbose)
    try:
        config_data = _load_yaml_to_data_model(config_path, Config)

        click.echo(color_message("⚙️  Configuration loaded successfully!", "green"))
        logger.debug("Configuration data: %s", config_data)

        resume_data = _load_yaml_to_data_model(data_file, ResumeData)

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
        working_output_filename = (
            output_filename_template or config_data.output_filename
        )

        if html_only:
            click.echo(color_message("🖨️  Rendering HTML only...", "cyan"))
            output = render_html(
                resume_data,
                working_output_dir,
                working_output_filename,
                working_template_name,
                working_template_dir,
                save_to_file,
                overwrite_existing,
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
        logger.exception("Data model validation failed.")
        logger.warning(
            "Ensure your data and configuration files match the expected schema."
        )
        raise click.exceptions.Exit(code=1) from e
    except RenderError as e:
        logger.exception("Rendering failed.")
        raise click.exceptions.Exit(code=1) from e
    except PdfError as e:
        logger.exception("PDF manipulation failed.")
        raise click.exceptions.Exit(code=1) from e
    except Exception as e:
        logger.exception("Unexpected error.")
        raise click.exceptions.Exit(code=1) from e
