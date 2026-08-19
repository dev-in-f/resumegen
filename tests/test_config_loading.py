from unittest.mock import patch

import pytest
from pydantic import ValidationError

from resumegen._core.config import (
    Config,
    DisplayLink,
    DocumentMetadata,
    EducationEntry,
    ExperienceEntry,
    MasterSkillEntry,
    PersonalInfo,
    ProjectEntry,
    ResumeData,
    SkillsSubsection,
)


class TestDocumentMetadata:
    def test_valid_minimal(self):
        m = DocumentMetadata(title="My Resume", author="Jane Doe")
        assert m.title == "My Resume"
        assert m.author == "Jane Doe"
        assert m.language == "en-US"
        assert m.keywords is None

    def test_valid_full(self):
        m = DocumentMetadata(
            title="Resume",
            author="Jane",
            language="fr-FR",
            keywords=["python", "ml"],
        )
        assert m.language == "fr-FR"
        assert m.keywords == ["python", "ml"]

    def test_missing_title_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            DocumentMetadata(author="Jane")
        assert "title" in str(exc_info.value)

    def test_missing_author_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            DocumentMetadata(title="Resume")
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
            description_bullets=["Did X"],
        )
        assert e.end_date is None
        assert e.description_bullets == ["Did X"]

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
        p = ProjectEntry(title="My Project", description_bullets=["Did X"])
        assert p.timeframe is None
        assert p.link is None
        assert p.subtitle is None
        assert p.description_bullets == ["Did X"]
        assert p.technologies is None

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
            personal_info=PersonalInfo(name="Jane", email="j@e.com", location="NYC"),
            document_metadata=DocumentMetadata(title="My Resume", author="Jane Doe"),
        )
        assert r.statement is None
        assert r.skill_sections == []
        assert r.experience == []
        assert r.projects == []
        assert r.education == []

    def test_full_resume(self):
        r = ResumeData(
            document_metadata=DocumentMetadata(title="My Resume", author="Jane Doe"),
            personal_info=PersonalInfo(name="Jane", email="j@e.com", location="NYC"),
            statement="Passionate engineer.",
            experience=[
                {
                    "title": "SWE",
                    "company": "Acme",
                    "location": "NYC",
                    "start_date": "2020-01",
                    "description_bullets": ["Did X"],
                }
            ],
            projects=[{"title": "Cool Project", "description_bullets": ["Did X"]}],
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


class TestConfig:
    def test_template_dir_missing_is_created(self, tmp_path):
        config = Config(template_dir=tmp_path / "templates")
        assert config.template_dir.exists()

    def test_template_dir_is_not_dir_uses_default(self, not_a_dir_path):
        config = Config(template_dir=not_a_dir_path)
        assert config.template_dir != not_a_dir_path
        assert config.template_dir.exists()
        assert config.template_dir.is_dir()

    def test_template_dir_is_not_dir_creates_default_if_missing(
        self, tmp_path, not_a_dir_path, monkeypatch
    ):
        with patch("resumegen._core.config.resources.files") as mock_files:
            mock_files.return_value = tmp_path
            config = Config(template_dir=not_a_dir_path)
            assert config.template_dir.exists()
            assert config.template_dir.is_dir()
        config = Config(template_dir=not_a_dir_path)
        assert config.template_dir.exists()
        assert config.template_dir.is_dir()

    def test_output_dir_missing_is_created(self, tmp_path):
        config = Config(output_dir=tmp_path / "output")
        assert config.output_dir.exists()
        assert config.output_dir.is_dir()

    def test_output_dir_is_not_dir_uses_default(self, not_a_dir_path):
        config = Config(output_dir=not_a_dir_path)
        assert config.output_dir != not_a_dir_path
        assert config.output_dir.exists()
        assert config.output_dir.is_dir()

    def test_output_dir_is_not_dir_creates_default_if_missing(
        self, tmp_path, not_a_dir_path
    ):
        missing_default = tmp_path / "nonexistent_default"
        with patch("resumegen._core.config.RESUMEGEN_DATA_DIR", missing_default):
            config = Config(output_dir=not_a_dir_path)
            assert config.output_dir.exists()
            assert config.output_dir.is_dir()

    def test_output_filename_raises_if_invalid(self):
        with pytest.raises(
            ValueError, match="Output filename must have a \\.pdf extension"
        ):
            Config(output_filename="invalid_filename.xml")

    def test_valid_output_filename(self):
        config = Config(output_filename="{author}_resume_{date}.pdf")
        assert config.output_filename == "{author}_resume_{date}.pdf"


class TestMasterData:
    @pytest.mark.parametrize(
        "proficiency",
        [1, 2, 3, 4, 5],
    )
    def test_valid_skill_proficiency_levels(self, proficiency):
        skill_entry = MasterSkillEntry(name="Python", proficiency=proficiency)
        assert skill_entry.proficiency == proficiency

    @pytest.mark.parametrize(
        "proficiency",
        [-1, 0, 6, 10],
    )
    def test_invalid_skill_proficiency_above_range(self, proficiency):
        with pytest.raises(ValidationError):
            MasterSkillEntry(name="Python", proficiency=proficiency)

    @pytest.mark.parametrize(
        "proficiency",
        [-1, 0, 6, 10],
    )
    def test_invalid_skill_proficiency_below_range(self, proficiency):
        with pytest.raises(ValidationError):
            MasterSkillEntry(name="Python", proficiency=proficiency)
