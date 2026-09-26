import logging
from datetime import datetime
from importlib import resources
from pathlib import Path

import litellm
from litellm import completion

from resumegen._core.formatting import _sanitize_filename_component
from resumegen._core.llm_utils import _build_system_prompt, _track_cost

logger = logging.getLogger(__name__)


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
    master_data: str,
    job_description: str,
    output_dir: Path,
    model: str,
    base_url: str | None = None,
    job_title: str | None = None,
    track_cost: bool = False,
    save_to_file: bool = True,
    output_filename: str | None = None,
    overwrite_existing: bool = False,
    feedback: bool = False,
    max_tokens: int = 4000,
) -> tuple[str, Path | None]:
    if model.strip(" ") == "":
        raise ValueError(
            "Model parameter is not set. "
            "Please set it to the model you want to use for tailoring resumes."
        )
    with resources.path("resumegen", "schemas/resume-data.json") as schema_path:
        schema = schema_path.read_text()

    litellm.success_callback = [_track_cost] if track_cost else []
    response = completion(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {
                "role": "system",
                "content": _build_system_prompt("tailor.txt.j2", feedback),
            },
            {
                "role": "user",
                "content": f"Master Resume Data:\n{master_data}\n\n"
                f"Job Description:\n{job_description}"
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
            "job_description_text": job_description,
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
