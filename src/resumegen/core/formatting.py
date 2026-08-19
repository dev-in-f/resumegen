import logging
from datetime import datetime

from resumegen.core.config import DocumentMetadata

logger = logging.getLogger(__name__)


def _sanitize_metadata(metadata: DocumentMetadata) -> dict[str, str]:
    """Normalizes DocumentMetadata values for filename rendering."""
    metadata_dict = metadata.model_dump()
    for key, value in metadata_dict.items():
        if isinstance(value, str):
            sanitized = value.lower().replace(" ", "_")
            metadata_dict[key] = sanitized
        if isinstance(value, list):
            metadata_dict[key] = [str(v).lower().replace(" ", "_") for v in value]
            metadata_dict[key] = "_".join(metadata_dict[key])
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
        Rendered output filename as a string.
    """
    output_filename = filename_template
    clean_metadata = _sanitize_metadata(metadata)
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logger.debug("Rendering output filename with template: %s", output_filename)
    return output_filename.format(**clean_metadata, date=date_str)
