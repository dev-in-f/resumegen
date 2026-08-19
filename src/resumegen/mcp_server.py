from importlib import resources
from pathlib import Path

import pikepdf
import yaml
from mcp.server.elicitation import AcceptedElicitation
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.prompts import base
from pydantic import BaseModel

from resumegen._cli.shared import _load_yaml_to_data_model
from resumegen._core.accessibility import AccessibilityReport, scan_accessibility
from resumegen._core.config import (
    RESUMEGEN_DATA_DIR,
    Config,
    ResumeData,
)
from resumegen._core.pdf import render_pdf

mcp = FastMCP("resumegen")


class RevisionFeedback(BaseModel):
    satisfied: bool = True
    feedback: str = ""


class SessionConfigElicit(BaseModel):
    output_dir: str = str(RESUMEGEN_DATA_DIR / "output")
    output_filename: str = "{author}_resume_{date}.pdf"
    template_name: str = "template.html.j2"
    overwrite_existing: bool = False


@mcp.prompt("Tailor Resume Data")
def tailor_resume_data_prompt(job_description: str) -> list[base.Message]:
    return [
        base.UserMessage(
            "Using my master resume data and a job description, "
            "generate a tailored resume YAML for that job matching"
            " the correct schema. You can read the schema using the"
            " get_schema tool and validate the YAML with the"
            " validate_resume_yaml tool. You can also use the"
            " get_example_yaml tool to see examples of valid YAML."
        ),
        base.UserMessage(job_description),
        base.AssistantMessage(
            "Let me verify I have all the information I need to "
            "generate a tailored resume YAML. "
            "I will use the master resume data and the job description "
            "to generate a tailored resume YAML that matches the correct schema. "
            "I will then validate the YAML using the validate_resume_yaml tool "
            "and provide you with the result."
        ),
    ]


@mcp.tool()
async def generate_resume(resume_data_path: str, ctx: Context) -> str:
    """
    Generate a PDF resume from YAML data matching the ResumeData schema.
    Returns the path to the generated PDF.
    Accessibility is run during the generation process and any issues are logged.
    You can use the check_accessibility tool to scan an existing
    PDF for accessibility issues.
    """
    try:
        result = await ctx.elicit(
            message=(
                "Configure resume generation options (leave blank to use defaults):"
            ),
            schema=SessionConfigElicit,
        )
        cfg = (
            Config(**result.data.model_dump())
            if isinstance(result, AcceptedElicitation)
            else Config()
        )
    except Exception:
        cfg = Config()
    resume_data: ResumeData = _load_yaml_to_data_model(
        Path(resume_data_path), ResumeData
    )
    with resources.path("resumegen", "templates") as template_dir:
        out, report = render_pdf(
            template_dir=template_dir,
            template_name=cfg.template_name,
            filename_template=cfg.output_filename,
            output_dir=cfg.output_dir,
            resume_data=resume_data,
            overwrite_existing=cfg.overwrite_existing,
        )

    return (
        f"Resume output to: {out}\nAccessibility report:"
        f"\n{
            report.get_report_string() if report else 'No accessibility issues found.'
        }"
    )


@mcp.tool()
def write_data_yaml(yaml_content: str, filename: str = "resume.yaml") -> str:
    """
    Write YAML content to the resumegen data directory under data/<filename>
    and return the file path. Use this before calling generate_resume or
    tailor_resume_data when you don't have an existing file.
    The filename should match the data type.
    """
    out = RESUMEGEN_DATA_DIR / "data" / filename
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml_content)
    return str(out)


@mcp.tool()
def validate_resume_yaml(yaml_file: str) -> str:
    """
    Validate a resume YAML file (by path) against the schema and return any errors.
    """
    try:
        _load_yaml_to_data_model(Path(yaml_file), ResumeData)
    except (ValueError, yaml.YAMLError, OSError) as e:
        return f"Validation failed: {e}"
    else:
        return "YAML is valid."


@mcp.tool()
def check_accessibility(pdf_path: str) -> str:
    """
    Scan an existing PDF for accessibility issues
    """
    with pikepdf.open(pdf_path) as pdf:
        report: AccessibilityReport = scan_accessibility(pdf)
    if not report.issues:
        return "No accessibility issues found."
    return report.get_report_string()


@mcp.resource("resumegen://examples/{name}")
def get_example_yaml(name: str) -> str:
    """
    Get an example YAML config by name.
    """
    with resources.path("resumegen", f"examples/{name}.yaml") as path:
        if not path.exists():
            return f"Example '{name}' not found."
        return path.read_text()


@mcp.tool()
def get_example_yaml_tool(name: str) -> str:
    """
    Get an example YAML config by name as an EmbeddedResource.
    """
    return get_example_yaml(name)


@mcp.resource("resumegen://schemas/{name}")
def get_schema(name: str) -> str:
    """
    Get a JSON schema by name.
    """
    with resources.path("resumegen", f"schemas/{name}.json") as path:
        if not path.exists():
            return f"Schema '{name}' not found."
        return path.read_text()


@mcp.tool()
def get_schema_tool(name: str) -> str:
    """
    Get a JSON schema by name as an EmbeddedResource.
    """
    return get_schema(name)


@mcp.resource("resumegen://examples/")
def list_examples() -> str:
    """
    List available example YAML configs.
    """
    with resources.path("resumegen", "examples") as examples_path:
        examples = [p.stem for p in examples_path.glob("*.yaml")]
        if examples == []:
            return f"Error: No examples found. Searched: {examples_path.resolve()}"
    return "\n".join(examples)


@mcp.tool()
def list_examples_tool() -> str:
    """
    List available example YAML configs as a tool.
    """
    return list_examples()


@mcp.resource("resumegen://schemas/")
def list_schemas() -> str:
    """
    List available JSON schemas.
    """
    with resources.path("resumegen", "schemas") as schemas_path:
        schemas = [p.stem for p in schemas_path.glob("*.json")]
    if schemas == []:
        return f"Error: No schemas found. Searched: {schemas_path.resolve()}"
    return "\n".join(schemas)


@mcp.tool()
def list_schemas_tool() -> str:
    """
    List available JSON schemas as a tool.
    """
    return list_schemas()


@mcp.resource("resumegen://fs/list")
def list_files() -> str:
    """
    List the files in the resumegen data directory and its subdirectories.
    Data files are in the 'data' subdirectory,
    tailored YAML is in the 'tailored' subdirectory,
    and generated PDFs are in the 'pdfs' subdirectory.
    You can view the files there.
    """
    files = (
        str(path.relative_to(RESUMEGEN_DATA_DIR))
        for path in RESUMEGEN_DATA_DIR.rglob("*")
        if path.is_file()
    )
    return "\n".join(files)


@mcp.tool()
def list_files_tool() -> str:
    """
    List the files in the resumegen data directory and its subdirectories as a tool.
    Data files are in the 'data' subdirectory,
    tailored YAML is in the 'tailored' subdirectory,
    and generated PDFs are in the 'pdfs' subdirectory.
    You can view the files there.
    """
    return list_files()


if __name__ == "__main__":
    mcp.run(transport="stdio")
