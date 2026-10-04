import logging
import os
from importlib import resources
from pathlib import Path
from typing import Optional

from platformdirs import user_config_path, user_data_path
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)
RESUMEGEN_DATA_DIR = Path(
    os.getenv("RESUMEGEN_DATA_DIR", user_data_path("resumegen", ensure_exists=True))
)
RESUMEGEN_DEFAULT_CONFIG_PATH = Path(
    os.getenv(
        "RESUMEGEN_DEFAULT_CONFIG_PATH",
        user_config_path("resumegen", ensure_exists=True) / "config.yaml",
    )
)

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


class DocumentMetadata(BaseModel):
    author: str
    title: str
    language: Optional[str] = "en-US"
    description: Optional[str] = None
    keywords: Optional[list[str]] = None


class ResumeData(BaseModel):
    document_metadata: DocumentMetadata
    personal_info: PersonalInfo
    statement: Optional[str] = None
    skill_sections: list[SkillsSubsection] = []
    experience: list[ExperienceEntry] = []
    projects: list[ProjectEntry] = []
    education: list[EducationEntry] = []


# ▄▄▄      ▄▄▄  ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄
# ████▄  ▄████ ███▀▀▀▀▀ ███▀▀███▄
# ███▀████▀███ ███      ███▄▄███▀
# ███  ▀▀  ███ ███      ███▀▀▀▀
# ███      ███ ▀███████ ███


class SessionConfig(BaseModel):
    output_dir: Path = RESUMEGEN_DATA_DIR / "output"
    output_filename: str = "{author}_resume_{date}.pdf"
    template_name: str = "template.html.j2"
    overwrite_existing: bool = False


# ▄▄▄      ▄▄▄                                 ▄▄▄▄▄▄
# ████▄  ▄████              ██                 ███▀▀██▄        ██
# ███▀████▀███  ▀▀█▄ ▄█▀▀▀ ▀██▀▀ ▄█▀█▄ ████▄   ███  ███  ▀▀█▄ ▀██▀▀ ▀▀█▄
# ███  ▀▀  ███ ▄█▀██ ▀███▄  ██   ██▄█▀ ██ ▀▀   ███  ███ ▄█▀██  ██  ▄█▀██
# ███      ███ ▀█▄██ ▄▄▄█▀  ██   ▀█▄▄▄ ██      ██████▀  ▀█▄██  ██  ▀█▄██


class MasterProjectEntry(ProjectEntry):
    tags: list[str] = []


class MasterSkillEntry(BaseModel):
    name: str
    proficiency: Optional[int] = None
    category: Optional[str] = None

    @field_validator("proficiency")
    @classmethod
    def validate_proficiency(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError("Proficiency must be between 1 and 5")
        return v


class MasterData(BaseModel):
    projects: list[MasterProjectEntry]
    skills: list[MasterSkillEntry]
    experience: list[ExperienceEntry]
    education: list[EducationEntry]
    personal_info: PersonalInfo


#  ▄▄▄▄▄▄▄               ▄▄
# ███▀▀▀▀▀              ██  ▀▀
# ███      ▄███▄ ████▄ ▀██▀ ██  ▄████
# ███      ██ ██ ██ ██  ██  ██  ██ ██
# ▀███████ ▀███▀ ██ ██  ██  ██▄ ▀████
#                                  ██
#                                ▀▀▀


class Config(BaseModel):
    output_dir: Path = Field(
        default=RESUMEGEN_DATA_DIR / "output", validate_default=True
    )
    output_filename: str = "{author}_resume_{date}.pdf"
    overwrite_existing: bool = False
    template_dir: Path = Field(
        default_factory=lambda: Path(str(resources.files("resumegen") / "templates")),
        validate_default=True,
    )
    template_name: str = "template.html.j2"
    model: str = ""
    base_url: str = ""

    @field_validator("template_dir")
    @classmethod
    def resolve_template_dir(cls, v):
        path = Path(v)
        if not path.exists():
            logger.warning("Template directory does not exist, creating: %s", path)
            path.mkdir(parents=True, exist_ok=True)
        elif not path.is_dir():
            logger.warning(
                "Template path exists but is not a directory: %s. Using default", path
            )
            default_dir = Path(str(resources.files("resumegen") / "templates"))
            if not default_dir.exists():
                logger.info(
                    "Default template directory does not exist, creating: %s",
                    default_dir,
                )
                default_dir.mkdir(parents=True, exist_ok=True)
            return default_dir.resolve()
        return path.resolve()

    @field_validator("output_dir", mode="before")
    @classmethod
    def apply_output_dir_env_override(cls, v):
        return os.getenv("RESUMEGEN_OUTPUT_DIR") or v

    @field_validator("output_dir")
    @classmethod
    def resolve_output_dir(cls, v):
        path = Path(v)
        if not path.exists():
            logger.info("Output directory does not exist, creating: %s", path)
            path.mkdir(parents=True, exist_ok=True)
        elif not path.is_dir():
            logger.warning(
                "Output path exists but is not a directory: %s.",
                path,
            )
            output_dir = RESUMEGEN_DATA_DIR / "output"
            logger.info("Using default output directory instead: %s", output_dir)
            if not output_dir.exists():
                logger.info(
                    "Default output directory does not exist, creating: %s",
                    output_dir,
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
