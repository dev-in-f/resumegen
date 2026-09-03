import logging
from importlib import resources

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)


def _track_cost(kwargs, completion_response, start_time, end_time):
    cost = kwargs.get("response_cost")
    if cost:
        logger.info("Cost of the request: $%f", cost)
    else:
        logger.info("Cost information not available in the response.")


def _build_system_prompt(template_name: str, feedback: bool = False) -> str:
    with (
        resources.path(
            "resumegen", "schemas/master-data.json"
        ) as master_resume_schema_path,
        resources.path("resumegen", "prompts") as prompts_dir,
    ):
        master_resume_schema = master_resume_schema_path.read_text()
        env = Environment(loader=FileSystemLoader(prompts_dir), autoescape=True)
        template = env.get_template(template_name)
        return template.render(
            master_resume_schema=master_resume_schema, feedback=feedback
        )
