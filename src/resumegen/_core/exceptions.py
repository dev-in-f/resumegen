class PdfError(Exception):
    pass


class MetadataInjectionError(PdfError):
    def __init__(self, original_exception: Exception | None = None):
        super().__init__("Error injecting metadata into PDF.")
        self.original_exception = original_exception


class RenderError(Exception):
    pass
