import logging

import litellm
from litellm import completion
from pydantic import BaseModel, field_validator

from resumegen._core.llm_utils import _build_system_prompt, _track_cost
from resumegen._core.logging import color_message

logger = logging.getLogger(__name__)


class ScoreReport(BaseModel):
    score: int | None
    strengths: list[str] = []
    gaps: list[str] = []
    raw_response: str = ""

    def get_report_string(self) -> str:
        if self.score is None or not isinstance(self.score, int):
            logger.debug("Raw response for score report: %s", self.raw_response)
            return "No score available."

        if self.score < 50:
            color = "red"
        elif self.score < 80:
            color = "yellow"
        else:
            color = "green"
        score_text = color_message(str(self.score), color)
        report_lines = [f"\x1b[1;37mScore:\x1b[0m {score_text}"]

        def section_header(title: str) -> str:
            return f"\x1b[1;37m{title}:\x1b[0m"

        if self.strengths:
            report_lines.append(section_header("Strengths"))
            report_lines.extend(f"- {strength}" for strength in self.strengths)
        if self.gaps:
            report_lines.append(section_header("Gaps"))
            report_lines.extend(f"- {gap}" for gap in self.gaps)
        return "\n".join(report_lines)

    @field_validator("score")
    @classmethod
    def check_score(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Score must be between 0 and 100.")
        return v


def score_master_data(
    master_data: str,
    job_description: str,
    model: str,
    max_tokens: int = 4000,
    base_url: str | None = None,
    track_cost: bool = False,
) -> str:
    litellm.success_callback = [_track_cost] if track_cost else []
    response = completion(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {
                "role": "system",
                "content": _build_system_prompt("score.txt.j2"),
            },
            {
                "role": "user",
                "content": f"Master Resume Data:\n{master_data}\n\n"
                f"Job Description:\n{job_description}",
            },
        ],
        base_url=base_url,
    )
    response_text = response.choices[0].message.content  # type: ignore
    if not response_text:
        raise ValueError("Received empty response.")
    return response_text
