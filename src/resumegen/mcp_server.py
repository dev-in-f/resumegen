import tempfile
from pathlib import Path

import pikepdf
from mcp.server.fastmcp import FastMCP

from resumegen.accessibility import AccessibilityReport, scan_accessibility
from resumegen.config import AppConfig, DocumentConfig, OutputConfig, load_yaml_config
from resumegen.pdf import render_pdf

mcp = FastMCP("resumegen")

BASE_DIR = Path(__file__).parent
EXAMPLES_DIR = BASE_DIR / "examples"
SCHEMAS_DIR = BASE_DIR / "schemas"


@mcp.tool()
def generate_resume(yaml_content: str, output_path: str) -> str:
    """
    Generate a PDF resume from a YAML string.
    Returns the path to the output PDF file.
    """
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w") as f:
        f.write(yaml_content)
        tmp_path = Path(f.name)
    doc_config = load_yaml_config(tmp_path, DocumentConfig)
    app_config = AppConfig(output_config=OutputConfig(output_dir=Path(output_path)))
    out = render_pdf(app_config, doc_config)
    return f"PDF written to: {out.resolve()}"


@mcp.tool()
def validate_resume_yaml(yaml_content: str) -> str:
    """
    Validate a resume YAML config against the schema and return any errors.
    """
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w") as f:
        f.write(yaml_content)
        tmp_path = Path(f.name)

    try:
        load_yaml_config(tmp_path, DocumentConfig)
        return "YAML is valid."
    except SystemExit:
        return "Validation failed - check schema errors above."


@mcp.tool()
def check_accessibility(pdf_path: str) -> str:
    """
    Scan an existing PDF for accessibility issues
    """
    with pikepdf.open(pdf_path) as pdf:
        report: AccessibilityReport = scan_accessibility(pdf)
    if not report.issues:
        return "No accessibility issues found."
    else:
        return report.get_report()


@mcp.resource("resumegen://examples/{name}")
def get_example_yaml(name: str) -> str:
    """
    Get an example YAML config by name.
    """
    path = EXAMPLES_DIR / f"{name}.yaml"
    if not path.exists():
        return f"Example '{name}' not found."
    return path.read_text()


@mcp.resource("resumegen://schemas/{name}")
def get_schema(name: str) -> str:
    """
    Get a JSON schema by name.
    """
    path = SCHEMAS_DIR / f"{name}.json"
    if not path.exists():
        return f"Schema '{name}' not found."
    return path.read_text()


@mcp.resource("resumegen://schemas/")
def list_examples() -> str:
    """
    List available example YAML configs.
    """
    examples = [p.stem for p in EXAMPLES_DIR.glob("*.yaml")]
    return "\n".join(examples)


@mcp.resource("resumegen://schemas/")
def list_schemas() -> str:
    """
    List available JSON schemas.
    """
    schemas = [p.stem for p in SCHEMAS_DIR.glob("*.json")]
    return "\n".join(schemas)


def main():
    mcp.run()
