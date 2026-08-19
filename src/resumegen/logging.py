import logging
import os

import dotenv

dotenv.load_dotenv()


class ColorLogFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_template = (
        "%(asctime)s [%(name)s] - %(levelname)s - %(message)s - %(filename)s:%(lineno)d"
    )
    FORMATS = {
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
    logger.setLevel(os.getenv("RESUMEGEN_LOG_LEVEL", logging.INFO))
    log_file = os.getenv("RESUMEGEN_LOG_FILE")
    if log_file:
        logger.addHandler(logging.FileHandler(log_file))

    ch = logging.StreamHandler()
    ch.setLevel(os.getenv("RESUMEGEN_LOG_LEVEL", logging.INFO))
    ch.setFormatter(ColorLogFormatter())
    logger.addHandler(ch)
