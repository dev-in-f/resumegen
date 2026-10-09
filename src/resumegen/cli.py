import logging

import click

from resumegen._bootstrap import bootstrap
from resumegen._cli import render, render_html, scan_pdf, score, tailor
from resumegen._core.logging import setup_logging

bootstrap()
logger = logging.getLogger(__name__)


setup_logging(logging.getLogger("resumegen"))


app = click.Group(
    commands={
        "render": render,
        "tailor": tailor,
        "scan-pdf": scan_pdf,
        "render-html": render_html,
        "score": score,
    },
    context_settings={"max_content_width": 120},
)
app = click.version_option(package_name="resumegen")(app)

if __name__ == "__main__":  # pragma no cover
    app()
