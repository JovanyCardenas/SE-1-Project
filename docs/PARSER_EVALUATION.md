# Local parser evaluation

Status: development prototype, evaluated locally on November 13, 2026. No deployment is part of
this iteration. All parsing runs locally without sending syllabus content to an external AI API.

## Reproducible regression checks

`python manage.py evaluate_syllabus_parser` runs 24 synthetic labeled cases from
`academics/fixtures/syllabus_cases.json`. Expected item titles, dates, types, and selected summary
counts/statuses are compared with output. Cases cover final-only syllabi, absent deadlines,
different column orders, weekly outlines, relative dates, ranges, separate release/due dates,
grading, recurring meetings, policy noise, missing years, and conflicting weekdays.

The current cases pass. These examples were used while developing the rules. Their pass rate is
not an accuracy estimate on unseen syllabi. Summary-group count checks also do not demonstrate
that every value in those groups is correct.

The Django suite includes integration and PDF tests in addition to these cases: upload validation,
review/publication, private report access, undated persistence, calendar filtering, duplicate
handling, rollback, and regressions found in real documents. Passing these verifies behavior under
test, not universal document understanding.

## Real-document development checks

Four text-based SJSU syllabi were used to inspect and improve extraction. They are development
examples, not an independent held-out test set. PDFs and their full extracted contents are not
committed to this repository.

| Document | Why it was useful |
| --- | --- |
| User-provided CMPE 140, Fall 2026 | Six-page document with substantial policy prose, a dated topic table, grading table, assessment counts, and an inconsistent final-exam weekday |
| [CS 256, Spring 2025](https://www.sjsu.edu/cs/docs/spring25_syllabi/CS256_Syllabus_Spring%202025_Maryam%20Khazaei%20Pool.pdf) | Narrative exam dates, time ranges, schedule rows, and inconsistent references to the final |
| [CS 259, Fall 2025](https://www.sjsu.edu/cs/docs/syllabi/fall25/Chun_CS259-Syllabus-PDF.pdf) | Weights before component labels, relative exam weeks, and lecture-number ranges |
| [CS 165C, Fall 2025](https://www.sjsu.edu/cs/docs/syllabi/fall25/CS-165C%20sect%201%20Syllabus%20Fall%202025_Combs.pdf) | Narrative weekly topics with nested assessments, grading notes, and an explicit statement that there is no written final exam |

These checks caught errors that the first synthetic examples missed: time ranges mistaken for
dates, week/lecture ranges mistaken for numeric dates, negated exams becoming tasks, shifted table
columns truncating labels, and rounding examples becoming grading components. Targeted regressions
now cover those failures.

For the supplied CMPE 140 document, the current extraction produces 34 proposed schedule items
(26 class sessions and eight named assessments/events), five grading components, and four
assessment-count summaries. The final weekday/date disagreement is flagged. These are observed
output counts, not a ground-truth recall claim. Homework/lab counts do not supply individual due
dates, so none are fabricated.

## What is still needed before a readiness claim

1. Assemble a separately annotated collection that the parser rules were not developed against,
   spanning institutions, departments, narrative/table formats, term lengths, and sparse schedules.
2. Label expected assessments, class sessions, grading, dates, and source evidence separately.
   Measure missed items and false positives by category, exact-date correctness, and incorrect
   inferred deadlines. Include "no deadline provided" as a valid expected result.
3. Evaluate OCR separately before accepting scans. Current extraction cannot read image-only pages.
4. Add a user correction workflow for missed items and conflicting/duplicate mentions, and validate
   that workflow on genuinely unfamiliar documents.
5. Agree on acceptance thresholds from that evidence before merging or deploying.

No precision/recall percentage is claimed here: the real documents have not been exhaustively,
independently annotated. Known limitations include remaining duplicate paraphrases, incomplete
conflict resolution, unfamiliar layouts, partial scans, and non-English text.
