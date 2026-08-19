from pathlib import Path
from typing import Optional

from pydantic import BaseModel, field_validator

# ruff: noqa: UP045


class DocumentMeta(BaseModel):
    title: str
    author: str
    language: str = "en-US"
    keywords: list[str] = []


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
    description_bullets: list[str] = []


class ProjectEntry(BaseModel):
    title: str
    timeframe: Optional[str] = None
    project_link: Optional[str] = None
    subtitle: Optional[str] = None
    description_bullets: list[str] = []
    technologies: list[str] = []


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
    skills: list[SkillsSubsection] | list[str] = []
    experiences: list[ExperienceEntry] = []
    projects: list[ProjectEntry] = []
    education: list[EducationEntry] = []


class DocumentConfig(BaseModel):
    meta: DocumentMeta
    template: Path

    @field_validator("template")
    @classmethod
    def template_must_exist(cls, v: Path) -> str:
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Template file does not exist: {v}")
        return str(path.resolve())

    resume: ResumeData


def load_yaml_config(file_path: Path) -> DocumentConfig:
    import yaml

    with open(file_path) as f:
        data = yaml.safe_load(f)
    return DocumentConfig(**data)
