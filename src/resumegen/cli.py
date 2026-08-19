import argparse
import logging
import warnings
from pathlib import Path

from resumegen.config import (
    AppConfig,
    DocumentConfig,
    load_yaml_config,
)
from resumegen.renderer import output_html, render_html, render_output_filename


def prefer_cli_arg(cli_value, config_value):
    """Prefer the CLI argument if provided, otherwise use the config value."""
    return cli_value if cli_value is not None else config_value


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


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an accessible resume from a template and data file."
    )
    parser.add_argument(
        "--config",
        "-c",
        help="Path to the configuration file. Loads default config if not provided.",
    )
    parser.add_argument(
        "-d",
        "--data",
        help="Path to the resume data YAML file.",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode with verbose output."
    )
    parser.add_argument(
        "--output-file",
        "-o",
        help="Path to save the generated resume."
        " Uses default from config if not provided.",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Render the template as HTML only, without generating a PDF.",
    )
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    setup_logging("DEBUG" if args.debug else "INFO")

    if args.config:
        if not Path(args.config).exists() or not Path(args.config).is_file():
            logging.error(f"Configuration file not found: {args.config}")
            return
        app_config: AppConfig = load_yaml_config(Path(args.config), AppConfig)
    else:
        app_config = AppConfig()

    if args.debug:
        app_config.logging_config.level = "DEBUG"
    setup_logging(app_config.logging_config.level, app_config.logging_config.file)
    logging.info("Initial configuration loaded...")

    data_file: Path = prefer_cli_arg(args.data, app_config.data_file)

    document_config = load_yaml_config(data_file, DocumentConfig)
    logging.info("Document configuration loaded...")

    app_config.output_config.output_filename = prefer_cli_arg(
        args.output_file, app_config.output_config.output_filename
    )
    output_path = Path(app_config.output_config.output_dir) / render_output_filename(
        document_config, app_config
    )
    logging.info(f"Output will be saved to: {output_path}")
    if args.html:
        output_html(document_config, app_config)
    else:
        warnings.warn(
            "PDF generation not implemented yet, defaulting to HTML output",
            stacklevel=2,
        )
