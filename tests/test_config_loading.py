import textwrap
from pathlib import Path

import pytest
from pydantic import ValidationError

from resumegen import config as resumegen_config
from resumegen.config import (
    AppConfig,
    DisplayLink,
    DocumentConfig,
    DocumentMeta,
    EducationEntry,
    ExperienceEntry,
    LoggingConfig,
    OutputConfig,
    PersonalInfo,
    ProjectEntry,
    ResumeData,
    SkillsSubsection,
    load_yaml_config,
)


def package_dir() -> Path:
    """Directory that config.py's relative-path validators resolve against."""
    return Path(resumegen_config.__file__).parent


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
        assert p.github == "https://github.com/jane"

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
        s = SkillsSubsection(title="Languages", skills="Python, Go")
        assert s.title == "Languages"
        assert s.skills == "Python, Go"

    def test_empty_skills_list(self):
        s = SkillsSubsection(title="Languages", skills="")
        assert s.skills == ""

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
        assert e.title == "Engineer"
        assert e.company == "Acme"
        assert e.location == "NYC"
        assert e.start_date == "2020-01"
        assert e.end_date == "2023-06"
        assert e.description_bullets == ["Built X", "Led Y"]

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
        assert p.title == "My Project"
        assert p.timeframe == "2024"
        assert p.link.text == "GitHub"
        assert p.link.url == "https://github.com/jane/proj"
        assert p.subtitle == "A cool thing"
        assert p.description_bullets == ["Did X"]
        assert p.technologies == ["Python", "Docker"]

    def test_missing_title_raises(self):
        with pytest.raises(ValidationError):
            ProjectEntry(subtitle="No title here")


