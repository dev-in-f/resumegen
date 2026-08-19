import logging

from resumegen.logging import setup_logging


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
        with open(log_file) as f:
            content = f.read()
        assert "Test log message" in content
