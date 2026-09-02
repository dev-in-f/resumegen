import logging
from datetime import datetime
from importlib import resources
from pathlib import Path

import litellm
from jinja2 import Environment, FileSystemLoader
from litellm import completion
from pydantic import BaseModel

from resumegen._core.formatting import _sanitize_filename_component
from resumegen._core.logging import color_message

logger = logging.getLogger(__name__)


class ScoreReport(BaseModel):
    score: int | None
    strengths: list[str] = []
    gaps: list[str] = []
    raw_response: str = ""

    def get_report_string(self) -> str:
        report_lines = []
        if self.score is None:
            logger.debug("Raw response for score report: %s", self.raw_response)
            return "No score available."
        match self.score:
            case score if score < 50:
                report_lines.append("Score: " + color_message(str(self.score), "red"))
            case score if 50 <= score < 80:
                report_lines.append(
                    "Score: " + color_message(str(self.score), "yellow")
                )
            case score if score >= 80:
                report_lines.append("Score: " + color_message(str(self.score), "green"))

        if self.strengths:
            report_lines.append("\x1b[1;37mStrengths:\x1b[0m")
            for strength in self.strengths:
                report_lines.extend([f"- {strength}"])
        if self.gaps:
            report_lines.append("\x1b[1;37mGaps:\x1b[0m")
            for gap in self.gaps:
                report_lines.extend([f"- {gap}"])
        return "\n".join(report_lines)


def _track_cost(kwargs, completion_response, start_time, end_time):
    cost = kwargs.get("response_cost")
    if cost:
        logger.info("Cost of the request: $%f", cost)
    else:
        logger.info("Cost information not available in the response.")


def _build_tailor_system_prompt(feedback: bool = False) -> str:
    with (
        resources.path(
            "resumegen", "schemas/master-data.json"
        ) as master_resume_schema_path,
        resources.path("resumegen", "prompts") as prompts_dir,
    ):
        master_resume_schema = master_resume_schema_path.read_text()
        env = Environment(loader=FileSystemLoader(prompts_dir), autoescape=True)
        template = env.get_template("tailor.txt.j2")
        return template.render(
            master_resume_schema=master_resume_schema, feedback=feedback
        )


def _extract_yaml_comments(text: str) -> str:
    comment_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            comment_lines.append(stripped.lstrip("#").strip())
    return "\n".join(comment_lines)


def _generate_filename(
    date: str, job_title: str | None, job_description: str | None
) -> str:
    if job_title:
        sanitized_job_title = _sanitize_filename_component(job_title)
        return f"tailored_resume_{sanitized_job_title}_{date}.yaml"
    if job_description:
        first_line = job_description.split("\n")[0]
        sanitized_first_line = _sanitize_filename_component(first_line)
        return f"tailored_resume_{sanitized_first_line}_{date}.yaml"
    return f"tailored_resume_{date}.yaml"


def _save_to_file(
    output_dir: Path,
    output_filename: str | None,
    response_text: str,
    template_context: dict,
    overwrite_existing: bool = False,
) -> Path:
    tz = datetime.now().astimezone().tzinfo
    date = datetime.now(tz).strftime("%Y-%m-%d.%H-%M")
    if output_filename:
        job_description_text = template_context.get("job_description_text") or ""
        first_line = job_description_text.split("\n")[0] if job_description_text else ""
        rendered_filename = output_filename.format(
            date=date,
            job_title=_sanitize_filename_component(
                template_context.get("job_title") or ""
            ),
            first_line=_sanitize_filename_component(first_line),
            model=_sanitize_filename_component(template_context.get("model") or ""),
        )
        output_path = output_dir / rendered_filename
    else:
        output_path = output_dir / _generate_filename(
            date,
            template_context.get("job_title"),
            template_context.get("job_description_text"),
        )
    if output_path.exists() and not overwrite_existing:
        raise FileExistsError(
            f"Output file {output_path} already exists and overwrite is disabled."
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        f.write(response_text)
    return output_path.resolve()


def tailor_resume(
    master_data_path: Path,
    job_description: Path | str,
    output_dir: Path,
    model: str,
    base_url: str | None = None,
    job_title: str | None = None,
    track_cost: bool = False,
    save_to_file: bool = True,
    output_filename: str | None = None,
    overwrite_existing: bool = False,
    feedback: bool = False,
) -> tuple[str, Path | None]:
    if model == "":
        raise ValueError(
            "Model parameter is not set. "
            "Please set it to the model you want to use for tailoring resumes."
        )
    with resources.path("resumegen", "schemas/resume-data.json") as schema_path:
        schema = schema_path.read_text()
    with master_data_path.open() as f:
        resume_data = f.read()

    if isinstance(job_description, Path):
        with job_description.open() as f:
            job_description_text = f.read()
    else:
        job_description_text = job_description

    litellm.success_callback = [_track_cost] if track_cost else []
    response = completion(
        model=model,
        max_tokens=4000,
        messages=[
            {"role": "system", "content": _build_tailor_system_prompt(feedback)},
            {
                "role": "user",
                "content": f"Master Resume Data:\n{resume_data}\n\n"
                f"Job Description:\n{job_description_text}"
                f"\n\nOutput Resume Data Schema:\n{schema}",
            },
        ],
        base_url=base_url,
    )
    response_text = response.choices[0].message.content  # type: ignore
    if not response_text:
        raise ValueError("Received empty response.")
    if save_to_file:
        template_context = {
            "job_title": job_title,
            "job_description_text": job_description_text,
            "model": model,
        }
        output_path = _save_to_file(
            output_dir,
            output_filename,
            response_text,
            template_context,
            overwrite_existing,
        )
        return response_text, output_path
    return response_text, None


def score_master_data():
    pass  # pragma: no cover
