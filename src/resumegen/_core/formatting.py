import logging
import re
from datetime import datetime

from resumegen._core.config import DocumentMetadata

logger = logging.getLogger(__name__)


MAX_FILENAME_LENGTH = 200
MAX_FIELD_LENGTH = 50

_INVALID_FILENAME_CHARS = re.compile(r"[^a-z0-9_-]+")
_REPEATED_UNDERSCORES = re.compile(r"_+")


def _sanitize_filename_component(value: str) -> str:
    """Lowercases, strips invalid filesystem characters, and truncates a value."""
    sanitized = value.lower().replace(" ", "_")
    sanitized = _INVALID_FILENAME_CHARS.sub("", sanitized)
    sanitized = _REPEATED_UNDERSCORES.sub("_", sanitized).strip("_-")
    return sanitized[:MAX_FIELD_LENGTH]


def _sanitize_metadata(metadata: DocumentMetadata) -> dict[str, str]:
    """Normalizes DocumentMetadata values for filename rendering."""
    metadata_dict = metadata.model_dump()
    for key, value in metadata_dict.items():
        if isinstance(value, str):
            metadata_dict[key] = _sanitize_filename_component(value)
        if isinstance(value, list):
            metadata_dict[key] = "_".join(
                _sanitize_filename_component(str(v)) for v in value
            )
    logger.debug("Sanitized metadata: %s", metadata_dict)
    return metadata_dict


def _format_output_filename(filename_template: str, metadata: DocumentMetadata) -> str:
    """
    Renders the output filename based on the template and document metadata.
    Supports placeholders matching DocumentMeta attributes.

    Arguments:
        filename_template: A string template for the filename.
        metadata: DocumentMetadata object containing the metadata
                  for rendering the filename.

    Returns:
        Rendered output filename as a string, sanitized to valid filename
        characters and truncated to a safe length.
    """
    output_filename = filename_template
    clean_metadata = _sanitize_metadata(metadata)
    date_str = datetime.now(tz=datetime.now().astimezone().tzinfo).strftime(
        "%Y-%m-%d_%H-%M-%S"
    )
    logger.debug("Rendering output filename with template: %s", output_filename)
    rendered = output_filename.format(**clean_metadata, date=date_str)
    return rendered[:MAX_FILENAME_LENGTH]
