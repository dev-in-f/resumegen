import io
import logging
import sys
import time
from pathlib import Path

from resumegen._core.logging import Spinner, setup_logging


class FakeStdout(io.StringIO):
    def __init__(self, isatty: bool):
        super().__init__()
        self._isatty = isatty

    def isatty(self):
        return self._isatty


class TestLogging:
    def test_setup_logging_no_env_vars(self):
        logger = logging.getLogger("test_logger")
        setup_logging(logger)
        assert logger.level == 20
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_setup_logging_log_level_env_var(self, monkeypatch):
        monkeypatch.setenv("RESUMEGEN_LOG_LEVEL", "DEBUG")
        logger = logging.getLogger("test_logger")
        setup_logging(logger)
        assert logger.level == logging.DEBUG

    def test_setup_logging_log_file_env_var(self, tmp_path, monkeypatch):
        log_file = tmp_path / "test.log"
        monkeypatch.setenv("RESUMEGEN_LOG_FILE", str(log_file))
        logger = logging.getLogger("test_logger")
        setup_logging(logger)
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        logger.info("Test log message")
        with Path.open(log_file) as f:
            content = f.read()
        assert "Test log message" in content

    def test_setup_logging_verbose_env_var(self, monkeypatch):
        monkeypatch.setenv("RESUMEGEN_VERBOSE", "1")
        logger = logging.getLogger("test_logger")
        setup_logging(logger)
        assert logger.level == logging.DEBUG
        for log in ["weasyprint", "pikepdf", "litellm", "fontTools"]:
            assert logging.getLogger(log).level == logging.DEBUG


class TestSpinner:
    def test_spinner_noop_when_disabled(self, monkeypatch):
        monkeypatch.setattr(sys, "stdout", FakeStdout(isatty=True))
        spinner = Spinner(message="Processing...", enabled=False)
        assert spinner.enabled is False
        with spinner:
            pass
        assert spinner._thread is None

    def test_spinner_noop_when_not_a_terminal(self, monkeypatch):
        monkeypatch.setattr(sys, "stdout", FakeStdout(isatty=False))
        spinner = Spinner(message="Processing...", enabled=True)
        assert spinner.enabled is False
        with spinner:
            pass
        assert spinner._thread is None

    def test_spinner_runs_when_enabled_and_terminal(self, monkeypatch):
        fake_stdout = FakeStdout(isatty=True)
        monkeypatch.setattr(sys, "stdout", fake_stdout)
        spinner = Spinner(message="Processing...", enabled=True)
        assert spinner.enabled is True
        with spinner:
            time.sleep(spinner.interval * 3)
        assert "Processing..." in fake_stdout.getvalue()
