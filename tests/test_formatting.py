import pytest

from resumegen.core.config import DocumentMetadata
from resumegen.core.formatting import _format_output_filename, _sanitize_metadata


class TestSanitizeMetadata:
    def test_strings_lowercased_and_spaces_replaced(self):
        meta = DocumentMetadata(
            title="My Cool Resume", author="Jane Doe", language="en-US"
        )
        result = _sanitize_metadata(meta)
        assert result["title"] == "my_cool_resume"
        assert result["author"] == "jane_doe"
        assert result["language"] == "en-us"

    def test_keywords_sanitized_and_joined_with_underscore(self):
        meta = DocumentMetadata(title="T", author="A", keywords=["Python", "ML"])
        result = _sanitize_metadata(meta)
        assert result["keywords"] == "python_ml"

    def test_single_keyword(self):
        meta = DocumentMetadata(title="T", author="A", keywords=["python"])
        result = _sanitize_metadata(meta)
        assert result["keywords"] == "python"

    def test_empty_keywords_produces_empty_string(self):
        meta = DocumentMetadata(title="T", author="A", keywords=[])
        result = _sanitize_metadata(meta)
        assert result["keywords"] == ""

    def test_none_description_preserved(self):
        meta = DocumentMetadata(title="T", author="A")
        result = _sanitize_metadata(meta)
        assert result["description"] is None

    def test_description_sanitized_when_set(self):
        meta = DocumentMetadata(title="T", author="A", description="Senior Engineer")
        result = _sanitize_metadata(meta)
        assert result["description"] == "senior_engineer"


class TestFormatOutputFilename:
    def test_formats_filename_with_metadata(self):
        meta = DocumentMetadata(
            title="My Cool Resume",
            author="Jane Doe",
            language="en-US",
            keywords=["Python", "ML"],
        )
        filename_template = "{title}_{author}_{language}_{keywords}.pdf"
        result = _format_output_filename(filename_template, meta)
        assert result == "my_cool_resume_jane_doe_en-us_python_ml.pdf"

    def test_formats_filename_with_missing_metadata(self):
        meta = DocumentMetadata(title="T", author="")
        filename_template = "{title}_{author}_{language}.pdf"
        result = _format_output_filename(filename_template, meta)
        assert result == "t__en-us.pdf"

    def test_formats_filename_with_unsupported_template_fields(self):
        meta = DocumentMetadata(title="T", author="A")
        filename_template = "{title}_{author}_{unsupported_field}.pdf"
        with pytest.raises(KeyError, match="unsupported_field"):
            _format_output_filename(filename_template, meta)
