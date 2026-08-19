import logging
from datetime import datetime
from importlib import resources
from pathlib import Path

import litellm
from litellm import completion


def _track_cost(kwargs, completion_response, start_time, end_time):
    cost = kwargs.get("response_cost")
    if cost:
        logging.info(f"Cost of the request: ${cost:.6f}")
    else:
        logging.info("Cost information not available in the response.")


def _build_taylor_system_prompt() -> str:
    master_resume_schema = resources.path("resumegen", "schemas/master-data.json")
    return f"""
    You are an expert resume writer. You will be given:
    1. A master data file containing all of a candidate's experience, skills,
    education, and projects
      - The master data file is in YAML and conforms to the following schema:
        ```json
        {master_resume_schema}

        ```
    2. A job description for a specific role the candidate is applying to

    Your task is to produce a tailored resume YAML config that:
    - Selects the most relevant experience highlights (max 4 per role)
    - Selects the most relevant skills and projects
    - Include a tailored statement that is specific to the job description
    - Rewords highlights to mirror the language and keywords in the job description
    - Keeps all rewording truthful - do not fabricate or exaggerate any information
    - Ensure all fields are filled where possible according to the schema,
      and do not remove any required fields
    - Preserves all personal and contact information exactly as given
    - Outputs ONLY valid YAML matching the resume config schema, no preamble,
      and explanations can ONLY be included as YAML comments AND ONLY
      if they are asked for

    The output must be valid YAML that conforms to the included resume JSON schema.
    Do not wrap the YAML with a code block or fencing. Just return the raw YAML text."""


def _generate_filename(
    date: str, job_title: str | None, job_description: str | None
) -> str:
    if job_title:
        sanitized_job_title = job_title.replace(" ", "_").lower()
        return f"tailored_resume_{sanitized_job_title}_{date}.yaml"
    elif job_description:
        first_line = job_description.split("\n")[0]
        sanitized_first_line = first_line.replace(" ", "_").lower()
        return f"tailored_resume_{sanitized_first_line}_{date}.yaml"
    else:
        return f"tailored_resume_{date}.yaml"


def _save_to_file(
    output_dir: Path,
    output_filename: str | None,
    response_text: str,
    template_context: dict,
) -> Path:
    date = datetime.now().strftime("%Y-%m-%d.%H-%M")
    output_dir.mkdir(parents=True, exist_ok=True)
    if output_filename:
        output_path = output_dir / output_filename.format(
            date=date,
            job_title=template_context.get("job_title"),
            first_line=template_context.get("job_description_text", "").split("\n")[0]
            if template_context.get("job_description_text")
            else "",
            model=template_context.get("model"),
        )
    else:
        output_path = output_dir / _generate_filename(
            date,
            template_context.get("job_title"),
            template_context.get("job_description_text"),
        )
    with open(output_path, "w") as f:
        f.write(response_text)
    return output_path.resolve()


def tailor_resume(
    master_data_path: Path,
    job_description: Path | str,
    output_dir: Path,
    model: str,
    track_cost: bool = False,
    save_to_file: bool = True,
    job_title: str | None = None,
    base_url: str | None = None,
    output_filename: str | None = None,
) -> str | Path:
    if model == "":
        raise ValueError(
            "Model parameter is not set. "
            "Please set it to the model you want to use for tailoring resumes."
        )
    with resources.path("resumegen", "schemas/resume-data.json") as schema_path:
        schema = schema_path.read_text()
    with open(master_data_path) as f:
        resume_data = f.read()

    if isinstance(job_description, Path):
        with open(job_description) as f:
            job_description_text = f.read()
    else:
        job_description_text = job_description

    try:
        litellm.success_callback = [_track_cost] if track_cost else []
        response = completion(
            model=model,
            max_tokens=4000,
            messages=[
                {"role": "system", "content": _build_taylor_system_prompt()},
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
            raise ValueError("Received empty response from the model.")
        if output_filename or save_to_file:
            template_context = {
                "job_title": job_title,
                "job_description_text": job_description_text,
                "model": model,
            }
            return _save_to_file(
                output_dir, output_filename, response_text, template_context
            )
        return response_text

    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        raise


def score_master_data():
    pass
