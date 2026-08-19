from enum import Enum

import pikepdf
from pydantic import BaseModel, computed_field

from resumegen.exceptions import PdfError


class Severity(Enum):
    WARNING = "warning"
    ERROR = "error"


class AccessibilityIssue(BaseModel):
    severity: Severity
    rule: str
    message: str


class AccessibilityReport(BaseModel):
    issues: list[AccessibilityIssue] = []

    @computed_field
    @property
    def has_errors(self) -> bool:
        return any(i.severity == Severity.ERROR for i in self.issues)

    def get_report(self) -> str:
        if not self.issues:
            return (
                "No accessibility issues found. "
                "The PDF is compliant with basic accessibility standards."
            )
        report_lines = []
        for issue in self.issues:
            report_lines.append(
                f"{issue.severity.value.upper()}: {issue.rule} - {issue.message}"
            )
        return "\n".join(report_lines)

    def to_json(self) -> str:
        return self.model_dump_json()


def scan_accessibility(pdf: pikepdf.Pdf) -> AccessibilityReport:
    report = AccessibilityReport()
    try:
        _check_metadata(pdf, report)
        _check_mark_info(pdf, report)
        _check_language(pdf, report)
        _check_struct_tree(pdf, report)
    except Exception as e:
        raise PdfError(f"Error scanning PDF for accessibility: {e}") from e
    return report


def _check_metadata(pdf: pikepdf.Pdf, report: AccessibilityReport) -> None:
    with pdf.open_metadata() as meta:
        if not meta.get("dc:title"):
            report.issues.append(
                AccessibilityIssue(
                    severity=Severity.ERROR,
                    rule="MissingTitle",
                    message="The PDF is missing a title in the metadata (dc:title).",
                )
            )
        if not meta.get("pdfuaid:part"):
            report.issues.append(
                AccessibilityIssue(
                    severity=Severity.WARNING,
                    rule="MissingPDFUAID",
                    message="The PDF is missing the PDF/UA identifier "
                    "in the metadata (pdfuaid:part).",
                )
            )


def _check_mark_info(pdf: pikepdf.Pdf, report: AccessibilityReport) -> None:
    mark_info = pdf.Root.get("/MarkInfo")
    if not mark_info or not mark_info.get("/Marked"):
        report.issues.append(
            AccessibilityIssue(
                severity=Severity.WARNING,
                rule="UnmarkedPDF",
                message="The PDF does not have MarkInfo indicating it is tagged.",
            )
        )


def _check_language(pdf: pikepdf.Pdf, report: AccessibilityReport) -> None:
    if not pdf.Root.get("/Lang"):
        report.issues.append(
            AccessibilityIssue(
                severity=Severity.WARNING,
                rule="MissingRootLanguage",
                message="The PDF root does not have a language declaration (/Lang).",
            )
        )
    with pdf.open_metadata() as meta:
        if not meta.get("dc:language"):
            report.issues.append(
                AccessibilityIssue(
                    severity=Severity.WARNING,
                    rule="MissingLanguage",
                    message="The PDF is missing a language "
                    "declaration in the metadata (dc:language).",
                )
            )


def _check_struct_tree(pdf: pikepdf.Pdf, report: AccessibilityReport) -> None:
    struct_tree = pdf.Root.get("/StructTreeRoot")
    if not struct_tree:
        report.issues.append(
            AccessibilityIssue(
                severity=Severity.WARNING,
                rule="MissingStructTree",
                message="The PDF does not have a structural tree (/StructTreeRoot).",
            )
        )
        return
    _walk_struct_tree(struct_tree, report)


def _walk_struct_tree(node: pikepdf.Object, report: AccessibilityReport) -> None:
    tag_type = str(node.get("/S", "")).lstrip("/")

    if tag_type == "Figure":
        alt = node.get("/Alt")
        if not alt:
            report.issues.append(
                AccessibilityIssue(
                    severity=Severity.WARNING,
                    rule="MissingAltText",
                    message="A Figure element is missing alternative text (/Alt).",
                )
            )

    if tag_type == "TH" and not node.get("/A"):
        report.issues.append(
            AccessibilityIssue(
                severity=Severity.WARNING,
                rule="MissingTableHeaderScope",
                message="A table header (TH) is missing a scope (/A).",
            )
        )

    children = node.get("/K")
    if children is None:
        return
    if isinstance(children, pikepdf.Array):
        for child in children:
            if isinstance(child, pikepdf.Dictionary):
                _walk_struct_tree(child, report)
    elif isinstance(children, pikepdf.Dictionary):
        _walk_struct_tree(children, report)
