from io import BytesIO, StringIO

from django.core.management import call_command
from django.test import SimpleTestCase

from .evaluation import evaluate_cases
from .syllabus import analyze_pages, analyze_syllabus, date_details
from .test_helpers import syllabus_pdf


class StructuredSyllabusTests(SimpleTestCase):
    def test_labeled_variations(self):
        report = evaluate_cases()
        for result in report["results"]:
            with self.subTest(case=result["case"]):
                self.assertTrue(result["passed"], result["errors"])

    def test_evaluation_command(self):
        output = StringIO()
        call_command("evaluate_syllabus_parser", stdout=output)
        self.assertIn("not an estimate of accuracy", output.getvalue())

    def test_date_order_is_explicit(self):
        self.assertEqual(date_details("5/10/2026", 2026, "MDY")["due_date"], "2026-05-10")
        self.assertEqual(date_details("5/10/2026", 2026, "DMY")["due_date"], "2026-10-05")
        with self.assertRaises(ValueError):
            analyze_pages(["Quiz 1"], 2026, "unknown")

    def test_date_ranges_do_not_become_invented_deadlines(self):
        for text in ("Sep 1-15", "September 1, 2026 to September 15, 2026"):
            self.assertEqual(date_details(text, 2026)["due_date"], "")

    def test_source_evidence_and_times_are_preserved(self):
        report = analyze_syllabus(BytesIO(syllabus_pdf("Finals  Fri, Dec 11, 8:30     Final Exam - On paper\n        - 10:30 AM", fixed_width=True)), 2026)
        item = report["items"][0]
        self.assertEqual(item["source_page"], 1)
        self.assertIn("10:30 AM", item["source_text"])
        self.assertTrue(item["time_text"])
        self.assertEqual(item["due_date"], "2026-12-11")

    def test_policy_and_grading_pdf_does_not_create_tasks(self):
        report = analyze_syllabus(BytesIO(syllabus_pdf("Grading\nHomework 20%\nFinal Exam 80%\nPolicies\nAssignments must be handwritten.")), 2026)
        self.assertEqual(report["items"], [])
        self.assertEqual(len(report["grading"]), 2)
        self.assertEqual(len(report["policies"]), 1)

    def test_metadata_has_provenance(self):
        report = analyze_pages(["Instructor: Example Professor\nEmail: professor@example.edu\nLecture: Mon/Wed 8:00 AM - 8:50 AM"], 2026)
        self.assertEqual(len(report["course_information"]), 2)
        self.assertEqual(len(report["meetings"]), 1)
        self.assertTrue(all(row["source_page"] == 1 for row in report["course_information"]))

    def test_time_range_is_not_a_second_date(self):
        item = analyze_pages(["Final exam: May 20, 2025, 3:15-5:15 PM"], 2025)["items"][0]
        self.assertEqual(item["due_date"], "2025-05-20")

    def test_week_ranges_never_become_calendar_dates(self):
        for wording in ("Week 3-4", "Weeks 11-12", "Approximately Week 5-6"):
            self.assertEqual(date_details(wording, 2026)["due_date"], "")
            self.assertEqual(date_details(wording, 2026)["date_status"], "relative")

    def test_no_written_final_does_not_create_an_exam(self):
        report = analyze_pages(["Assignments\nThere will be no written final exam. Instead, teams will give presentations."], 2026)
        self.assertFalse(any(item["item_type"] == "exam" for item in report["items"]))
        self.assertEqual(report["assessment_overview"][0]["count"], 0)

    def test_negative_and_positive_exam_statements_flag_conflict(self):
        report = analyze_pages(["Final exam December 11, 2026\nThere will be no written final exam."], 2026)
        self.assertFalse(report["items"][0]["include"])
        self.assertTrue(any("no final exam" in warning for warning in report["items"][0]["warnings"]))

    def test_weight_first_rows_keep_relative_assessments(self):
        report = analyze_pages(["Grading Information\n15%     Midterm Exam 1\n        Approximately Week 6\n\n20%     Final Exam\n        December 11, 2026"], 2026)
        self.assertEqual(len(report["grading"]), 2)
        self.assertEqual(report["items"][0]["due_date"], "")
        self.assertEqual(report["items"][1]["due_date"], "2026-12-11")

    def test_narrative_week_schedule_keeps_nested_assessments(self):
        report = analyze_pages(["Course Schedule\nWeek 3-4: Customer discovery.\n    o Assessment: Write a customer interview report.\nWeek 5: Prototyping.\n    o Assessment: Submit a design memo."], 2026)
        self.assertEqual(len(report["items"]), 4)
        self.assertTrue(all(not item["due_date"] for item in report["items"]))
        self.assertEqual(sum(item["item_type"] == "class_session" for item in report["items"]), 2)

    def test_policy_identifier_is_not_a_calendar_date(self):
        report = analyze_pages(["University Policies\nDirective 97-03 requires registration with the disability office."], 2026)
        self.assertEqual(report["items"], [])

    def test_lecture_number_ranges_and_shifted_columns(self):
        report = analyze_pages(["Course Schedule\n    Lecture           Topic\n    1 - 4          Hardware parallelism\n    5 - 6          Software parallelism"], 2026)
        self.assertEqual([item["title"] for item in report["items"]], ["Hardware parallelism", "Software parallelism"])
        self.assertTrue(all(not item["due_date"] for item in report["items"]))

    def test_readings_are_retained_without_becoming_tasks(self):
        report = analyze_pages(["Date       Topics          Readings\n9/15/2026  Memory systems  Chapter 2"], 2026)
        self.assertEqual(len(report["items"]), 1)
        self.assertEqual(report["items"][0]["reading_text"], "Chapter 2")

    def test_wrapped_holiday_date_does_not_split_the_lecture_row(self):
        report = analyze_pages(["Course Schedule\nWeek    Date                   Topics\n4       Wed, Sep 9             Instruction Set\n        (Mon, Sep 7 -          Architecture (3)\n        Labor Day,\n        campus closed,\n        no lecture)"], 2026)
        self.assertEqual(len(report["items"]), 2)
        lecture = next(item for item in report["items"] if item["item_type"] == "class_session")
        closure = next(item for item in report["items"] if item["item_type"] == "event")
        self.assertEqual(lecture["title"], "Instruction Set Architecture (3)")
        self.assertEqual(lecture["due_date"], "2026-09-09")
        self.assertEqual(closure["due_date"], "2026-09-07")

    def test_grading_totals_rounding_examples_and_notes_are_not_components(self):
        report = analyze_pages(["Grading\nTeam activities and classroom participation\n(asking questions and providing feedback) - 15%\nFinal project 85%\nTotal: 100%\nNote - up to 5% extra credit may be issued.\nEx: 89.5 = 90%"], 2026)
        self.assertEqual(len(report["grading"]), 2)
        self.assertIn("Team activities", report["grading"][0]["label"])
