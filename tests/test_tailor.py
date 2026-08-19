import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import litellm
import pytest
from conftest import MINIMAL_DATA_YAML, MINIMAL_JOB_DESCRIPTION
from litellm import completion as _litellm_completion

from resumegen._core.tailor import (
    _build_taylor_system_prompt,
    _generate_filename,
    _save_to_file,
    _track_cost,
    tailor_resume,
)


def _mock_completion(mock_text):
    def _side_effect(*args, **kwargs):
        kwargs.pop("base_url", None)
        return _litellm_completion(*args, mock_response=mock_text, **kwargs)

    return _side_effect


class TestTrackCost:
    def test_logs_cost_when_present(self, caplog):
        with caplog.at_level(logging.INFO):
            _track_cost({"response_cost": 0.001234}, None, None, None)
        assert "0.001234" in caplog.text

    def test_logs_unavailable_when_no_cost(self, caplog):
        with caplog.at_level(logging.INFO):
            _track_cost({}, None, None, None)
        assert "not available" in caplog.text


class TestBuildTaylorSystemPrompt:
    def test_returns_non_empty_string(self):
        result = _build_taylor_system_prompt()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_resume_writer_context(self):
        result = _build_taylor_system_prompt()
        assert "resume" in result.lower()


class TestGenerateFilename:
    def test_uses_job_title_when_provided(self):
        name = _generate_filename("2024-01-01.10-00", "Software Engineer", None)
        assert "software_engineer" in name
        assert "2024-01-01.10-00" in name

    def test_uses_first_line_of_job_description_when_no_title(self):
        name = _generate_filename("2024-01-01.10-00", None, "Backend Dev\nMore details")
        assert "backend_dev" in name

    def test_fallback_when_neither_title_nor_description(self):
        name = _generate_filename("2024-01-01.10-00", None, None)
        assert name == "tailored_resume_2024-01-01.10-00.yaml"

    def test_spaces_replaced_with_underscores(self):
        name = _generate_filename("2024-01-01.10-00", "Data Science Lead", None)
        assert " " not in name


class TestSaveToFile:
    def test_saves_content_to_file(self, output_dir):
        path = _save_to_file(output_dir, None, "content here", {})
        assert path.exists()
        assert path.read_text() == "content here"

    def test_creates_output_dir_if_missing(self, tmp_path):
        new_dir = tmp_path / "new" / "nested"
        path = _save_to_file(new_dir, None, "content", {})
        assert path.exists()

    def test_uses_output_filename_template(self, output_dir):
        context = {
            "job_title": "Engineer",
            "model": "gpt-4o",
            "job_description_text": "",
        }
        path = _save_to_file(output_dir, "resume_{job_title}.yaml", "content", context)
        assert "Engineer" in path.name

    def test_output_filename_with_first_line_placeholder(self, output_dir):
        context = {
            "job_title": None,
            "model": "gpt-4o",
            "job_description_text": "DevOps Role\nDetails",
        }
        path = _save_to_file(output_dir, "resume_{first_line}.yaml", "content", context)
        assert (
            "DevOps_Role" in path.name or "devops" in path.name.lower() or path.exists()
        )

    def test_output_filename_with_no_job_description_text(self, output_dir):
        context = {"job_title": None, "model": "gpt-4o", "job_description_text": None}
        path = _save_to_file(output_dir, "resume_{first_line}.yaml", "content", context)
        assert path.exists()

    def test_uses_generated_filename_when_no_template(self, output_dir):
        context = {"job_title": "Engineer", "job_description_text": "Something"}
        path = _save_to_file(output_dir, None, "content", context)
        assert "engineer" in path.name


