import json

import pikepdf
import pytest

from resumegen.accessibility import (
    AccessibilityReport,
    Severity,
    _walk_struct_tree,
    scan_accessibility,
)


@pytest.fixture
def example_issues():
    return [
        {
            "severity": "warning",
            "rule": "TestRule1",
            "message": "This is a warning.",
        },
        {
            "severity": "error",
            "rule": "TestRule2",
            "message": "This is an error.",
        },
    ]


class TestAccessibilityReport:
    def test_accessibility_report_no_errors(self):
        report = AccessibilityReport(issues=[])
        assert not report.has_errors

    def test_accessibility_report_with_warning(self):
        report = AccessibilityReport(
            issues=[
                {
                    "severity": "warning",
                    "rule": "TestRule",
                    "message": "This is a warning.",
                }
            ]
        )
        assert not report.has_errors

    def test_accessibility_report_with_error(self):
        report = AccessibilityReport(
            issues=[
                {
                    "severity": "error",
                    "rule": "TestRule",
                    "message": "This is an error.",
                }
            ]
        )
        assert report.has_errors

    def test_accessibility_report_to_json(self, example_issues):
        report = AccessibilityReport(issues=example_issues)
        json_output = report.to_json()
        data = json.loads(json_output)

        assert len(data["issues"]) == 2
        assert data["issues"][0]["severity"] == "warning"
        assert data["issues"][0]["rule"] == "TestRule1"
        assert data["issues"][0]["message"] == "This is a warning."
        assert data["issues"][1]["severity"] == "error"
        assert data["issues"][1]["rule"] == "TestRule2"
        assert data["issues"][1]["message"] == "This is an error."

    def test_get_report(self, example_issues):
        report = AccessibilityReport(issues=example_issues)
        report_str = report.get_report()
        assert "WARNING: TestRule1 - This is a warning." in report_str
        assert "ERROR: TestRule2 - This is an error." in report_str

    def test_get_report_no_issues(self):
        report = AccessibilityReport(issues=[])
        report_str = report.get_report()
        assert "No accessibility issues found." in report_str


class TestScanAccessibility:
    def test_scan_accessibility_no_issues(self, accessible_pdf):
        report = scan_accessibility(accessible_pdf)
        assert not report.issues

    def test_scan_accessibility_missing_title(self, accessible_pdf):
        with accessible_pdf.open_metadata() as meta:
            del meta["dc:title"]
        report = scan_accessibility(accessible_pdf)
        assert len(report.issues) == 1
        assert report.issues[0].severity == Severity.ERROR
        assert report.issues[0].rule == "MissingTitle"
        assert (
            report.issues[0].message
            == "The PDF is missing a title in the metadata (dc:title)."
        )

    def test_scan_accessibility_missing_xmp_language(self, accessible_pdf):
        with accessible_pdf.open_metadata() as meta:
            del meta["dc:language"]
        report = scan_accessibility(accessible_pdf)
        assert len(report.issues) == 1
        assert report.issues[0].severity == Severity.WARNING
        assert report.issues[0].rule == "MissingLanguage"
        assert (
            report.issues[0].message == "The PDF is missing a language declaration in "
            "the metadata (dc:language)."
        )

    def test_scan_accessibility_missing_root_language(self, accessible_pdf):
        del accessible_pdf.Root["/Lang"]
        report = scan_accessibility(accessible_pdf)
        assert len(report.issues) == 1
        assert report.issues[0].severity == Severity.WARNING
        assert report.issues[0].rule == "MissingRootLanguage"
        assert (
            report.issues[0].message
            == "The PDF root does not have a language declaration (/Lang)."
        )

    def test_scan_accessibility_no_pdfuaid(self, accessible_pdf):
        with accessible_pdf.open_metadata() as meta:
            del meta["pdfuaid:part"]
        report = scan_accessibility(accessible_pdf)
        assert len(report.issues) == 1
        assert report.issues[0].severity == Severity.WARNING
        assert report.issues[0].rule == "MissingPDFUAID"
        assert (
            report.issues[0].message == "The PDF is missing the PDF/UA identifier"
            " in the metadata (pdfuaid:part)."
        )

    def test_scan_accessibility_unmarked_pdf(self, accessible_pdf):
        del accessible_pdf.Root["/MarkInfo"]
        report = scan_accessibility(accessible_pdf)
        assert len(report.issues) == 1
        assert report.issues[0].severity == Severity.WARNING
        assert report.issues[0].rule == "UnmarkedPDF"
        assert (
            report.issues[0].message
            == "The PDF does not have MarkInfo indicating it is tagged."
        )

    def test_scan_accessibility_missing_struct_tree(self, accessible_pdf):
        del accessible_pdf.Root["/StructTreeRoot"]
        report = scan_accessibility(accessible_pdf)
        assert len(report.issues) == 1
        assert report.issues[0].severity == Severity.WARNING
        assert report.issues[0].rule == "MissingStructTree"
        assert (
            report.issues[0].message
            == "The PDF does not have a structural tree (/StructTreeRoot)."
        )


