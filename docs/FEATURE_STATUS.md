# Feature status and next work

Checked against the local `feature/syllabus-parsing` working tree on November 13, 2026.
This includes uncommitted parser improvements after `a8f4676`; it is not a statement that these
changes are on `main` or deployed. The roadmap comes from `ACADEMIC_PLANNER_SPEC.md`.

| Area | Implemented | Remaining |
| --- | --- | --- |
| Accounts | Register, log in/out, profile editing, a public-profile flag | Account preferences/settings page, password recovery UI, enforcement of future classmate/message privacy rules |
| Shared courses | Create or join by normalized code/section/term/year; reuse shared items | Course search, leave/archive, course editing, institution-aware matching, shared syllabus/version management |
| Syllabus | Local text-PDF analysis, private review, dated/undated items, class schedules, reference findings, provenance, JSON export, reviewed publication | Broader independent evaluation, local OCR, add missing rows, shared corrections/deletion, conflict reconciliation, syllabus revision handling |
| Calendar/dashboard | Course list, five upcoming dated items, ordered calendar list | Month/week views, filters, actual due times/time zones, recurring events, reminders |
| Personal planner | Private manual assignments with create/edit/delete, optional course/date, notes and completion | Personal events; state on shared items; effort, hidden items and due overrides |
| Grading | Parsed weights/points retained privately with the import | Reviewed shared grading categories, item-category mapping, private scores, weighted totals and projections |
| Calendar integration | No integration app or sync endpoints | Google OAuth, calendar selection, two-way create/update/delete, external IDs, retries and conflict handling; optional ICS export |
| Classmates/messaging | Basic profile privacy preference only | Classmate directory, conversations, private-user contact rules, relationship-scoped identity reveal, block/report |
| Workload | Upcoming item list only | Weekly workload, effort estimates, crunch-week indicators, study blocks |
| Resources | Placeholder route | Optional course resource posts, links, comments and moderation |

Admin configuration, feature toggles, maintenance support, a PWA shell, and an older household
module also exist. They do not implement the missing academic-planner features. The dashboard Add Assignment now opens the private assignment form; settings remains a coming-soon page.
Old planner templates/routes are disconnected and should not be counted as working features.

## Suggested implementation order

1. Finish the correction workflow: add an omitted syllabus item, edit/delete reviewed shared items,
   resolve duplicates/conflicts, and retain a change history. Evaluate extraction on unseen syllabi.
2. Build the private student layer: manual assignments/events and independent completion/notes.
   Keep this separate from shared course items, including access-control tests with two students.
3. Build a useful calendar: week/month views, filters, times/time zones, recurring meetings, reminders.
4. Turn extracted grading into reviewed course settings; add private scores and grade calculations.
5. Add two-way Google Calendar synchronization with user-specific mappings and conflict handling.
6. Add classmates, privacy enforcement, and messaging. Workload planning and the resource hub follow.

The order is a proposal, not an expansion of the work completed in this parser iteration. Any
future extraction approach must respect the current requirement to run locally with no external AI API.
