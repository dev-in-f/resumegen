import logging

import click

from resumegen._bootstrap import bootstrap
from resumegen._cli import render, scan_pdf, tailor
from resumegen._core.logging import setup_logging

bootstrap()
logger = logging.getLogger(__name__)


setup_logging(logging.getLogger("resumegen"))


app = click.Group(commands={"render": render, "tailor": tailor, "scan-pdf": scan_pdf})

if __name__ == "__main__":  # pragma no cover
    app()
