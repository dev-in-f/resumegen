import argparse
import logging
from pathlib import Path

from resumegen.config import load_yaml_config


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an accessible resume from a template and data file."
    )
    parser.add_argument(
        "--config",
        "-c",
        help="Path to the configuration file. Searches for config.yaml by default.",
        default="config.yaml",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode with verbose output."
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Path to save the generated resume. Defaults to 'resume.pdf'.",
        default="resume.pdf",
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
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(levelname)s [%(name)s] %(message)s",
    )
    logging.debug(f"Parsed arguments: {args}")
    if not Path(args.config).exists():
        logging.error(f"Configuration file not found: {args.config}")
        return
    try:
        load_yaml_config(args.config)
    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        return
    logging.info("Configuration loaded successfully.")
