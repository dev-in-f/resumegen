import itertools
import logging
import os
import sys
import threading
import time
from typing import ClassVar

import dotenv

dotenv.load_dotenv()

LIBRARY_LOGGERS = [
    "weasyprint",
    "pikepdf",
    "litellm",
    "fontTools",
]


class DynamicStderrHandler(logging.StreamHandler):
    def emit(self, record):
        self.stream = sys.stderr
        super().emit(record)


class ColorLogFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_template = "%(asctime)s [%(name)s] - %(levelname)s - %(message)s"
    FORMATS: ClassVar[dict[int, str]] = {
        logging.DEBUG: grey + format_template + reset,
        logging.INFO: grey + format_template + reset,
        logging.WARNING: yellow + format_template + reset,
        logging.ERROR: red + format_template + reset,
        logging.CRITICAL: bold_red + format_template + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logging(logger: logging.Logger):
    if os.getenv("RESUMEGEN_VERBOSE") == "1":
        logger.setLevel(logging.DEBUG)
        for log in LIBRARY_LOGGERS:
            logging.getLogger(log).setLevel(logging.DEBUG)
    else:
        for log in LIBRARY_LOGGERS:
            logging.getLogger(log).setLevel(
                os.getenv("RESUMEGEN_LOG_LEVEL", logging.INFO)
            )
        logger.setLevel(os.getenv("RESUMEGEN_LOG_LEVEL", logging.INFO))
    log_file = os.getenv("RESUMEGEN_LOG_FILE")
    if log_file:
        logger.addHandler(logging.FileHandler(log_file))

    ch = DynamicStderrHandler()
    ch.setLevel(os.getenv("RESUMEGEN_LOG_LEVEL", logging.INFO))
    ch.setFormatter(ColorLogFormatter())
    logger.addHandler(ch)


class Spinner:
    """Displays a spinning indicator with a message while a block runs.

    No-ops when `enabled` is False or stdout isn't a terminal.
    """

    frames = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")
    interval = 0.08

    def __init__(self, message: str, enabled: bool = True):
        self.message = message
        self.enabled = enabled and sys.stdout.isatty()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def _spin(self):
        for frame in itertools.cycle(self.frames):  # pragma: no branch
            if self._stop_event.is_set():
                break
            sys.stdout.write(f"\r{color_message(frame, 'cyan')}  {self.message}")
            sys.stdout.flush()
            time.sleep(self.interval)

    def __enter__(self):
        if self.enabled:
            self._thread = threading.Thread(target=self._spin, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.enabled and self._thread:
            self._stop_event.set()
            self._thread.join()
            sys.stdout.write("\r" + " " * (len(self.message) + 4) + "\r")
            sys.stdout.flush()
        return False


def color_message(message: str, color: str) -> str:
    color_codes = {
        "grey": "\x1b[38;20m",
        "yellow": "\x1b[33;20m",
        "red": "\x1b[31;20m",
        "green": "\x1b[32;20m",
        "blue": "\x1b[34;20m",
        "cyan": "\x1b[36;20m",
        "magenta": "\x1b[35;20m",
        "white": "\x1b[37;20m",
    }
    reset_code = "\x1b[0m"
    return f"{color_codes.get(color, '')}{message}{reset_code}"
