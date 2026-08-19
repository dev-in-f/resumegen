import logging

import pytest
from click.testing import CliRunner

from resumegen._cli.shared import _override_logging_options

runner = CliRunner()


class TestLoggingOverrides:
    @pytest.fixture(autouse=True)
    def reset_resumegen_logger(self):
        logger = logging.getLogger("resumegen")
        original_level = logger.level
        original_handlers = list(logger.handlers)
        yield
        logger.setLevel(original_level)
        for handler in list(logger.handlers):
            if handler not in original_handlers:
                logger.removeHandler(handler)
                handler.close()
        logging.getLogger("resumegen.cli").setLevel(logging.NOTSET)

    def test_logging_level_cli_overrides(self):
        logging.getLogger("resumegen").setLevel(logging.WARNING)
        _override_logging_options("INFO", None)
        assert logging.getLogger("resumegen").getEffectiveLevel() == logging.INFO
        assert logging.getLogger("resumegen.cli").getEffectiveLevel() == logging.INFO
        assert (
            logging.getLogger("resumegen._core.pdf").getEffectiveLevel() == logging.INFO
        )

    def test_logging_file_cli_overrides(self, tmp_path):
        log_file = tmp_path / "test.log"
        _override_logging_options(None, log_file)
        logger = logging.getLogger("resumegen._core.pdf")
        logger.warning("Test message")
        with log_file.open() as f:
            content = f.read()
        assert "Test message" in content

    def test_logging_removes_handler_set_previously(self, tmp_path):
        log_file1 = tmp_path / "test1.log"
        log_file2 = tmp_path / "test2.log"
        _override_logging_options(None, log_file1)
        logger = logging.getLogger("resumegen.cli")
        logger.warning("Message 1")
        _override_logging_options(None, log_file2)
        logger.warning("Message 2")
        with log_file1.open() as f1, log_file2.open() as f2:
            content1 = f1.read()
            content2 = f2.read()
        assert "Message 1" in content1
        assert "Message 2" in content2

    def test_logging_overrides_verbose(self):
        logging.getLogger("resumegen").setLevel(logging.WARNING)
        _override_logging_options(None, None, verbose=True)
        assert logging.getLogger("resumegen").getEffectiveLevel() == logging.DEBUG
        assert logging.getLogger("resumegen.cli").getEffectiveLevel() == logging.DEBUG
