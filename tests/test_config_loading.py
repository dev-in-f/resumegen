import textwrap
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.config import (
    DocumentConfig,
    DocumentMeta,
    EducationEntry,
    ExperienceEntry,
    PersonalInfo,
    ProjectEntry,
    ResumeData,
    SkillsSubsection,
    load_yaml_config,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_template(tmp_path: Path) -> Path:
    """Create a minimal template file so DocumentConfig validation passes."""
    t = tmp_path / "resume.html"
    t.write_text("<html></html>")
    return t


def minimal_resume_data() -> dict:
    return {
        "personal_info": {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "location": "New York, NY",
        }
    }


class TestDocumentMeta:
    def test_valid_minimal(self):
        m = DocumentMeta(title="My Resume", author="Jane Doe")
        assert m.title == "My Resume"
        assert m.author == "Jane Doe"
        assert m.language == "en-US"
        assert m.keywords == []

    def test_valid_full(self):
        m = DocumentMeta(
            title="Resume",
            author="Jane",
            language="fr-FR",
            keywords=["python", "ml"],
        )
        assert m.language == "fr-FR"
        assert m.keywords == ["python", "ml"]

    def test_missing_title_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            DocumentMeta(author="Jane")
        assert "title" in str(exc_info.value)

    def test_missing_author_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            DocumentMeta(title="Resume")
        assert "author" in str(exc_info.value)


class TestPersonalInfo:
    def test_valid_minimal(self):
        p = PersonalInfo(name="Jane Doe", email="jane@example.com", location="NYC")
        assert p.phone is None
        assert p.linkedin is None
        assert p.github is None

    def test_valid_full(self):
        p = PersonalInfo(
            name="Jane Doe",
            email="jane@example.com",
            location="NYC",
            phone="555-1234",
            linkedin="https://linkedin.com/in/jane",
            github="https://github.com/jane",
        )
        assert p.phone == "555-1234"
        assert p.linkedin == "https://linkedin.com/in/jane"

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            PersonalInfo(email="j@e.com", location="NYC")
        assert "name" in str(exc_info.value)

    def test_missing_email_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            PersonalInfo(name="Jane", location="NYC")
        assert "email" in str(exc_info.value)

    def test_missing_location_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            PersonalInfo(name="Jane", email="j@e.com")
        assert "location" in str(exc_info.value)


class TestSkillsSubsection:
    def test_valid(self):
        s = SkillsSubsection(title="Languages", skills=["Python", "Go"])
        assert s.title == "Languages"
        assert s.skills == ["Python", "Go"]

    def test_empty_skills_list(self):
        s = SkillsSubsection(title="Languages", skills=[])
        assert s.skills == []

    def test_missing_title_raises(self):
        with pytest.raises(ValidationError):
            SkillsSubsection(skills=["Python"])

    def test_missing_skills_raises(self):
        with pytest.raises(ValidationError):
            SkillsSubsection(title="Languages")


class TestExperienceEntry:
    def test_valid_minimal(self):
        e = ExperienceEntry(
            title="Engineer",
            company="Acme",
            location="NYC",
            start_date="2020-01",
        )
        assert e.end_date is None
        assert e.description_bullets == []

    def test_valid_full(self):
        e = ExperienceEntry(
            title="Engineer",
            company="Acme",
            location="NYC",
            start_date="2020-01",
            end_date="2023-06",
            description_bullets=["Built X", "Led Y"],
        )
        assert e.end_date == "2023-06"
        assert len(e.description_bullets) == 2

    def test_missing_required_fields_raises(self):
        with pytest.raises(ValidationError):
            ExperienceEntry(title="Engineer")


class TestProjectEntry:
    def test_valid_minimal(self):
        p = ProjectEntry(title="My Project")
        assert p.timeframe is None
        assert p.link is None
        assert p.subtitle is None
        assert p.description_bullets == []
        assert p.technologies == []

    def test_valid_full(self):
        p = ProjectEntry(
            title="My Project",
            timeframe="2024",
            link={"text": "GitHub", "url": "https://github.com/jane/proj"},
            subtitle="A cool thing",
            description_bullets=["Did X"],
            technologies=["Python", "Docker"],
        )
        assert p.technologies == ["Python", "Docker"]

    def test_missing_title_raises(self):
        with pytest.raises(ValidationError):
            ProjectEntry(subtitle="No title here")


class TestEducationEntry:
    def test_valid_minimal(self):
        e = EducationEntry(
            degree="B.S. Computer Science",
            institution="State University",
            location="Boston, MA",
        )
        assert e.completion_date is None
        assert e.gpa is None
        assert e.honors is None

    def test_valid_full(self):
        e = EducationEntry(
            degree="B.S. CS",
            institution="MIT",
            location="Cambridge, MA",
            completion_date="2022-05",
            description="Focused on ML",
            gpa="3.9",
            honors=["Dean's List", "Phi Beta Kappa"],
        )
        assert e.honors == ["Dean's List", "Phi Beta Kappa"]

    def test_missing_required_fields_raises(self):
        with pytest.raises(ValidationError):
            EducationEntry(degree="B.S.")


class TestResumeData:
    def test_valid_minimal(self):
        r = ResumeData(
            personal_info=PersonalInfo(name="Jane", email="j@e.com", location="NYC")
        )
        assert r.statement is None
        assert r.skills == []
        assert r.experiences == []
        assert r.projects == []
        assert r.education == []

    def test_full_resume(self):
        r = ResumeData(
            personal_info={"name": "Jane", "email": "j@e.com", "location": "NYC"},
            statement="Passionate engineer.",
            experiences=[
                {
                    "title": "SWE",
                    "company": "Acme",
                    "location": "NYC",
                    "start_date": "2020-01",
                }
            ],
            projects=[{"title": "Cool Project"}],
            education=[
                {
                    "degree": "B.S.",
                    "institution": "MIT",
                    "location": "Cambridge, MA",
                }
            ],
        )
        assert r.statement == "Passionate engineer."
        assert len(r.experiences) == 1
        assert len(r.projects) == 1
        assert len(r.education) == 1

    def test_missing_personal_info_raises(self):
        with pytest.raises(ValidationError):
            ResumeData()


class TestDocumentConfig:
    def test_valid(self, tmp_path):
        template = make_template(tmp_path)
        config = DocumentConfig(
            meta={"title": "Resume", "author": "Jane"},
            template=str(template),
            resume=minimal_resume_data(),
        )
        assert Path(config.template).exists()

    def test_template_path_resolved_to_absolute(self, tmp_path):
        template = make_template(tmp_path)
        config = DocumentConfig(
            meta={"title": "Resume", "author": "Jane"},
            template=str(template),
            resume=minimal_resume_data(),
        )
        assert Path(config.template).is_absolute()

    def test_nonexistent_template_raises(self, tmp_path):
        with pytest.raises(ValidationError) as exc_info:
            DocumentConfig(
                meta={"title": "Resume", "author": "Jane"},
                template=str(tmp_path / "missing.html"),
                resume=minimal_resume_data(),
            )
        assert "does not exist" in str(exc_info.value)

    def test_missing_meta_raises(self, tmp_path):
        template = make_template(tmp_path)
        with pytest.raises(ValidationError) as exc_info:
            DocumentConfig(template=str(template), resume=minimal_resume_data())
        assert "meta" in str(exc_info.value)

    def test_missing_resume_raises(self, tmp_path):
        template = make_template(tmp_path)
        with pytest.raises(ValidationError) as exc_info:
            DocumentConfig(
                meta={"title": "Resume", "author": "Jane"},
                template=str(template),
            )
        assert "resume" in str(exc_info.value)


class TestLoadYamlConfig:
    def _write_yaml(self, tmp_path: Path, content: str) -> Path:
        p = tmp_path / "config.yaml"
        p.write_text(textwrap.dedent(content))
        return p

    def test_valid_minimal_yaml(self, tmp_path):
        template = make_template(tmp_path)
        yaml_file = self._write_yaml(
            tmp_path,
            f"""\
            meta:
              title: My Resume
              author: Jane Doe
            template: {template}
            resume:
              personal_info:
                name: Jane Doe
                email: jane@example.com
                location: New York, NY
            """,
        )
        config = load_yaml_config(yaml_file)
        assert config.meta.title == "My Resume"
        assert config.resume.personal_info.name == "Jane Doe"

    def test_valid_full_yaml(self, tmp_path):
        template = make_template(tmp_path)
        yaml_file = self._write_yaml(
            tmp_path,
            f"""\
            meta:
              title: Full Resume
              author: Jane Doe
              language: en-US
              keywords:
                - python
                - devops
            template: {template}
            resume:
              personal_info:
                name: Jane Doe
                email: jane@example.com
                location: New York, NY
                phone: "555-0100"
                linkedin: https://linkedin.com/in/jane
                github: https://github.com/jane
              statement: Experienced engineer.
              skills:
                - title: Languages
                  skills:
                    - Python
                    - Go
              experiences:
                - title: Software Engineer
                  company: Acme Corp
                  location: NYC
                  start_date: "2021-01"
                  end_date: "2024-06"
                  description_bullets:
                    - Built internal tooling
              projects:
                - title: OSS Library
                  technologies:
                    - Python
              education:
                - degree: B.S. Computer Science
                  institution: State University
                  location: Boston, MA
                  gpa: "3.8"
            """,
        )
        config = load_yaml_config(yaml_file)
        assert config.meta.keywords == ["python", "devops"]
        assert config.resume.personal_info.phone == "555-0100"
        assert len(config.resume.experiences) == 1
        assert config.resume.experiences[0].company == "Acme Corp"
        assert len(config.resume.projects) == 1
        assert config.resume.education[0].gpa == "3.8"
        assert isinstance(config.resume.skills[0], SkillsSubsection)

    def test_missing_required_field_raises(self, tmp_path):
        template = make_template(tmp_path)
        yaml_file = self._write_yaml(
            tmp_path,
            f"""\
            meta:
              title: Resume
            template: {template}
            resume:
              personal_info:
                name: Jane Doe
                email: jane@example.com
                location: NYC
            """,
        )
        with pytest.raises(ValidationError) as exc_info:
            load_yaml_config(yaml_file)
        assert "author" in str(exc_info.value)

    def test_nonexistent_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_yaml_config(tmp_path / "nonexistent.yaml")

    def test_nonexistent_template_in_yaml_raises(self, tmp_path):
        yaml_file = self._write_yaml(
            tmp_path,
            """\
            meta:
              title: Resume
              author: Jane
            template: /does/not/exist.html
            resume:
              personal_info:
                name: Jane
                email: jane@example.com
                location: NYC
            """,
        )
        with pytest.raises(ValidationError) as exc_info:
            load_yaml_config(yaml_file)
        assert "does not exist" in str(exc_info.value)
