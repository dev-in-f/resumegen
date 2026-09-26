import logging
import os
from pathlib import Path

import click
import litellm
import yaml
from pydantic import ValidationError

from resumegen._cli.shared import (
    _load_yaml_to_data_model,
    _override_logging_options,
    llm_arguments,
    llm_options,
    logging_options,
)
from resumegen._core.config import RESUMEGEN_DEFAULT_CONFIG_PATH, Config
from resumegen._core.logging import Spinner
from resumegen._core.score import ScoreReport, score_master_data

logger = logging.getLogger("resumegen.cli")


@click.command()
@logging_options
@llm_options
@llm_arguments
@click.option(
    "-c",
    "--config",
    "config_path",
    default=RESUMEGEN_DEFAULT_CONFIG_PATH,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    show_default=False,
    help="Path to the configuration file. Defaults to ~/.config/resumegen/config.yaml",
)
def score(
    master_data_file: Path,
    job_description_file: Path,
    log_level: str | None,
    log_file: Path | None,
    verbose: bool,
    model: str | None,
    base_url: str | None,
    track_cost: bool,
    config_path: Path,
    max_tokens: int = 4000,
):
    _override_logging_options(log_level, log_file, verbose)
    try:
        app_config = _load_yaml_to_data_model(config_path, Config)
        logger.debug("Loaded configuration: %s", app_config)
        score_model = model or app_config.model or os.getenv("RESUMEGEN_MODEL", "")
        score_model_base_url = (
            base_url or app_config.base_url or os.getenv("RESUMEGEN_BASEURL", "")
        )

        if not score_model or score_model.strip() == "":
            logger.error(
                "No model specified. Please provide a model "
                "via command line, config file, "
                "or environment variable."
            )
            raise click.exceptions.Exit(code=1)  # noqa: TRY301

        with job_description_file.open() as f:
            job_description_content = f.read()
        with master_data_file.open() as f:
            master_data_content = f.read()

        with Spinner(f"📊 Scoring resume with '{score_model}'", enabled=True):
            raw_score_report = score_master_data(
                master_data_content,
                job_description_content,
                model=score_model,
                base_url=score_model_base_url,
                track_cost=track_cost,
                max_tokens=max_tokens,
            )
        score_report = yaml.safe_load(raw_score_report)
        score_report = ScoreReport.model_validate(score_report)
        click.echo(score_report.get_report_string())

    except ValidationError as e:
        logger.exception("Data model validation failed.")
        logger.warning(
            "Ensure your data and configuration files match the expected schema."
        )
        raise click.exceptions.Exit(code=1) from e
    except litellm.BadRequestError as e:  # type: ignore
        logger.exception("Language model request failed with a bad request.")
        raise click.exceptions.Exit(code=1) from e
    except litellm.Timeout as e:  # type: ignore
        logger.exception("Language model request timed out.")
        raise click.exceptions.Exit(code=1) from e
    except litellm.RateLimitError as e:  # type: ignore
        logger.exception("Language model rate limit exceeded.")
        raise click.exceptions.Exit(code=1) from e
    except litellm.BudgetExceededError as e:  # type: ignore
        logger.exception("Language model budget exceeded.")
        raise click.exceptions.Exit(code=1) from e
    except litellm.APIError as e:  # type: ignore
        logger.exception("Language model API error.")
        raise click.exceptions.Exit(code=1) from e
    except Exception as e:
        logger.exception("Unexpected error during scoring.")
        raise click.exceptions.Exit(code=1) from e