class TestWalkStructTree:
    def test_figure_missing_alt_text(self):
        node = pikepdf.Dictionary(S=pikepdf.Name("/Figure"))
        report = AccessibilityReport()
        _walk_struct_tree(node, report)
        assert len(report.issues) == 1
        assert report.issues[0].severity == Severity.WARNING
        assert report.issues[0].rule == "MissingAltText"

    def test_figure_with_alt_text(self):
        node = pikepdf.Dictionary(S=pikepdf.Name("/Figure"), Alt="A description")
        report = AccessibilityReport()
        _walk_struct_tree(node, report)
        assert not report.issues

    def test_table_header_missing_scope(self):
        node = pikepdf.Dictionary(S=pikepdf.Name("/TH"))
        report = AccessibilityReport()
        _walk_struct_tree(node, report)
        assert len(report.issues) == 1
        assert report.issues[0].severity == Severity.WARNING
        assert report.issues[0].rule == "MissingTableHeaderScope"

    def test_table_header_with_scope(self):
        node = pikepdf.Dictionary(S=pikepdf.Name("/TH"), A=pikepdf.Name("/Row"))
        report = AccessibilityReport()
        _walk_struct_tree(node, report)
        assert not report.issues

    def test_node_without_children_does_not_recurse(self):
        node = pikepdf.Dictionary(S=pikepdf.Name("/P"))
        report = AccessibilityReport()
        _walk_struct_tree(node, report)
        assert not report.issues

    def test_recurses_into_array_children(self):
        child = pikepdf.Dictionary(S=pikepdf.Name("/Figure"))
        node = pikepdf.Dictionary(
            S=pikepdf.Name("/Document"),
            K=pikepdf.Array([child]),
        )
        report = AccessibilityReport()
        _walk_struct_tree(node, report)
        assert len(report.issues) == 1
        assert report.issues[0].rule == "MissingAltText"

    def test_recurses_into_single_dict_child(self):
        child = pikepdf.Dictionary(S=pikepdf.Name("/TH"))
        node = pikepdf.Dictionary(S=pikepdf.Name("/Document"), K=child)
        report = AccessibilityReport()
        _walk_struct_tree(node, report)
        assert len(report.issues) == 1
        assert report.issues[0].rule == "MissingTableHeaderScope"

    def test_skips_non_dict_array_children(self):
        node = pikepdf.Dictionary(
            S=pikepdf.Name("/Figure"),
            K=pikepdf.Array([0, 1, 2]),
        )
        report = AccessibilityReport()
        _walk_struct_tree(node, report)
        assert len(report.issues) == 1
        assert report.issues[0].rule == "MissingAltText"

    def test_non_array_non_dict_child_does_not_recurse(self):
        node = pikepdf.Dictionary(S=pikepdf.Name("/Figure"), K=0)
        report = AccessibilityReport()
        _walk_struct_tree(node, report)
        assert len(report.issues) == 1
        assert report.issues[0].rule == "MissingAltText"
