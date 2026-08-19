import logging
from pathlib import Path
from typing import Annotated

import typer

from resumegen.config import (
    AppConfig,
    DocumentConfig,
    load_yaml_config,
)
from resumegen.pdf import html_to_pdf
from resumegen.renderer import output_html, render_html, render_output_filename

app = typer.Typer()


def setup_logging(level: str, output_file: Path | None = None):
    mapping = logging.getLevelNamesMapping()
    numeric_level = mapping.get(level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(levelname)s [%(name)s] %(message)s",
        force=True,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(output_file) if output_file else logging.NullHandler(),
        ],
    )
    logging.getLogger("fontTools").setLevel(logging.ERROR)


def strip_none_objects(d: dict) -> dict:
    """Remove keys with None values from a multi-level dictionary.
    Intended for determining if a cli flag was provided, otherwise
    use default/config file
    """
    return {
        key: strip_none_objects(value) if isinstance(value, dict) else value
        for key, value in d.items()
        if value is not None
    }


def render_output_with_a11y_report(
    document_config: DocumentConfig, app_config: AppConfig
):
    html_content = render_html(document_config, app_config)
    output_path = Path(app_config.output_config.output_dir) / render_output_filename(
        document_config, app_config
    )
    report = html_to_pdf(
        html_content,
        str(app_config.template_dir),
        output_path,
        document_config.document_metadata,
        overwrite=app_config.output_config.overwrite,
    )
    report.print()


def deep_merge(base: dict, overrides: dict) -> dict:
    for key, value in overrides.items():
        if (
            (isinstance(value, dict))
            and (key in base)
            and (isinstance(base[key], dict))
        ):
            base[key] = deep_merge(base[key], value)
        else:
            base[key] = value
    return base


@app.command()
def default():
    setup_logging("INFO")
    app_config = AppConfig()
    document_config = load_yaml_config(Path(app_config.data_file), DocumentConfig)
    logging.info("Using default configuration...")
    render_output_with_a11y_report(document_config, app_config)


@app.command()
def generate(
    config: Annotated[
        str | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to the configuration file. "
            "Loads default config if not provided.",
            exists=True,
            mode="r",
        ),
    ] = None,
    data_file: Annotated[
        str | None,
        typer.Option(
            "--data",
            "-d",
            help="Path to the resume data YAML file.",
            exists=True,
            mode="r",
        ),
    ] = None,
    output_file: Annotated[
        str | None,
        typer.Option(
            "--output-file",
            "-o",
            help="Filename template for the output file. "
            "Uses default from config if not provided.",
            mode="rw",
            dir_okay=True,
            file_okay=False,
        ),
    ] = None,
    template_filename: Annotated[
        str | None,
        typer.Option(
            "--template",
            "-t",
            help="The name of the template to use relative to the template directory,"
            " defaults to `template.html.j2`",
            mode="r",
            exists=True,
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Allow overwrite of existing output file."),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Enable debug mode with verbose output.",
        ),
    ] = False,
    html: Annotated[
        bool,
        typer.Option(
            "--html",
            help="Render the template as HTML only, without generating a PDF.",
        ),
    ] = False,
    output_dir: Annotated[
        str | None,
        typer.Option(
            "--output-dir",
            help="Directory to save the generated resume. "
            "Overrides config if provided.",
        ),
    ] = None,
    template_dir: Annotated[
        str | None,
        typer.Option(
            "--template-dir",
            help="Directory containing the resume templates. "
            "Overrides config if provided.",
        ),
    ] = None,
    log_file: Annotated[
        str | None,
        typer.Option(
            "--log-file",
            help="Path to save the log file. Overrides config if provided.",
            mode="rw",
        ),
    ] = None,
):
    initial_vars = locals().values()
    setup_logging("DEBUG" if debug else "INFO", Path(log_file) if log_file else None)

    app_config_cli_args = {
        "output_config": {
            "output_dir": output_dir,
            "output_filename": output_file,
            "overwrite": force,
        },
        "template_dir": template_dir,
        "logging_config": {
            "level": "DEBUG" if debug else None,
            "file": log_file,
        },
        "data_file": data_file,
    }

    # keep this dictionary in case we add more overrides later
    document_config_cli_args = {
        "template_path": template_filename,
    }

    if not any(initial_vars):
        confirm = typer.confirm(
            "No CLI arguments provided, do you want to run with default config values?"
            " (You can bypass this check by running `resumegen default`)",
            default=False,
        )
        if not confirm:
            typer.echo("Aborting. Please provide CLI arguments or a config file.")
            raise typer.Exit(code=1)
        else:
            default()
            return

    app_config_raw = (
        load_yaml_config(Path(config), AppConfig) if config else AppConfig()
    )
    app_config = AppConfig.model_validate(
        deep_merge(app_config_raw.model_dump(), strip_none_objects(app_config_cli_args))
    )
    log_level = "DEBUG" if debug else app_config.logging_config.level
    if log_file:
        log_path = Path(log_file)
    elif app_config.logging_config.file:
        log_path = Path(app_config.logging_config.file)
    else:
        log_path = None
    setup_logging(log_level, log_path)

    document_config = load_yaml_config(Path(app_config.data_file), DocumentConfig)
    document_config = DocumentConfig.model_validate(
        deep_merge(
            document_config.model_dump(), strip_none_objects(document_config_cli_args)
        )
    )

    logging.info("Document configuration loaded...")

    output_filename = render_output_filename(document_config, app_config)
    output_path = Path(app_config.output_config.output_dir) / output_filename

    if html:
        logging.info(f"Output will be saved to: {output_path.with_suffix('.html')}")
        output_html(document_config, app_config)
    else:
        render_output_with_a11y_report(document_config, app_config)
