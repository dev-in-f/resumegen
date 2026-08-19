import pikepdf
import pytest

from resumegen.config import DocumentMetadata, ResumeData


@pytest.fixture
def minimal_resume_data(minimal_document_metadata) -> ResumeData:
    return ResumeData(
        personal_info={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "location": "New York, NY",
        },
        document_metadata=minimal_document_metadata,
        experience=[
            {
                "title": "Engineer",
                "company": "Acme Co.",
                "location": "New York, NY",
                "start_date": "2020-01",
                "description_bullets": ["Did stuff"],
            }
        ],
        skill_sections=[
            {
                "title": "Languages",
                "skills": ["Python"],
            }
        ],
    )


@pytest.fixture
def minimal_document_metadata() -> DocumentMetadata:
    return DocumentMetadata(
        title="Resume",
        author="Jane Doe",
        keywords=["python", "engineer"],
        language="en-US",
    )


@pytest.fixture
def not_a_dir_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    file_path = tmp_path / "not_a_directory"
    file_path.write_text("I am a file, not a directory.")
    return file_path


@pytest.fixture
def blank_pdf():
    pdf = pikepdf.new()
    page = pikepdf.Page(
        pikepdf.Dictionary(
            Type=pikepdf.Name("/Page"),
            MediaBox=[0, 0, 612, 792],
        )
    )
    pdf.pages.append(page)
    return pdf


@pytest.fixture
def accessible_pdf(blank_pdf):
    with blank_pdf.open_metadata() as meta:
        meta["dc:title"] = "Test PDF"
        meta["dc:language"] = "en-US"
        meta["pdfuaid:part"] = "1"
    blank_pdf.Root["/MarkInfo"] = pikepdf.Dictionary(Marked=True)
    blank_pdf.Root["/Lang"] = "en-US"
    blank_pdf.Root["/StructTreeRoot"] = pikepdf.Dictionary(TextOne="Test")

    return blank_pdf
