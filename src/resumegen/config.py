import logging
import warnings
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, field_validator

# ruff: noqa: UP045


# ▄▄▄▄▄▄▄                                      ▄▄▄▄▄▄
# ███▀▀███▄                                    ███▀▀██▄        ██
# ███▄▄███▀ ▄█▀█▄ ▄█▀▀▀ ██ ██ ███▄███▄ ▄█▀█▄   ███  ███  ▀▀█▄ ▀██▀▀ ▀▀█▄
# ███▀▀██▄  ██▄█▀ ▀███▄ ██ ██ ██ ██ ██ ██▄█▀   ███  ███ ▄█▀██  ██  ▄█▀██
# ███  ▀███ ▀█▄▄▄ ▄▄▄█▀ ▀██▀█ ██ ██ ██ ▀█▄▄▄   ██████▀  ▀█▄██  ██  ▀█▄██


class PersonalInfo(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    location: str
    linkedin: Optional[str] = None
    github: Optional[str] = None


class SkillsSubsection(BaseModel):
    title: str
    skills: list[str]


class ExperienceEntry(BaseModel):
    title: str
    company: str
    location: str
    start_date: str
    end_date: Optional[str] = None
    description_bullets: list[str]


class DisplayLink(BaseModel):
    text: str
    url: str


class ProjectEntry(BaseModel):
    title: str
    timeframe: Optional[str] = None
    link: Optional[DisplayLink] = None
    subtitle: Optional[str] = None
    description_bullets: list[str]
    technologies: Optional[list[str]] = None


class EducationEntry(BaseModel):
    degree: str
    institution: str
    location: str
    completion_date: Optional[str] = None
    description: Optional[str] = None
    gpa: Optional[str] = None
    honors: Optional[list[str]] = None


class ResumeData(BaseModel):
    personal_info: PersonalInfo
    statement: Optional[str] = None
    skill_sections: list[SkillsSubsection] = []
    experience: list[ExperienceEntry] = []
    projects: list[ProjectEntry] = []
    education: list[EducationEntry] = []


#  ▄▄▄▄▄▄▄               ▄▄
# ███▀▀▀▀▀              ██  ▀▀
# ███      ▄███▄ ████▄ ▀██▀ ██  ▄████
# ███      ██ ██ ██ ██  ██  ██  ██ ██
# ▀███████ ▀███▀ ██ ██  ██  ██▄ ▀████
#                                  ██
#                                ▀▀▀


class Config(BaseModel):
    log_level: str = "INFO"
    log_file: Optional[Path] = None
    output_dir: Path = Path("output").resolve()
    output_filename: str = "{document_author}_resume_{date}.pdf"
    overwrite_existing: bool = False
    template_dir: Path = Path("templates").resolve()
    template_filename: Path = Path("template.html.j2")
    document_title: str
    document_author: str
    document_description: Optional[str] = None
    document_language: Optional[str] = "en-US"
    document_keywords: Optional[list[str]] = None

    @field_validator("template_dir")
    @classmethod
    def resolve_template_dir(cls, v):
        path = Path(v)
        if not path.exists():
            warnings.warn(
                f"Template directory does not exist, creating: {path}", stacklevel=2
            )
            path.mkdir(parents=True, exist_ok=True)
        elif not path.is_dir():
            warnings.warn(
                f"Template path exists but is not a directory: {path}. Using default",
                stacklevel=2,
            )
            default_dir = Path("templates")
            if not default_dir.exists():
                logging.info(
                    (
                        "Default template directory does"
                        f" not exist, creating: {default_dir}"
                    ),
                )
                default_dir.mkdir(parents=True, exist_ok=True)
            return default_dir.resolve()
        if not path.is_absolute():
            path = Path(__file__).parent / path
        return path.resolve()

    @field_validator("output_dir")
    @classmethod
    def resolve_output_dir(cls, v):
        path = Path(v)
        if not path.exists():
            logging.info(
                f"Output directory does not exist, creating: {path}", stacklevel=2
            )
            path.mkdir(parents=True, exist_ok=True)
        elif not path.is_dir():
            warnings.warn(
                f"Output path exists but is not a directory: {path}"
                " Using default directory 'output'",
                stacklevel=2,
            )
            output_dir = Path("output")
            if not output_dir.exists():
                logging.info(
                    f"Default output directory does not exist, creating: {output_dir}",
                )
                output_dir.mkdir(parents=True, exist_ok=True)
            return output_dir.resolve()
        return path.resolve()

    @field_validator("output_filename")
    @classmethod
    def validate_output_filename(cls, v):
        if Path(v).suffix != ".pdf":
            raise ValueError("Output filename must have a .pdf extension")
        return v

    @field_validator("log_file")
    @classmethod
    def resolve_log_file_path(cls, v):
        if v is None:
            return None
        path = Path(v)
        if not path.parent.exists():
            warnings.warn(
                f"Log file directory does not exist: {path.parent}", stacklevel=2
            )
            return None
        return path.resolve()


def load_yaml_to_data_model[T: BaseModel](file_path: Path, model: type[T]) -> T:
    with open(file_path) as f:
        data = yaml.safe_load(f)
        logging.debug(f"Loaded YAML from {file_path}: {data}")
    return model(**data)
