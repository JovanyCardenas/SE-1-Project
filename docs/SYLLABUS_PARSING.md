# Syllabus parsing

## Try the flow

1. Use Python 3.12 or 3.13, create/activate a virtual environment, and run `pip install -r requirements.txt`.
2. Create `.env` from `.env.example`; set a nonempty `SECRET_KEY`, `DEBUG=True`, and localhost `ALLOWED_HOSTS`.
3. Run `python manage.py migrate` and `python manage.py runserver`.
4. Register or sign in. Open **Courses → Add or join a course**.
5. Enter the SJSU course code, section, semester, and year. Matching offerings share one course.
6. Open **Upload syllabus**, choose that course, and upload a text-based PDF.
7. Correct each proposed title, date, and type; uncheck unwanted rows. Original text and page numbers
   are available beside each proposal. Undated/ambiguous rows start unchecked.
8. Click **Publish selected items** to save shared course deadlines. They appear on the course page,
   calendar list, and (for future dates) dashboard. Cancel saves no deadlines; Review later preserves the draft.

Course identity is normalized for whitespace/case in codes and leading zeros in numeric sections.
For example, `CMPE 131`, section `01` matches `cmpe131`, section `1` for the same term and year.
This first version assumes SJSU; institution-aware matching is a future extension.

## Supported extraction

- Text PDFs up to 10 MB, 30 pages, 250,000 extracted characters, and 100 distinct proposed items.
- A page content stream over 5 MB is rejected before text extraction.
- Assignment/homework/HW, quiz, exam/midterm/final, project, lab, presentation, and common course-event keywords.
- Dates on the same line as the item; also a standalone date immediately before/after an item title.
- US numeric dates: `9/15/2026`, `9-15-26`, `9/15`.
- ISO dates: `2026-09-15`.
- English month names: `September 15, 2026`, `Sep 15 2026`, `Sept. 15th`, `September 15`.
- A missing year uses the selected course year and displays a warning.
- Invalid dates, compact date ranges, multiple dates, and missing dates require manual correction.
- Duplicate proposals are collapsed. No PDF content is sent to an external AI/API service.

The parser is deterministic and intentionally proposes rows for human review. It does not guarantee
correct extraction from every syllabus layout. Compare the review with the original file, especially
multi-column tables and text wrapping. Only dates are saved, not due times or time zones.

Scans/OCR, DOCX, grading weights, recurring events, arbitrary natural-language dates, and automatic
updates to previously published deadlines are not supported. Weight-only grading rows are skipped.
If a changed syllabus changes a title/date/type, it creates a separate reviewed item; it does not
silently replace the old one. Shared-item editing/deletion needs a future correction workflow.

## Data and permissions

The shared data lives in `academics`, following the project specification:

- `Course`: one offering, unique by normalized code/section/semester/year.
- `CourseEnrollment`: a unique user/course membership. Joining is self-service.
- `SyllabusImport`: private review draft with filename, SHA-256, extracted candidates, uploader, and status.
- `CourseAssignment`: published item with `SYLLABUS` source, original text/page, verifier, and import reference.

The original PDF is not retained or served as a public media file. Drafts are database-backed and visible
only to their uploader, who must still be enrolled. Published rows are visible to course members.
Any enrolled member can upload, review, and publish. There is no instructor-approval role yet.
Personal completion, grades, and notes are not stored on shared items.

Publication claims the draft and saves rows in one database transaction. Repeated submissions cannot
republish the same draft. A database uniqueness constraint prevents duplicate assignments across
imports using normalized title, due date, and type. Failures roll back the draft status and all new rows.
Different offerings keep separate deadlines. Source text is rendered using Django's HTML escaping.

The existing `/syllabus/upload/` URL now points to `academics.views.upload_syllabus`. Review/course URLs
are namespaced under `/academics/`. `planner.parser` re-exports the new parser for discoverability;
the old disconnected planner routes, forms, and templates remain legacy scaffolding and are not enabled.
Use `academics.parser.extract_candidates`; its proposals use `item_type`, include flags, and source metadata.

## Validation

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Tests generate real PDFs with pypdf and cover supported dates, incomplete/ambiguous rows, upload limits,
malformed/encrypted/blank PDFs, review edits, skipping, persistence, course reuse, access restrictions,
CSRF, HTML escaping, duplicate/replayed publication, and transaction rollback. No external API key is needed.

The new additive migration is `academics/migrations/0001_initial.py`. Apply it on deployment with
`python manage.py migrate`. Do not replace the old planner migrations or regenerate this migration
independently. The existing GitHub Actions workflow runs project checks, migration checks, and tests
on Python 3.12 and 3.13; wait for its result and teammate review before merging.
