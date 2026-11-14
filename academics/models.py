import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Course(models.Model):
    SEMESTERS = [(value, value.title()) for value in ("spring", "summer", "fall", "winter")]

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30)
    section = models.CharField(max_length=20)
    semester = models.CharField(max_length=10, choices=SEMESTERS)
    year = models.PositiveIntegerField(validators=[MinValueValidator(2000), MaxValueValidator(2100)])

    class Meta:
        ordering = ["-year", "semester", "code", "section"]
        constraints = [
            models.UniqueConstraint(fields=["code", "section", "semester", "year"], name="unique_course_offering")
        ]

    def __str__(self):
        return f"{self.code}-{self.section} · {self.get_semester_display()} {self.year}"


class CourseEnrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "course"], name="unique_course_enrollment")]


class SyllabusImport(models.Model):
    """Private, persistent review draft. The original PDF is not publicly stored."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Awaiting review"
        PUBLISHED = "published", "Published"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="syllabus_imports")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64)
    candidates = models.JSONField(default=list)
    analysis = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)


class CourseAssignment(models.Model):
    class Kind(models.TextChoices):
        ASSIGNMENT = "assignment", "Assignment"
        QUIZ = "quiz", "Quiz"
        EXAM = "exam", "Exam"
        PROJECT = "project", "Project"
        LAB = "lab", "Lab"
        PRESENTATION = "presentation", "Presentation"
        EVENT = "event", "Course event / deadline"
        CLASS_SESSION = "class_session", "Class session"

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=200)
    item_type = models.CharField(max_length=20, choices=Kind.choices)
    due_date = models.DateField(null=True, blank=True)
    schedule_details = models.JSONField(default=dict, blank=True)
    source = models.CharField(max_length=20, default="SYLLABUS", editable=False)
    source_import = models.ForeignKey(SyllabusImport, on_delete=models.SET_NULL, null=True, related_name="assignments")
    source_text = models.TextField(blank=True)
    source_page = models.PositiveIntegerField(null=True, blank=True)
    fingerprint = models.CharField(max_length=64, editable=False)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date", "title"]
        constraints = [models.UniqueConstraint(fields=["course", "fingerprint"], name="unique_syllabus_assignment")]

    def __str__(self):
        return self.title
