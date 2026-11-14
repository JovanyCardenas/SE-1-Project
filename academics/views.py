import hashlib

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import CourseForm, ReviewFormSet, UploadForm
from .models import Course, CourseEnrollment, SyllabusImport
from .parser import SyllabusParseError
from .syllabus import analyze_syllabus
from .services import publish_import


@login_required
@require_http_methods(["GET", "POST"])
def course_add(request):
    form = CourseForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        values = form.cleaned_data.copy()
        name = values.pop("name")
        with transaction.atomic():
            course, _ = Course.objects.get_or_create(**values, defaults={"name": name})
            CourseEnrollment.objects.get_or_create(course=course, user=request.user)
        messages.success(request, f"Joined {course}. Existing shared course items are available below.")
        return redirect("academics:course_detail", pk=course.pk)
    return render(request, "academics/course_form.html", {"form": form})


@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk, enrollments__user=request.user)
    drafts = course.syllabus_imports.filter(uploaded_by=request.user, status=SyllabusImport.Status.DRAFT)
    return render(request, "academics/course_detail.html", {"course": course, "drafts": drafts})


@login_required
@require_http_methods(["GET", "POST"])
def upload_syllabus(request):
    form = UploadForm(
        request.POST if request.method == "POST" else None, request.FILES or None,
        user=request.user, initial={"course": request.GET.get("course")},
    )
    if request.method == "POST" and form.is_valid():
        upload = form.cleaned_data["syllabus"]
        course = form.cleaned_data["course"]
        try:
            analysis = analyze_syllabus(upload, year=course.year, date_order=form.cleaned_data.get("date_order") or "MDY")
            candidates = analysis.pop("items")
            for candidate in candidates:
                candidate["keep_undated"] = not bool(candidate["due_date"])
        except SyllabusParseError as exc:
            form.add_error("syllabus", str(exc))
        else:
            upload.seek(0)
            draft = SyllabusImport.objects.create(
                course=course, uploaded_by=request.user, filename=upload.name,
                file_hash=hashlib.sha256(upload.read()).hexdigest(), candidates=candidates, analysis=analysis,
            )
            return redirect("academics:syllabus_review", pk=draft.pk)
    return render(request, "pages/upload_syllabus.html", {
        "form": form, "has_courses": form.fields["course"].queryset.exists(),
    })


@login_required
@require_http_methods(["GET", "POST"])
def syllabus_review(request, pk):
    draft = get_object_or_404(
        SyllabusImport.objects.select_related("course"), pk=pk,
        uploaded_by=request.user, course__enrollments__user=request.user,
    )
    if draft.status != SyllabusImport.Status.DRAFT:
        messages.info(request, "This import has already been processed.")
        return redirect("academics:course_detail", pk=draft.course_id)
    if request.method == "POST" and request.POST.get("action") == "cancel":
        SyllabusImport.objects.filter(pk=draft.pk, status=SyllabusImport.Status.DRAFT).update(
            status=SyllabusImport.Status.CANCELLED,
        )
        messages.info(request, "Import cancelled.")
        return redirect("academics:course_detail", pk=draft.course_id)
    formset = ReviewFormSet(
        request.POST if request.method == "POST" else None, initial=draft.candidates, prefix="items",
    )
    if request.method == "POST" and formset.is_valid():
        created, duplicates = publish_import(draft.pk, request.user, formset.cleaned_data)
        messages.success(request, f"Published {created} shared items. Skipped {duplicates} existing duplicates.")
        return redirect("academics:course_detail", pk=draft.course_id)
    return render(request, "academics/syllabus_review.html", {
        "draft": draft, "formset": formset, "rows": zip(formset.forms, draft.candidates),
    })


@login_required
@require_http_methods(["GET"])
def syllabus_report(request, pk):
    draft = get_object_or_404(SyllabusImport, pk=pk, uploaded_by=request.user, course__enrollments__user=request.user)
    response = JsonResponse({**draft.analysis, "items": draft.candidates}, json_dumps_params={"indent": 2})
    response["Content-Disposition"] = 'attachment; filename="syllabus-extraction.json"'
    return response
