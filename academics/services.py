import hashlib

from django.db import transaction
from django.utils import timezone

from .models import CourseAssignment, SyllabusImport


def assignment_fingerprint(title, due_date, item_type):
    normalized = " ".join(title.split()).casefold()
    return hashlib.sha256(f"{normalized}\n{due_date.isoformat()}\n{item_type}".encode()).hexdigest()


@transaction.atomic
def publish_import(draft_id, user, reviewed_rows):
    """Claim the draft once, then insert verified rows in the same transaction."""
    draft = SyllabusImport.objects.get(
        pk=draft_id, uploaded_by=user, course__enrollments__user=user,
    )
    claimed = SyllabusImport.objects.filter(pk=draft.pk, status=SyllabusImport.Status.DRAFT).update(
        status=SyllabusImport.Status.PUBLISHED, published_at=timezone.now(),
    )
    if not claimed:
        return 0, 0
    created_count = duplicate_count = 0
    for row, original in zip(reviewed_rows, draft.candidates, strict=True):
        if not row.get("include"):
            continue
        _, created = CourseAssignment.objects.get_or_create(
            course=draft.course,
            fingerprint=assignment_fingerprint(row["title"], row["due_date"], row["item_type"]),
            defaults={
                "title": row["title"], "due_date": row["due_date"], "item_type": row["item_type"],
                "source_import": draft, "source_text": original["source_text"],
                "source_page": original["source_page"], "verified_by": user,
            },
        )
        created_count += int(created)
        duplicate_count += int(not created)
    return created_count, duplicate_count
