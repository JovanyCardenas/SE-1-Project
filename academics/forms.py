import re

from django import forms
from django.forms import BaseFormSet, formset_factory
from django.utils import timezone

from .models import Course, CourseAssignment
from .parser import MAX_BYTES, MAX_CANDIDATES


class CourseForm(forms.Form):
    code = forms.CharField(max_length=30, label="Course code", help_text="For example, CMPE 131.")
    name = forms.CharField(max_length=200, label="Course name")
    section = forms.CharField(max_length=20, help_text="Use the section on your registration.")
    semester = forms.ChoiceField(choices=Course.SEMESTERS)
    year = forms.IntegerField(min_value=2000, max_value=2100, initial=lambda: timezone.localdate().year)

    def clean_code(self):
        return re.sub(r"\s+", "", self.cleaned_data["code"]).upper()

    def clean_section(self):
        value = re.sub(r"\s+", "", self.cleaned_data["section"]).upper()
        return str(int(value)) if value.isascii() and value.isdecimal() else value


class UploadForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.none())
    syllabus = forms.FileField(
        help_text="Text-based PDF, up to 10 MB and 30 pages. Scans require OCR first.",
        widget=forms.ClearableFileInput(attrs={"accept": ".pdf,application/pdf"}),
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["course"].queryset = Course.objects.filter(enrollments__user=user)

    def clean_syllabus(self):
        upload = self.cleaned_data["syllabus"]
        if not upload.name.lower().endswith(".pdf"):
            raise forms.ValidationError("Only PDF files are supported.")
        if upload.size > MAX_BYTES:
            raise forms.ValidationError("Choose a PDF no larger than 10 MB.")
        signature = upload.read(5)
        upload.seek(0)
        if signature != b"%PDF-":
            raise forms.ValidationError("This does not appear to be a valid PDF.")
        return upload


class CandidateForm(forms.Form):
    include = forms.BooleanField(required=False, label="Include this item")
    title = forms.CharField(max_length=200, required=False)
    due_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    item_type = forms.ChoiceField(choices=CourseAssignment.Kind.choices, required=False, label="Type")

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("include"):
            # Skipped rows need not have valid dates or titles.
            self._errors.clear()
            return cleaned
        for field in ("title", "due_date", "item_type"):
            if not cleaned.get(field) and field not in self.errors:
                self.add_error(field, "Required for an included item.")
        if cleaned.get("title"):
            cleaned["title"] = " ".join(cleaned["title"].split())
        return cleaned


class CandidateFormSet(BaseFormSet):
    def clean(self):
        super().clean()
        if self.total_form_count() != len(self.initial) or self.initial_form_count() != len(self.initial):
            raise forms.ValidationError("The review rows changed. Reload this page and try again.")
        if any(self.errors):
            return
        if not any(form.cleaned_data.get("include") for form in self.forms):
            raise forms.ValidationError("Include at least one item, or cancel this import.")


ReviewFormSet = formset_factory(
    CandidateForm, formset=CandidateFormSet, extra=0,
    max_num=MAX_CANDIDATES, absolute_max=MAX_CANDIDATES, validate_max=True,
)
