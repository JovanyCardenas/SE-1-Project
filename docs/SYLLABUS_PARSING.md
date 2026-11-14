# Local syllabus parsing

This is a deterministic extraction-and-review prototype. It uses local pypdf text extraction,
section recognition, table columns, and date/assessment rules. It makes no external AI or network
calls. It is not a claim of accurate extraction from every syllabus.

## Try locally

1. Use Python 3.12 or 3.13, create/activate a virtual environment, and install `requirements.txt`.
2. Create `.env` from `.env.example`; set `SECRET_KEY`, `DEBUG=True`, and localhost `ALLOWED_HOSTS`.
3. Run `python manage.py migrate` and `python manage.py runserver`.
4. Sign in, open **Courses → Add or join a course**, and enter code, section, semester, and year.
5. Open **Upload syllabus**, choose the numeric date order, and upload a text-based PDF.
6. Review titles, types, dates, warnings, source excerpts, and page numbers. Uncheck unwanted rows.
   Undated and conflicting rows start unchecked. Include an undated item with **Keep date unknown**;
   it is saved on the course page and excluded from the calendar and dated upcoming list.
7. Inspect **Other course information found** for grading, assessment counts, meetings, and policies.
   These are private reference findings, not planner tasks or shared grade-calculation settings.
   **Download extracted information** exports the original analysis as JSON, not the edited form.
8. **Publish selected items** saves reviewed course items. **Review later** retains the draft;
   **Cancel import** saves no course items. No course items are created by extraction alone.

Course matching normalizes whitespace/case and numeric section zeros: `CMPE 131`, section `01`
matches `cmpe131`, section `1` for the same term/year. Matching currently assumes SJSU.
Re-upload after a parser update; existing drafts retain their original analysis and published
items are not automatically reinterpreted or changed.

## What the analysis represents

| Syllabus content | Result |
| --- | --- |
| Named assignment, exam, project, lab, quiz, presentation | Proposed assessment, dated when evidence supplies a single valid date |
| Only a final-exam date | Final-exam proposal; no invented homework deadlines |
| Undated, TBA, week-relative or ranged assessment | Reviewable undated item with original wording |
| Date/topic or week/topic schedule | Class-session proposals, with readings retained where identified |
| Holiday, closure, exam-review session | Course-event proposal |
| "Five homework assignments" | Assessment overview with a count, not five fictional tasks |
| Percentage or points grading table | Private grading components |
| Recurring meeting, instructor details, policies | Separate private reference findings |

Supported table structures include date/topic, week/date/topic, topic/date, assignment/due,
weight/component, and week/topic/reading columns. Wrapped cells are joined when their indentation
matches the recognized structure. Columns and headings must still be recognizable; arbitrary
multicolumn layouts and extraction-order errors can cause omissions or misclassification.

Dates support ISO, English month names before/after the day, and numeric month/day or day/month
according to the upload choice. A missing year uses the course year with a warning. An explicit
due label can distinguish a release date from a deadline. Otherwise, multiple dates, ranges,
week numbers, and relative expressions are preserved without inventing one calendar date.
Weekday/date contradictions are flagged and start unchecked. Times are retained as reference text;
they do not create time-zone-aware events or reminders. Recurring meetings are not expanded.

Each proposed item includes source text/page, type/category, original date wording, date status,
warnings, and available time/reading text. The report also records blank pages and extraction counts.
These counts describe output, not how much of the source was successfully understood.

## Boundaries and remaining work

- Text PDFs only, up to 10 MB, 30 pages, 250,000 extracted characters, and 100 proposals.
  Page content streams above 5 MB are rejected before text extraction.
- No OCR is bundled. Image-only PDFs are rejected; mixed text/scanned documents warn about blank
  extracted pages. A partly scanned page may still contain some text and escape this warning.
- DOCX, handwriting, non-English wording, arbitrary natural-language dates, and every possible
  table layout are not supported or validated.
- Similar mentions with different wording may remain separate proposals. Contradictory statements
  are not comprehensively reconciled. Compare the source before publishing.
- Policies are retained as excerpts, not interpreted into enforceable academic rules.
- Shared item editing/deletion and automatic changes from updated syllabi are not implemented.
  Changed title/date/type creates a separate item instead of replacing an existing one.
- No manual missing-item form exists yet. Parser omissions therefore still need a future correction
  workflow in addition to editing the proposed rows.

## Architecture and permissions

The active upload path calls `academics.syllabus.analyze_syllabus(upload, year, date_order)`;
`analyze_pages()` accepts already extracted text for tests. The report has `items`, `grading`,
`assessment_overview`, `meetings`, `course_information`, `policies`, `warnings`, and `coverage`.
`academics.parser` supplies shared date/limit helpers and the older `extract_candidates` / `parse_text`
APIs, retained for compatibility. Those older APIs do not return the full structured report.
The disconnected planner upload routes/forms/templates remain legacy scaffolding.

- `Course` and `CourseEnrollment` represent a shared offering and membership.
- `SyllabusImport` stores private candidates and analysis, filename/hash, uploader, and status.
- `CourseAssignment` stores reviewed shared items, nullable `due_date`, provenance, verifier, and
  `schedule_details` containing original date/time/reading/category information.

Original PDFs are not retained or publicly served. Drafts/reports require their uploader to remain
enrolled. Shared items require course membership. Joining is self-service; any member may upload
and publish. There is no instructor-approval role. Source text is HTML-escaped.

Publication claims a draft and inserts rows atomically. Replays do not republish it. A unique
fingerprint combines normalized title, type, and date; for undated items it also uses original date
wording so the same topic in different weeks remains distinct. Failures roll back the transaction.
The original analysis download does not expose another member's draft and remains available by its
private report URL after publication.

## Validation

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py evaluate_syllabus_parser --report parser-evaluation.json
```

The evaluation command uses committed synthetic examples and exits with an error on mismatch.
Tests also generate PDFs and exercise review edits, undated publication, calendar exclusion,
access restrictions, CSRF, HTML escaping, duplicate/replayed publication, and rollback.
No external API key is needed. These regression checks do not measure accuracy on unseen syllabi.

Run migrations locally after updating: `0001_initial` creates the academic models, and
`0002_courseassignment_schedule_details_and_more` adds structured analysis, schedule details,
class sessions, and nullable dates. Existing dated rows are preserved. These instructions do not
authorize deployment or merging; this iteration remains local development work.
