import pytest


@pytest.fixture
def minimal_resume_data():
    return {
        "personal_info": {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "location": "New York, NY",
        }
    }


@pytest.fixture
def template_dir(tmp_path):
    d = tmp_path / "template"
    d.mkdir()
    (d / "template.html.j2").write_text("<html></html>")
    return d


@pytest.fixture
def minimal_document_metadata():
    return {"title": "Resume", "author": "Jane"}


@pytest.fixture
def not_a_dir_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    file_path = tmp_path / "not_a_directory"
    file_path.write_text("I am a file, not a directory.")
    return file_path