class TestDisplayLink:
    def test_valid(self):
        link = DisplayLink(text="GitHub", url="https://github.com/jane")
        assert link.text == "GitHub"
        assert link.url == "https://github.com/jane"

    def test_missing_text_raises(self):
        with pytest.raises(ValidationError):
            DisplayLink(url="https://github.com/jane")

    def test_missing_url_raises(self):
        with pytest.raises(ValidationError):
            DisplayLink(text="GitHub")


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
        assert e.completion_date == "2022-05"
        assert e.description == "Focused on ML"
        assert e.gpa == "3.9"
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
        assert r.skill_sections == []
        assert r.experience == []
        assert r.projects == []
        assert r.education == []

    def test_full_resume(self):
        r = ResumeData(
            personal_info={"name": "Jane", "email": "j@e.com", "location": "NYC"},
            statement="Passionate engineer.",
            experience=[
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
        assert len(r.experience) == 1
        assert len(r.projects) == 1
        assert len(r.education) == 1

    def test_missing_personal_info_raises(self):
        with pytest.raises(ValidationError):
            ResumeData()


class TestDocumentConfig:
    def test_valid(self, template_dir, minimal_resume_data, minimal_document_metadata):
        config = DocumentConfig(
            document_metadata=minimal_document_metadata,
            resume_data=minimal_resume_data,
            template_filename=str(template_dir / "template.html.j2"),
        )
        assert Path(config.template_filename).is_file()
        assert (Path(config.template_filename)).exists()

    def test_template_path_resolved_to_absolute(
        self, template_dir, minimal_resume_data, minimal_document_metadata
    ):
        config = DocumentConfig(
            document_metadata=minimal_document_metadata,
            resume_data=minimal_resume_data,
            template_filename=str(template_dir / "template.html.j2"),
        )
        assert Path(config.template_filename).is_absolute()

    def test_relative_template_path_stored_as_path(
        self, minimal_resume_data, minimal_document_metadata
    ):
        config = DocumentConfig(
            document_metadata=minimal_document_metadata,
            resume_data=minimal_resume_data,
            template_filename="template.html.j2",
        )
        assert config.template_filename == Path("template.html.j2")
        assert config.template_filename.name == "template.html.j2"

    def test_nonexistent_template_path_accepted(
        self, tmp_path, minimal_resume_data, minimal_document_metadata
    ):
        # Existence is validated at render time by Jinja2, not at config parse time
        config = DocumentConfig(
            document_metadata=minimal_document_metadata,
            template_filename=str(tmp_path / "missing" / "template.html.j2"),
            resume_data=minimal_resume_data,
        )
        assert config.template_filename.name == "template.html.j2"

    def test_template_path_directory_accepted(
        self, tmp_path, minimal_resume_data, minimal_document_metadata
    ):
        # Existence is validated at render time by Jinja2, not at config parse time
        config = DocumentConfig(
            document_metadata=minimal_document_metadata,
            template_filename=str(tmp_path),
            resume_data=minimal_resume_data,
        )
        assert config.template_filename == tmp_path

    def test_missing_document_metadata_raises(self, template_dir, minimal_resume_data):
        with pytest.raises(ValidationError) as exc_info:
            DocumentConfig(
                template_filename=str(template_dir / "template.html.j2"),
                resume_data=minimal_resume_data,
            )
        assert "document_metadata" in str(exc_info.value)

    def test_missing_resume_raises(self, template_dir, minimal_document_metadata):
        with pytest.raises(ValidationError) as exc_info:
            DocumentConfig(
                document_metadata=minimal_document_metadata,
                template_filename=str(template_dir / "template.html.j2"),
            )
        assert "resume_data" in str(exc_info.value)


class TestLoggingConfig:
    def test_valid_minimal(self):
        c = LoggingConfig()
        assert c.level == "INFO"
        assert c.file is None

    def test_valid_with_file(self, tmp_path):
        log_file = tmp_path / "app.log"
        c = LoggingConfig(file=log_file)
        assert c.file == log_file.resolve()

    def test_nonexistent_log_file_directory_warns(self, tmp_path):
        non_existent_dir = tmp_path / "nonexistent"
        log_file = non_existent_dir / "app.log"
        with pytest.warns(UserWarning, match="Log file directory does not exist"):
            c = LoggingConfig(file=log_file)
        assert c.file is None


class TestOutputConfig:
    def test_valid_minimal(self, tmp_path):
        c = OutputConfig()
        assert c.output_dir == Path("output").resolve()
        assert c.output_filename == "{author}_resume_{date}.pdf"
        assert c.overwrite is False

    def test_valid_custom_output_dir(self, tmp_path):
        custom_dir = tmp_path / "my_output"
        c = OutputConfig(output_dir=custom_dir)
        assert c.output_dir == custom_dir.resolve()

    def test_output_dir_creation(self, tmp_path):
        new_dir = tmp_path / "new_output"
        assert not new_dir.exists()
        OutputConfig(output_dir=new_dir)
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_output_dir_is_file_warns_creates_new_output_dir(self, not_a_dir_path):
        assert not Path("output").exists()
        with pytest.warns(
            UserWarning, match="Output path exists but is not a directory"
        ):
            c = OutputConfig(output_dir=not_a_dir_path)

        assert Path("output").exists()
        assert Path("output").is_dir()
        assert c.output_dir == Path("output").resolve()

    def test_output_dir_is_file_warns_existing_output_dir(self, not_a_dir_path):
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        with pytest.warns(
            UserWarning, match="Output path exists but is not a directory"
        ):
            c = OutputConfig(output_dir=not_a_dir_path)

        assert output_dir.exists()
        assert output_dir.is_dir()
        assert c.output_dir == output_dir.resolve()

    def test_valid_custom_output_filename(self):
        c = OutputConfig(output_filename="resume.pdf")
        assert c.output_filename == "resume.pdf"

    def test_non_pdf_output_filename_raises(self):
        with pytest.raises(ValidationError):
            OutputConfig(output_filename="resume.txt")


class TestAppConfig:
    def test_valid_minimal(self):
        c = AppConfig()
        assert c.logging_config.level == "INFO"
        assert c.logging_config.file is None
        assert c.output_config.output_dir == Path("output").resolve()
        assert c.output_config.output_filename == "{author}_resume_{date}.pdf"
        assert c.output_config.overwrite is False
        assert c.template_dir == Path("templates").resolve()
        assert c.data_file == Path("resume_data.yaml").resolve()

    def test_valid_custom_template_dir(self, tmp_path):
        custom_template_dir = tmp_path / "my_templates"
        custom_template_dir.mkdir()
        c = AppConfig(template_dir=custom_template_dir)
        assert c.template_dir == custom_template_dir.resolve()

    def test_nonexistent_template_dir_warns_and_creates(self, tmp_path):
        non_existent_dir = tmp_path / "nonexistent_templates"
        assert not non_existent_dir.exists()
        with pytest.warns(
            UserWarning, match="Template directory does not exist, creating"
        ):
            c = AppConfig(template_dir=non_existent_dir)
        assert non_existent_dir.exists()
        assert non_existent_dir.is_dir()
        assert c.template_dir == non_existent_dir.resolve()

    def test_template_dir_is_file_warns_and_uses_default_existing(self, not_a_dir_path):
        default_dir = Path("templates")
        default_dir.mkdir(exist_ok=True)

        with pytest.warns(
            UserWarning, match="Template path exists but is not a directory"
        ):
            c = AppConfig(template_dir=not_a_dir_path)
        assert default_dir.exists()
        assert default_dir.is_dir()
        assert c.template_dir == default_dir.resolve()

    def test_template_dir_is_file_warns_and_creates_default(self, not_a_dir_path):
        default_dir = Path("templates")
        assert not default_dir.exists()

        with pytest.warns(
            UserWarning, match="Template path exists but is not a directory"
        ):
            c = AppConfig(template_dir=not_a_dir_path)
        assert default_dir.exists()
        assert default_dir.is_dir()
        assert c.template_dir == default_dir.resolve()

    def test_template_dir_existing_relative_path_resolved(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        relative_path = Path("relative_templates")
        relative_path.mkdir()
        (relative_path / "template.html.j2").write_text("<html></html>")
        c = AppConfig(template_dir=relative_path)
        assert c.template_dir == (package_dir() / relative_path).resolve()

    def test_nonexistent_data_file_warns_and_returns_none(self, tmp_path):
        missing_file = tmp_path / "missing.yaml"
        with pytest.warns(UserWarning, match="Data file does not exist"):
            c = AppConfig(data_file=missing_file)
        assert c.data_file is None

    def test_data_file_not_a_file_warns_and_returns_none(self, tmp_path):
        directory_path = tmp_path / "a_directory"
        directory_path.mkdir()
        with pytest.warns(UserWarning, match="Data file does not exist"):
            c = AppConfig(data_file=directory_path)
        assert c.data_file is None

    def test_valid_absolute_data_file_resolved(self, tmp_path):
        data_file = tmp_path / "resume_data.yaml"
        data_file.write_text("personal_info: {}")
        c = AppConfig(data_file=data_file)
        assert c.data_file == data_file.resolve()

    def test_relative_data_file_resolved_against_package_dir(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        relative_file = Path("my_resume_data.yaml")
        relative_file.write_text("personal_info: {}")
        c = AppConfig(data_file=relative_file)
        assert c.data_file == (package_dir() / relative_file).resolve()


class TestLoadYamlConfig:
    def _write_yaml(self, tmp_path: Path, content: str) -> Path:
        p = tmp_path / "config.yaml"
        p.write_text(textwrap.dedent(content))
        return p

    def test_valid_minimal_document_config_yaml(self, tmp_path, template_dir):
        yaml_file = self._write_yaml(
            tmp_path,
            f"""\
            document_metadata:
              title: My Resume
              author: Jane Doe
            template_path: {template_dir / "template.html.j2"}
            resume_data:
              personal_info:
                name: Jane Doe
                email: jane@example.com
                location: New York, NY
            """,
        )
        config = load_yaml_config(yaml_file, DocumentConfig)
        assert isinstance(config, DocumentConfig)
        assert config.document_metadata.title == "My Resume"
        assert config.resume_data.personal_info.name == "Jane Doe"

    def test_valid_full_document_config_yaml(self, tmp_path, template_dir):
        yaml_file = self._write_yaml(
            tmp_path,
            f"""\
            document_metadata:
              title: Full Resume
              author: Jane Doe
              language: en-US
              keywords:
                - python
                - devops
            template_path: {template_dir / "template.html.j2"}
            resume_data:
              personal_info:
                name: Jane Doe
                email: jane@example.com
                location: New York, NY
                phone: "555-0100"
                linkedin: https://linkedin.com/in/jane
                github: https://github.com/jane
              statement: Experienced engineer.
              skill_sections:
                - title: Languages
                  skills: Python Go
              experience:
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
        config = load_yaml_config(yaml_file, DocumentConfig)
        assert config.document_metadata.keywords == ["python", "devops"]
        assert config.resume_data.personal_info.phone == "555-0100"
        assert len(config.resume_data.experience) == 1
        assert config.resume_data.experience[0].company == "Acme Corp"
        assert len(config.resume_data.projects) == 1
        assert config.resume_data.education[0].gpa == "3.8"
        assert isinstance(config.resume_data.skill_sections[0], SkillsSubsection)

    def test_missing_required_field_raises(self, tmp_path, template_dir):
        yaml_file = self._write_yaml(
            tmp_path,
            f"""\
            document_metadata:
              title: Resume
            template_path: {template_dir / "template.html.j2"}
            resume_data:
              personal_info:
                name: Jane Doe
                email: jane@example.com
                location: NYC
            """,
        )
        with pytest.raises(ValidationError) as exc_info:
            load_yaml_config(yaml_file, DocumentConfig)
        assert "author" in str(exc_info.value)

    def test_nonexistent_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_yaml_config(tmp_path / "nonexistent.yaml", DocumentConfig)

    def test_template_path_in_yaml_loaded_as_path(self, tmp_path):
        yaml_file = self._write_yaml(
            tmp_path,
            """\
            document_metadata:
              title: Resume
              author: Jane
            template_path: /does/not/exist/template.html.j2
            resume_data:
              personal_info:
                name: Jane
                email: jane@example.com
                location: NYC
            """,
        )
        config = load_yaml_config(yaml_file, DocumentConfig)
        assert config.template_filename.name == "template.html.j2"

    def test_load_app_config_yaml(self, tmp_path):
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        data_file = tmp_path / "resume_data.yaml"
        data_file.write_text("personal_info: {}")
        yaml_file = self._write_yaml(
            tmp_path,
            f"""\
            template_dir: {template_dir}
            data_file: {data_file}
            """,
        )
        config = load_yaml_config(yaml_file, AppConfig)
        assert isinstance(config, AppConfig)
        assert config.template_dir == template_dir.resolve()
        assert config.data_file == data_file.resolve()