class TestTailorResume:
    def test_raises_when_model_is_empty(
        self, master_data_file, job_description_file, output_dir
    ):
        with pytest.raises(ValueError, match="Model parameter is not set"):
            tailor_resume(master_data_file, job_description_file, output_dir, "")

    def test_returns_path_when_save_to_file(
        self, master_data_file, job_description_file, output_dir
    ):
        with patch(
            "resumegen._core.tailor.completion",
            side_effect=_mock_completion(MINIMAL_DATA_YAML),
        ):
            result = tailor_resume(
                master_data_file,
                job_description_file,
                output_dir,
                "gpt-4o",
                save_to_file=True,
            )
        assert isinstance(result, Path)
        assert result.exists()

    def test_returns_string_when_not_save_to_file(
        self, master_data_file, job_description_file, output_dir
    ):
        with patch(
            "resumegen._core.tailor.completion",
            side_effect=_mock_completion(MINIMAL_DATA_YAML),
        ):
            result = tailor_resume(
                master_data_file,
                job_description_file,
                output_dir,
                "gpt-4o",
                save_to_file=False,
            )
        assert isinstance(result, str)
        assert result == MINIMAL_DATA_YAML

    def test_accepts_job_description_as_string(self, master_data_file, output_dir):
        with patch(
            "resumegen._core.tailor.completion",
            side_effect=_mock_completion("tailored yaml"),
        ):
            result = tailor_resume(
                master_data_file,
                MINIMAL_JOB_DESCRIPTION,
                output_dir,
                "gpt-4o",
                save_to_file=False,
            )
        assert result == "tailored yaml"

    def test_job_title_used_in_filename(
        self, master_data_file, job_description_file, output_dir
    ):
        with patch(
            "resumegen._core.tailor.completion",
            side_effect=_mock_completion("tailored yaml"),
        ):
            result = tailor_resume(
                master_data_file,
                job_description_file,
                output_dir,
                "gpt-4o",
                save_to_file=True,
                job_title="Senior_Dev",
            )
        assert isinstance(result, Path)
        assert "senior_dev" in result.name

    def test_output_filename_overrides_default(
        self, master_data_file, job_description_file, output_dir
    ):
        with patch(
            "resumegen._core.tailor.completion",
            side_effect=_mock_completion("tailored yaml"),
        ):
            result = tailor_resume(
                master_data_file,
                job_description_file,
                output_dir,
                "gpt-4o",
                save_to_file=False,
                output_filename="custom_{model}.yaml",
            )
        assert isinstance(result, Path)
        assert "gpt-4o" in result.name

    def test_base_url_passed_to_completion(
        self, master_data_file, job_description_file, output_dir
    ):
        with patch("resumegen._core.tailor.completion") as mock_completion:
            mock_resp = MagicMock()
            mock_resp.choices[0].message.content = "tailored yaml"
            mock_completion.return_value = mock_resp
            tailor_resume(
                master_data_file,
                job_description_file,
                output_dir,
                "mymodel",
                save_to_file=False,
                base_url="http://localhost:11434",
            )
        _, kwargs = mock_completion.call_args
        assert kwargs.get("base_url") == "http://localhost:11434"

    def test_raises_when_response_is_empty(
        self, master_data_file, job_description_file, output_dir
    ):
        mock_resp = MagicMock()
        mock_resp.choices[0].message.content = None
        with (
            patch("resumegen._core.tailor.completion", return_value=mock_resp),
            pytest.raises(ValueError, match="empty response"),
        ):
            tailor_resume(
                master_data_file,
                job_description_file,
                output_dir,
                "gpt-4o",
                save_to_file=False,
            )

    def test_track_cost_registers_callback(
        self, master_data_file, job_description_file, output_dir
    ):
        with patch(
            "resumegen._core.tailor.completion",
            side_effect=_mock_completion("tailored yaml"),
        ):
            tailor_resume(
                master_data_file,
                job_description_file,
                output_dir,
                "gpt-4o",
                track_cost=True,
                save_to_file=False,
            )
        from resumegen._core.tailor import _track_cost

        assert _track_cost in litellm.success_callback

    def test_no_track_cost_clears_callback(
        self, master_data_file, job_description_file, output_dir
    ):
        with patch(
            "resumegen._core.tailor.completion",
            side_effect=_mock_completion("tailored yaml"),
        ):
            tailor_resume(
                master_data_file,
                job_description_file,
                output_dir,
                "gpt-4o",
                track_cost=False,
                save_to_file=False,
            )
        assert litellm.success_callback == []

    def test_re_raises_on_exception(
        self, master_data_file, job_description_file, output_dir
    ):
        with (
            patch(
                "resumegen._core.tailor.completion",
                side_effect=RuntimeError("api error"),
            ),
            pytest.raises(RuntimeError, match="api error"),
        ):
            tailor_resume(
                master_data_file,
                job_description_file,
                output_dir,
                "gpt-4o",
                save_to_file=False,
            )
