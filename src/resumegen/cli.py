import logging
from pathlib import Path
from typing import Annotated

import typer

from resumegen.config import (
    RESUMEGEN_DEFAULT_CONFIG_PATH,
    Config,
    DocumentMetadata,
    ResumeData,
    load_yaml_to_data_model,
)
from resumegen.pdf import render_pdf
from resumegen.renderer import output_html

app = typer.Typer()


def setup_logging(level: str, log_file: Path | None = None) -> None:
    mapping = logging.getLevelNamesMapping()
    numeric_level = mapping.get(level.upper(), logging.INFO)
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        force=True,
        handlers=handlers,
    )


@app.command()
def main(
    data_file: Annotated[Path, typer.Argument(help="Path to the data file.")],
    log_level: Annotated[
        str | None,
        typer.Option(
            "--log-level",
            help="Logging level (e.g., INFO, DEBUG).",
            envvar="RESUMEGEN_LOG_LEVEL",
        ),
    ] = None,
    log_file: Annotated[
        Path | None,
        typer.Option(
            help="Path to the log file.", envvar="RESUMEGEN_LOG_FILE", mode="rw"
        ),
    ] = None,
    output_dir: Annotated[
        Path | None,
        typer.Option(
            "--output-dir",
            help="Directory to save the generated resume.",
            envvar="RESUMEGEN_OUTPUT_DIR",
            exists=True,
            file_okay=False,
            dir_okay=True,
        ),
    ] = None,
    output_template: Annotated[
        str | None,
        typer.Option(
            "--output-template",
            help="Filename template for the generated resume.",
            envvar="RESUMEGEN_OUTPUT_FILENAME",
        ),
    ] = None,
    overwrite_existing: Annotated[
        bool,
        typer.Option("--force", "-f", help="Allow overwrite of existing output file."),
    ] = False,
    template_dir: Annotated[
        Path | None,
        typer.Option(
            "--template-dir",
            help="Directory containing the resume templates.",
            envvar="RESUMEGEN_TEMPLATE_DIR",
        ),
    ] = None,
    template_name: Annotated[
        str | None,
        typer.Option(
            "-t",
            "--template",
            help="Filename of the resume template to use.",
            envvar="RESUMEGEN_TEMPLATE_FILENAME",
        ),
    ] = None,
    document_author: Annotated[
        str | None, typer.Option("--author", help="Author of the resume.")
    ] = None,
    document_title: Annotated[
        str | None, typer.Option("--title", help="Title of the resume.")
    ] = None,
    html_only: Annotated[
        bool, typer.Option("--html", help="Render HTML only, no PDF generation.")
    ] = False,
    config_path: Annotated[
        Path,
        typer.Option(
            "-c",
            "--config",
            help="Path to the configuration file.",
            exists=True,
            mode="r",
            dir_okay=False,
            envvar="RESUMEGEN_DEFAULT_CONFIG_PATH",
        ),
    ] = RESUMEGEN_DEFAULT_CONFIG_PATH,
):
    try:
        config_data = load_yaml_to_data_model(config_path, Config)
        setup_logging(
            log_level or config_data.log_level,
            log_file or config_data.log_file,
        )
        logging.info("Configuration loaded successfully.")
        logging.debug(f"Configuration data: {config_data}")
        resume_data = load_yaml_to_data_model(data_file, ResumeData)
        logging.info("Resume data loaded successfully.")
        logging.debug(f"Resume data loaded: {resume_data}")
        resume_metadata = resume_data.document_metadata
        document_metadata = DocumentMetadata(
            author=document_author or resume_metadata.author,
            title=document_title or resume_metadata.title,
            language=resume_metadata.language,
            description=resume_metadata.description,
            keywords=resume_metadata.keywords,
        )

        logging.debug(f"Final document metadata: {document_metadata}")
        working_template_dir = template_dir or config_data.template_dir
        working_template_name = template_name or config_data.template_name
        working_output_dir = output_dir or config_data.output_dir
        working_output_filename = output_template or config_data.output_filename

        if html_only:
            logging.info("Rendering HTML only...")
            output = output_html(
                working_template_dir,
                working_template_name,
                document_metadata,
                resume_data,
                working_output_filename,
                working_output_dir,
            )
            logging.info(f"HTML generated at: {output.resolve()}")
        else:
            logging.info("Rendering PDF...")
            output, report = render_pdf(
                working_template_dir,
                working_template_name,
                working_output_filename,
                working_output_dir,
                resume_data,
                overwrite_existing or config_data.overwrite_existing,
            )
            logging.info(f"PDF generated at: {output.resolve()}")
            if report:
                logging.info("Accessibility report:")
                report.print()

    except Exception as e:
        logging.exception(f"Failed to generate resume: {e}")
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()
