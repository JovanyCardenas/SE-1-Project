"""Reproducible labeled examples; fixture scores are not real-world accuracy."""
import json
from pathlib import Path

from .syllabus import analyze_pages

DEFAULT_CASES = Path(__file__).parent / "fixtures" / "syllabus_cases.json"


def evaluate_cases(path=DEFAULT_CASES):
    cases = json.loads(Path(path).read_text(encoding="utf-8"))
    results = []
    for case in cases:
        report = analyze_pages(case["pages"], case.get("year", 2026), case.get("date_order", "MDY"))
        actual = [[item["title"], item["due_date"], item["item_type"]] for item in report["items"]]
        errors = []
        if actual != case["items"]:
            errors.append({"field": "items", "expected": case["items"], "actual": actual})
        for group, expected in case.get("groups", {}).items():
            if len(report[group]) != expected:
                errors.append({"field": group, "expected": expected, "actual": len(report[group])})
        if "statuses" in case:
            statuses = [item["date_status"] for item in report["items"]]
            if statuses != case["statuses"]:
                errors.append({"field": "date_status", "expected": case["statuses"], "actual": statuses})
        if "blank_pages" in case and report["pages_without_text"] != case["blank_pages"]:
            errors.append({"field": "pages_without_text", "actual": report["pages_without_text"]})
        results.append({"case": case["name"], "passed": not errors, "errors": errors})
    return {"scope": "Synthetic labeled regression fixtures; not an estimate of accuracy on unseen syllabi.",
            "total": len(results), "passed": sum(result["passed"] for result in results), "results": results}
