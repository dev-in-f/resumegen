import logging
import os
from pathlib import Path

import click
import litellm
from pydantic import ValidationError

from resumegen._cli.shared import (
    _load_yaml_to_data_model,
    _override_logging_options,
    interactive_options,
    llm_arguments,
    llm_options,
    logging_options,
    render_options,
)
from resumegen._core.config import Config
from resumegen._core.logging import Spinner, color_message
from resumegen._core.tailor import (
    _extract_yaml_comments,
    tailor_resume,
)

logger = logging.getLogger("resumegen.cli")


@click.command()
@render_options
@logging_options
@interactive_options
@llm_options
@llm_arguments
@click.option(
    "--job-title",
    type=str,
    help="Job title used in the output filename."
    " If not provided, the first line of the job description will be used.",
)
@click.option(
    "-o",
    "--output-template",
    "output_filename_template",
    type=str,
    help="Override the default output filename template, optionally including a "
    "directory portion (e.g. '{job_title}/tailored.yaml'); any directory in the "
    "rendered result is created under --output-dir if it doesn't exist. The "
    "filename can use the placeholders {date}, {job_title}, {model}, and "
    "{first_line} for dynamic content.",
)
@click.option(
    "--feedback",
    is_flag=True,
    default=False,
    help="Ask the model to explain its tailoring rationale (as YAML comments "
    "in the output) and print that rationale to the console.",
)
def tailor(
    master_data_file: Path,
    job_description_file: Path,
    log_level: str | None,
    log_file: Path | None,
    verbose: bool,
    job_title: str | None,
    model: str | None,
    base_url: str | None,
    track_cost: bool,
    output_dir: Path | None,
    config_path: Path,
    overwrite_existing: bool,
    interactive: bool = True,
    save_to_file: bool = True,
    output_filename_template: str | None = None,
    feedback: bool = False,
):
    """Tailor resume data based on a job description using a LLM."""
    _override_logging_options(log_level, log_file, verbose)
    try:
        app_config = _load_yaml_to_data_model(config_path, Config)
        logger.debug("Loaded configuration: %s", app_config)
        tailor_model = model or app_config.model or os.getenv("RESUMEGEN_MODEL", "")
        working_output_dir = output_dir or app_config.output_dir

        with job_description_file.open() as f:
            job_description_content = f.read()
        with master_data_file.open() as f:
            master_data_content = f.read()

        with Spinner(
            f"🤖  Requesting tailored resume from '{tailor_model}'...",
            enabled=interactive,
        ):
            response_text, output_path = tailor_resume(
                master_data_content,
                job_description_content,
                working_output_dir,
                tailor_model,
                base_url or app_config.base_url,
                job_title,
                track_cost,
                save_to_file,
                output_filename_template,
                overwrite_existing,
                feedback,
            )
        if interactive:
            if output_path is not None:
                click.echo(
                    color_message(f"💾  Tailored data saved to: {output_path}", "green")
                )
            else:
                click.echo(color_message("💾  Tailored data:", "green"))
                click.echo(response_text)
            if feedback:
                rationale = _extract_yaml_comments(response_text)
                click.echo(color_message("🧠  Tailoring rationale:", "cyan"))
                click.echo(
                    rationale
                    or "(No rationale comments were included in the response.)"
                )
        else:
            click.echo(response_text)
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
        logger.exception("Unexpected error during tailoring.")
        raise click.exceptions.Exit(code=1) from e
