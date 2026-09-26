import logging
from pathlib import Path

import click
import yaml
from pydantic import BaseModel

from resumegen._core.config import RESUMEGEN_DEFAULT_CONFIG_PATH
from resumegen._core.logging import LIBRARY_LOGGERS


def render_options(f) -> click.Command:
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
    return click.option(
        "--force",
        "-f",
        "overwrite_existing",
        type=bool,
        is_flag=True,
        default=False,
        help="Overwrite existing files.",
    )(f)


def logging_options(f) -> click.Command:
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
    return click.option(
        "-v",
        "--verbose",
        is_flag=True,
        default=False,
        help="Enable verbose logging (DEBUG level including imported module loggers).",
        envvar="RESUMEGEN_VERBOSE",
    )(f)


def llm_options(f) -> click.Command:
    f = click.option(
        "--model",
        type=str,
        help="Language model to use for tailoring the resume. "
        "Required to be set via an environment variable, "
        "in the config file, or as a command-line option.",
        envvar="RESUMEGEN_MODEL",
    )(f)
    f = click.option(
        "--base-url",
        type=str,
        help="Base URL for the language model API. "
        "Required for generic models. "
        "Check the litellm documentation for details on how to set this up.",
        envvar="RESUMEGEN_BASE_URL",
    )(f)
    f = click.option(
        "--max-tokens",
        type=int,
        default=4000,
        help="Maximum number of tokens to generate.",
    )(f)
    return click.option(
        "--track-cost",
        is_flag=True,
        default=False,
        help="Track the cost of API calls to the language model. ",
    )(f)


def llm_arguments(f) -> click.Command:
    f = click.argument(
        "master_data_file", type=click.Path(path_type=Path, dir_okay=False, exists=True)
    )(f)
    return click.argument(
        "job_description_file",
        type=click.Path(path_type=Path, dir_okay=False, exists=True),
    )(f)


def _override_logging_options(
    log_level: str | None, log_file: Path | None, verbose: bool = False
) -> None:
    logger = logging.getLogger("resumegen")
    if log_level:
        logger.setLevel(log_level)
        for handler in logger.handlers:
            handler.setLevel(log_level)
    if log_file:
        for handler in list(logger.handlers):
            if isinstance(handler, logging.FileHandler):
                logger.removeHandler(handler)
                handler.close()
        logger.addHandler(logging.FileHandler(log_file))
    if verbose:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
        for lib_logger in LIBRARY_LOGGERS:
            logging.getLogger(lib_logger).setLevel(logging.DEBUG)


def _load_yaml_to_data_model[T: BaseModel](file_path: Path, model: type[T]) -> T:
    """
    Load a YAML file and validate it against a Pydantic data model.
    """
    with file_path.open() as f:
        data = yaml.safe_load(f)
        return model.model_validate(data)


def _split_output_path(
    output_value: str | None, output_dir: Path | None
) -> tuple[Path | None, str | None]:
    """Split output option into directory portion and
    filename portion if that's the input format."""
    if output_value:
        path = Path(output_value)
        if path.parent != Path():
            return path.parent, path.name
        return output_dir, output_value
    return output_dir, output_value


def interactive_options(f) -> click.Command:
    f = click.option(
        "--save/--no-save",
        "-s",
        "save_to_file",
        is_flag=True,
        default=True,
        help="Write the rendered output to a file. Independent of --interactive: "
        "combine with --no-interactive to both save and print to stdout.",
    )(f)
    return click.option(
        "--interactive/--no-interactive",
        "interactive",
        is_flag=True,
        default=True,
        help="Print decorated status messages. With --no-interactive, the raw "
        "rendered content is printed to stdout instead (in addition to being "
        "saved, unless --no-save is also given), for use in scripts/pipelines.",
    )(f)
