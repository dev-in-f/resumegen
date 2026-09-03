from resumegen._core.accessibility import AccessibilityReport, scan_accessibility
from resumegen._core.config import (
    Config,
    DisplayLink,
    DocumentMetadata,
    EducationEntry,
    ExperienceEntry,
    MasterData,
    MasterProjectEntry,
    MasterSkillEntry,
    PersonalInfo,
    ProjectEntry,
    ResumeData,
    SkillsSubsection,
)
from resumegen._core.exceptions import MetadataInjectionError, PdfError, RenderError
from resumegen._core.html_rendering import render_html
from resumegen._core.pdf import render_pdf
from resumegen._core.score import ScoreReport, score_master_data
from resumegen._core.tailor import tailor_resume

__all__ = [
    "AccessibilityReport",
    "Config",
    "DisplayLink",
    "DocumentMetadata",
    "EducationEntry",
    "ExperienceEntry",
    "MasterData",
    "MasterProjectEntry",
    "MasterSkillEntry",
    "MetadataInjectionError",
    "PdfError",
    "PersonalInfo",
    "ProjectEntry",
    "RenderError",
    "ResumeData",
    "ScoreReport",
    "SkillsSubsection",
    "render_html",
    "render_pdf",
    "scan_accessibility",
    "score_master_data",
    "tailor_resume",
]
