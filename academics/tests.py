from datetime import date
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from .forms import UploadForm
from .models import Course, CourseAssignment, CourseEnrollment, SyllabusImport
from .parser import MAX_BYTES, SyllabusParseError, extract_candidates, parse_text
from .test_helpers import syllabus_pdf


class ParserTests(SimpleTestCase):
    def test_supported_dates(self):
        for value in ("9/15/2026", "09/15/26", "9-15-2026", "9-15-26", "2026-09-15",
                      "September 15, 2026", "Sep 15 2026", "Sept. 15th, 2026", "9/15", "September 15"):
            with self.subTest(value=value):
                row = parse_text(f"Homework 1 - {value}", year=2026)[0]
                self.assertEqual(row["due_date"], "2026-09-15")
                self.assertTrue(row["include"])

    def test_terminal_punctuation(self):
        self.assertEqual(parse_text("Quiz 1 due 9/15/2026.")[0]["due_date"], "2026-09-15")

    def test_missing_year_is_explicitly_flagged(self):
        row = parse_text("Quiz 1 - 9/15", year=2026)[0]
        self.assertIn("Year assumed", row["warnings"][0])
        self.assertEqual(parse_text("Quiz 1 - 9/15")[0]["due_date"], "")

    def test_leap_year(self):
        self.assertEqual(parse_text("Lab 1 - 2/29", year=2028)[0]["due_date"], "2028-02-29")
        self.assertFalse(parse_text("Lab 1 - 2/29", year=2026)[0]["include"])

    def test_invalid_and_ambiguous_dates_require_review(self):
        for line in ("Homework 1 - 02/30/2026", "Quiz 1 - TBA", "Project 1 - 9/1 to 9/15",
                     "Exam - 13/02/2026", "Lab 1 - 2026-15-01", "Project - September 1–15", "Lab - 9/1–15"):
            with self.subTest(line=line):
                row = parse_text(line, year=2026)[0]
                self.assertEqual(row["due_date"], "")
                self.assertFalse(row["include"])
                self.assertTrue(row["warnings"])

    def test_types_and_grading_rows(self):
        cases = {"Homework 1": "assignment", "HW2": "assignment", "Quizzes": "quiz",
                 "Midterm": "exam", "Final exam": "exam", "Final project": "project",
                 "Lab 1": "lab", "Presentation": "presentation", "No class": "event"}
        for title, kind in cases.items():
            with self.subTest(title=title):
                self.assertEqual(parse_text(f"{title} - 9/15", year=2026)[0]["item_type"], kind)
        self.assertEqual(parse_text("Homework 20%\nInstructor office hours 9/15\nWelcome"), [])

    def test_adjacent_date_and_title_lines(self):
        for text in ("Homework 1\n9/15/2026", "9/15/2026\nHomework 1"):
            rows = parse_text(text)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["due_date"], "2026-09-15")

    def test_does_not_inherit_dates_across_unrelated_lines(self):
        row = parse_text("9/15/2026\nIntroduction\nQuiz 1")[0]
        self.assertEqual(row["due_date"], "")

    def test_time_and_different_year_are_flagged(self):
        row = parse_text("Exam 9/15/2027 at 10:00 AM", year=2026)[0]
        self.assertEqual(len(row["warnings"]), 2)

    def test_real_pdf_extraction_preserves_source_and_deduplicates(self):
        rows = extract_candidates(BytesIO(syllabus_pdf("Quiz 1 - 9/15\nQuiz 1 - 9/15", pages=2)), year=2026)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_page"], 1)
        self.assertEqual(rows[0]["source_text"], "Quiz 1 - 9/15")

    def test_rejects_bad_pdf(self):
        for data in (b"not a pdf", b"%PDF-1.4\nbroken"):
            with self.subTest(data=data), self.assertRaises(SyllabusParseError):
                extract_candidates(BytesIO(data))

    def test_rejects_encrypted_pdf(self):
        with self.assertRaisesMessage(SyllabusParseError, "Password-protected"):
            extract_candidates(BytesIO(syllabus_pdf(password="secret")))

    def test_rejects_image_only_or_blank_pdf(self):
        with self.assertRaisesMessage(SyllabusParseError, "No readable text"):
            extract_candidates(BytesIO(syllabus_pdf(text="")))

    def test_rejects_page_limit(self):
        with self.assertRaisesMessage(SyllabusParseError, "30 pages"):
            extract_candidates(BytesIO(syllabus_pdf(pages=31)))

    def test_rejects_byte_limit(self):
        with self.assertRaisesMessage(SyllabusParseError, "10 MB"):
            extract_candidates(BytesIO(b"%PDF-" + b"x" * MAX_BYTES))

    def test_does_not_silently_truncate_candidates(self):
        text = "\n".join(f"Homework {i} - 9/15" for i in range(101))
        with self.assertRaisesMessage(SyllabusParseError, "100 possible items"):
            extract_candidates(BytesIO(syllabus_pdf(text)), year=2026)

    def test_text_with_no_deadlines_returns_empty(self):
        self.assertEqual(extract_candidates(BytesIO(syllabus_pdf("Welcome to CMPE 131"))), [])


class SyllabusWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="student")
        cls.other = get_user_model().objects.create_user(username="classmate")
        cls.outsider = get_user_model().objects.create_user(username="outsider")
        cls.course = Course.objects.create(code="CMPE131", name="Software Engineering", section="1", semester="fall", year=2026)
        CourseEnrollment.objects.create(user=cls.user, course=cls.course)
        CourseEnrollment.objects.create(user=cls.other, course=cls.course)

    def setUp(self):
        self.client.force_login(self.user)

    def upload(self, text="Homework 1 - 9/15/2026", data=None, name="syllabus.pdf", course=None):
        return self.client.post(reverse("upload_syllabus"), {
            "course": (course or self.course).pk,
            "syllabus": SimpleUploadedFile(name, data if data is not None else syllabus_pdf(text), content_type="application/pdf"),
        })

    def draft(self, text="Homework 1 - 9/15/2026"):
        response = self.upload(text)
        self.assertEqual(response.status_code, 302)
        return SyllabusImport.objects.latest("created_at")

    def review_url(self, draft):
        return reverse("academics:syllabus_review", args=[draft.pk])

    def review_data(self, draft):
        data = {"items-TOTAL_FORMS": str(len(draft.candidates)), "items-INITIAL_FORMS": str(len(draft.candidates))}
        for index, row in enumerate(draft.candidates):
            for key in ("title", "due_date", "item_type"):
                data[f"items-{index}-{key}"] = row[key]
            if row["include"]:
                data[f"items-{index}-include"] = "on"
        return data

    def test_upload_stages_without_publishing_and_review_renders(self):
        draft = self.draft()
        self.assertEqual(draft.status, SyllabusImport.Status.DRAFT)
        self.assertEqual(len(draft.file_hash), 64)
        self.assertFalse(CourseAssignment.objects.exists())
        response = self.client.get(self.review_url(draft))
        self.assertContains(response, "Publish selected items")
        self.assertContains(response, "Homework 1")
        self.assertContains(response, "2026-09-15")

    def test_edited_rows_publish_and_are_visible_to_classmates(self):
        draft = self.draft()
        data = self.review_data(draft)
        data.update({"items-0-title": "Revised homework", "items-0-due_date": "2026-09-20", "items-0-item_type": "project"})
        response = self.client.post(self.review_url(draft), data)
        self.assertRedirects(response, reverse("academics:course_detail", args=[self.course.pk]))
        item = CourseAssignment.objects.get()
        self.assertEqual((item.title, item.due_date, item.item_type), ("Revised homework", date(2026, 9, 20), "project"))
        self.assertEqual(item.source, "SYLLABUS")
        self.assertEqual(item.verified_by, self.user)
        self.assertEqual(item.source_text, draft.candidates[0]["source_text"])
        self.client.force_login(self.other)
        self.assertContains(self.client.get(reverse("academics:course_detail", args=[self.course.pk])), item.title)
        self.assertContains(self.client.get(reverse("calendar")), item.title)

    def test_invalid_review_does_not_partially_save(self):
        draft = self.draft("Homework 1 - 9/15/2026\nQuiz 1 - 9/16/2026")
        data = self.review_data(draft)
        data["items-1-due_date"] = "2026-02-30"
        self.assertContains(self.client.post(self.review_url(draft), data), "Enter a valid date")
        self.assertFalse(CourseAssignment.objects.exists())
        draft.refresh_from_db()
        self.assertEqual(draft.status, SyllabusImport.Status.DRAFT)

    def test_unchecked_invalid_row_is_skipped(self):
        draft = self.draft("Homework 1 - 9/15/2026\nQuiz 1 - TBA")
        data = self.review_data(draft)
        data["items-1-due_date"] = "bad-date"
        self.assertEqual(self.client.post(self.review_url(draft), data).status_code, 302)
        self.assertEqual(CourseAssignment.objects.count(), 1)

    def test_uncertain_item_requires_correction_before_inclusion(self):
        draft = self.draft("Quiz 1 - TBA")
        data = self.review_data(draft)
        data["items-0-include"] = "on"
        self.assertContains(self.client.post(self.review_url(draft), data), "Required for an included item")
        data["items-0-due_date"] = "2026-09-15"
        self.assertEqual(self.client.post(self.review_url(draft), data).status_code, 302)
        self.assertEqual(CourseAssignment.objects.count(), 1)

    def test_duplicate_upload_and_repeated_post_are_idempotent(self):
        for _ in range(2):
            draft = self.draft()
            data = self.review_data(draft)
            for _ in range(2):
                self.assertEqual(self.client.post(self.review_url(draft), data).status_code, 302)
        self.assertEqual(CourseAssignment.objects.count(), 1)

    def test_duplicate_title_case_and_whitespace_are_normalized(self):
        for title in ("Homework 1", "  HOMEWORK   1  "):
            draft = self.draft()
            data = self.review_data(draft)
            data["items-0-title"] = title
            self.client.post(self.review_url(draft), data)
        self.assertEqual(CourseAssignment.objects.count(), 1)

    def test_changed_dates_do_not_overwrite_published_rows(self):
        for day in (15, 16):
            draft = self.draft(f"Homework 1 - 9/{day}/2026")
            self.client.post(self.review_url(draft), self.review_data(draft))
        self.assertEqual(CourseAssignment.objects.count(), 2)

    def test_cancel_does_not_publish_and_cannot_be_replayed(self):
        draft = self.draft()
        self.client.post(self.review_url(draft), {"action": "cancel"})
        self.client.post(self.review_url(draft), self.review_data(draft))
        draft.refresh_from_db()
        self.assertEqual(draft.status, SyllabusImport.Status.CANCELLED)
        self.assertFalse(CourseAssignment.objects.exists())

    def test_all_unchecked_requires_cancel_or_selection(self):
        draft = self.draft()
        data = self.review_data(draft)
        data.pop("items-0-include")
        self.assertContains(self.client.post(self.review_url(draft), data), "Include at least one item")
        self.assertFalse(CourseAssignment.objects.exists())

    def test_empty_extraction_has_actionable_review_state(self):
        draft = self.draft("Welcome to CMPE 131")
        response = self.client.get(self.review_url(draft))
        self.assertContains(response, "No possible deadlines")
        self.assertNotContains(response, "Publish selected items")

    def test_missing_and_tampered_management_forms_are_rejected(self):
        draft = self.draft()
        for changes in ({"items-TOTAL_FORMS": "0"}, {"items-TOTAL_FORMS": "101"}, {"items-INITIAL_FORMS": "0"}):
            data = self.review_data(draft)
            data.update(changes)
            self.assertEqual(self.client.post(self.review_url(draft), data).status_code, 200)
            self.assertFalse(CourseAssignment.objects.exists())
        self.assertEqual(self.client.post(self.review_url(draft), {}).status_code, 200)
        self.assertFalse(CourseAssignment.objects.exists())

    def test_other_students_cannot_read_publish_or_cancel_private_draft(self):
        draft = self.draft()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.review_url(draft)).status_code, 404)
        self.assertEqual(self.client.post(self.review_url(draft), self.review_data(draft)).status_code, 404)
        self.assertEqual(self.client.post(self.review_url(draft), {"action": "cancel"}).status_code, 404)

    def test_nonmembers_cannot_read_course_or_upload_to_it(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(reverse("academics:course_detail", args=[self.course.pk])).status_code, 404)
        self.assertEqual(self.upload().status_code, 200)
        self.assertFalse(SyllabusImport.objects.exists())

    def test_membership_is_rechecked_at_review(self):
        draft = self.draft()
        CourseEnrollment.objects.filter(user=self.user).delete()
        self.assertEqual(self.client.post(self.review_url(draft), self.review_data(draft)).status_code, 404)

    def test_anonymous_access_redirects_to_login(self):
        draft = self.draft()
        self.client.logout()
        for url in (reverse("upload_syllabus"), self.review_url(draft), reverse("academics:course_add"),
                    reverse("academics:course_detail", args=[self.course.pk])):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/accounts/login/", response.url)

    def test_upload_validation_and_parse_errors_are_displayed(self):
        for data, name, message in ((b"bad", "bad.txt", "Only PDF"), (b"bad", "bad.pdf", "valid PDF"),
                                    (b"%PDF-broken", "bad.pdf", "could not be read"),
                                    (syllabus_pdf(text=""), "scan.pdf", "No readable text")):
            with self.subTest(name=name):
                self.assertContains(self.upload(data=data, name=name), message)
        self.assertFalse(SyllabusImport.objects.exists())

    def test_upload_form_size_and_pointer(self):
        upload = SimpleUploadedFile("large.pdf", b"%PDF-" + b"x" * MAX_BYTES)
        form = UploadForm({"course": self.course.pk}, {"syllabus": upload}, user=self.user)
        self.assertFalse(form.is_valid())
        upload = SimpleUploadedFile("valid.pdf", syllabus_pdf())
        form = UploadForm({"course": self.course.pk}, {"syllabus": upload}, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(upload.tell(), 0)

    def test_source_text_is_html_escaped(self):
        draft = self.draft("Quiz <script>alert(1)</script> - 9/15/2026")
        response = self.client.get(self.review_url(draft))
        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertContains(response, "&lt;script&gt;")

    def test_csrf_is_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(reverse("upload_syllabus"), {}).status_code, 403)

    def test_missing_file_shows_validation_error(self):
        response = self.client.post(reverse("upload_syllabus"), {"course": self.course.pk})
        self.assertContains(response, "This field is required")
        self.assertFalse(SyllabusImport.objects.exists())

    def test_different_offerings_remain_separate(self):
        response = self.client.post(reverse("academics:course_add"), {
            "code": "CMPE 131", "name": "Software Engineering", "section": "2", "semester": "fall", "year": "2026",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Course.objects.count(), 2)

    def test_invalid_type_or_title_cannot_be_published(self):
        draft = self.draft()
        for field, value in (("item_type", "invented"), ("title", ""), ("title", "x" * 201)):
            data = self.review_data(draft)
            data[f"items-0-{field}"] = value
            self.assertEqual(self.client.post(self.review_url(draft), data).status_code, 200)
            self.assertFalse(CourseAssignment.objects.exists())

    def test_matching_course_is_reused_without_overwriting_name(self):
        self.client.force_login(self.outsider)
        response = self.client.post(reverse("academics:course_add"), {
            "code": " cmpe 131 ", "name": "Alternate name", "section": "01", "semester": "fall", "year": "2026",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Course.objects.count(), 1)
        self.course.refresh_from_db()
        self.assertEqual(self.course.name, "Software Engineering")
        self.assertTrue(CourseEnrollment.objects.filter(user=self.outsider, course=self.course).exists())

    def test_pages_render_and_only_show_enrolled_course_data(self):
        draft = self.draft("Homework 1 - 9/15/2099")
        self.client.post(self.review_url(draft), self.review_data(draft))
        for name in ("course_list", "calendar", "dashboard", "upload_syllabus", "academics:course_add"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.assertContains(self.client.get(reverse("dashboard")), "Homework 1")
        self.client.force_login(self.outsider)
        for name in ("course_list", "calendar", "dashboard"):
            self.assertNotContains(self.client.get(reverse(name)), "Homework 1")
            self.assertNotContains(self.client.get(reverse(name)), "CMPE131")

    def test_publish_rolls_back_if_an_insert_fails(self):
        draft = self.draft("Homework 1 - 9/15/2026\nQuiz 1 - 9/16/2026")
        original = CourseAssignment.objects.get_or_create
        calls = 0

        def fail_second(**kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("Simulated database failure")
            return original(**kwargs)

        with patch("academics.services.CourseAssignment.objects.get_or_create", side_effect=fail_second):
            with self.assertRaises(RuntimeError):
                self.client.post(self.review_url(draft), self.review_data(draft))
        self.assertFalse(CourseAssignment.objects.exists())
        draft.refresh_from_db()
        self.assertEqual(draft.status, SyllabusImport.Status.DRAFT)
