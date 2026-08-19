import logging
import os
from pathlib import Path

import click

from resumegen.config import (
    RESUMEGEN_DEFAULT_CONFIG_PATH,
    Config,
    DocumentMetadata,
    ResumeData,
    load_yaml_to_data_model,
)
from resumegen.pdf import render_pdf
from resumegen.renderer import output_html
from resumegen.tailor import score_master_data, tailor_resume


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
        type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
        help="Directory to save the generated data.",
    )(f)
    f = click.option(
        "-c",
        "--config",
        "config_path",
        default=RESUMEGEN_DEFAULT_CONFIG_PATH,
        envvar="RESUMEGEN_DEFAULT_CONFIG_PATH",
        type=click.Path(exists=True, dir_okay=False, path_type=Path),
        show_default=False,
        help="Path to the configuration file. "
        "Defaults to ~/.config/resumegen/config.yaml",
    )(f)
    return f


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
    try:
        config_data = load_yaml_to_data_model(config_path, Config)
        env_log_file = os.getenv("RESUMEGEN_LOG_FILE")
        log_file_from_env = Path(env_log_file) if env_log_file else None

        setup_logging(
            log_level or os.getenv("RESUMEGEN_LOG_LEVEL", "INFO"),
            log_file or log_file_from_env,
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
    "-s",
    "--score",
    is_flag=True,
    default=False,
    help="Score how relevant the data from the master "
    "data file is to the job description. ",
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
    "--no-save/--save",
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
    score: bool,
    track_cost: bool,
    save_to_file: bool,
    log_level: str | None,
    log_file: Path | None,
    output_dir: Path | None,
    config_path: Path,
    output_filename: str | None = None,
) -> str | Path:
    try:
        env_log_file = os.getenv("RESUMEGEN_LOG_FILE")
        log_file_from_env = Path(env_log_file) if env_log_file else None
        setup_logging(
            log_level or os.getenv("RESUMEGEN_LOG_LEVEL", "INFO"),
            log_file or log_file_from_env if log_file_from_env else None,
        )
        app_config = load_yaml_to_data_model(config_path, Config)
        logging.debug("Configuration loaded successfully.")
        tailor_model = model or app_config.model or os.getenv("RESUMEGEN_MODEL", "")
        if score:
            logging.info("Scoring master data against job description...")
            score_master_data()
        return tailor_resume(
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

    except Exception as e:
        logging.exception(f"Tailoring failed with the following error: {e}")
        raise click.exceptions.Exit(code=1) from e


app = click.Group(commands={"render": render, "tailor": tailor})

if __name__ == "__main__":  # pragma no cover
    app()
