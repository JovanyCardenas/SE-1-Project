# Spartan Academic Planner (SAP) — Technical Specification & Roadmap

## 1. Project Overview & Vision
The **Spartan Academic Planner** is a student-centric platform designed to bridge the gap between static course syllabi and actionable weekly workloads. Unlike standard LMS platforms (e.g., Canvas), SAP focuses on student personal productivity:
* Automatically parsing course syllabi into tasks, due dates, and grade weights.
* Projecting weekly workloads (in estimated hours) so students can predict "crunch weeks."
* Providing an interactive, exportable academic calendar (.ics / Google Calendar).
* Fostering peer collaboration through an organized Course Resource Hub.

---

## 2. Django Architecture & App Boundaries

    SE-1-Project/
    ├── core/         # Global config, banners, maintenance, feature flags, impersonation
    ├── accounts/     # User profile, major, academic standing, UI theme settings
    ├── academics/    # Terms, Courses, Syllabus parsing, Assignments, Grade categories
    ├── degreeplan/   # CSEP / Education plan, degree catalog, prerequisite validation
    ├── planner/      # Calendar views, weekly effort distribution, iCal feed generation
    └── hub/          # Course resources, study materials, upvotes, and comments

### Module Responsibility Breakdown

| App | Key Models | Primary Responsibilities |
| :--- | :--- | :--- |
| **core** | SystemSetting, SiteBanner, FeatureToggle | Site-wide controls, superuser tools, maintenance middleware, banner context. |
| **accounts** | Profile, StudentPreference | Auth extensions, university ID, major, UI customization (accent colors). |
| **academics** | Term, Course, SyllabusDocument, GradingCategory, Assignment | Course rosters, PDF upload & text extraction, assignment weights, grade computation. |
| **degreeplan** | DegreeProgram, CatalogCourse, StudentEducationPlan, PlannedSemester, PlannedCourseItem | Master course catalog, prerequisite checking, multi-semester plan builder, unit load limits. |
| **planner** | WorkloadSnapshot, CustomEvent | Weekly workload heuristics, FullCalendar JSON feed, .ics calendar sync. |
| **hub** | ResourcePost, ResourceVote, ResourceComment | Peer study guides, cheatsheet sharing, document tags, voting system. |

---

## 3. Data Schema (Core Entity Relationships)

    User (Student)
      │
      ├── Profile (major, term, theme_color)
      │
      ├── StudentEducationPlan (CSEP Macro Plan)
      │     │
      │     └── PlannedSemester (e.g., Fall 2026, order: 1)
      │           │
      │           └── PlannedCourseItem (status: Planned/Completed)
      │                 └── FK -> CatalogCourse (code: "CS 146", units: 3)
      │                             └── M2M -> Prerequisites (CatalogCourse)
      │
      ├── CourseEnrollment (m2m -> Course)
      │     │
      │     ├── Course (code: "CS 146", title: "Data Structures", instructor)
      │     │     │
      │     │     ├── SyllabusDocument (file, status: PENDING/PARSED/VERIFIED)
      │     │     ├── GradingCategory (name: "Midterms", weight: 30.0%)
      │     │     │
      │     │     ├── Assignment
      │     │     │     ├── title, due_date, estimated_hours
      │     │     │     ├── weight_category (FK -> GradingCategory)
      │     │     │     ├── score_earned, points_possible, completed (bool)
      │     │     │     └── is_custom (bool: student-added vs. syllabus-parsed)
      │     │     │
      │     │     └── ResourcePost
      │     │           ├── post_type (NOTE, GUIDE, LINK, EXAM_PREP)
      │     │           ├── file / url / description
      │     │           ├── Upvotes (FK -> User)
      │     │           └── Comments (FK -> User, threaded)
      │     │
      │     └── WorkloadBlock (calculated weekly hours, stress-index)


---

## 4. Feature Implementation Details

### A. Syllabus Ingestion & Verification
1. **Upload Pipeline:** Upload PDF to `media/syllabi/<course_id>/`.
2. **Text Extraction:** Process text via `pdfplumber` or `pypdf`.
3. **Pattern Matching / LLM Heuristic:** Extract tables/lines containing:
   * Dates (`MM/DD`, `Week X`, `Month Day`).
   * Deliverable titles (`Homework 1`, `Milestone 2`, `Midterm Exam`).
   * Grade weight percentages (`Exams: 30%`, `Labs: 20%`).
4. **Staging / Verification Step:** Parse into temporary JSON staging rows so students can verify, edit inaccurate dates, and approve before rows write to `academics_assignment`.

### B. Smart Workload & Effort Planner
* **Weekly Aggregator:** Query assignments grouped by calendar week:
  * `Total Hours = Sum of (assignment.estimated_hours)`
* **Workload Index Badge:**
  * `< 10 hrs/week`: Light (Green)
  * `10–25 hrs/week`: Moderate (Blue)
  * `> 25 hrs/week`: High Crunch Week (Red Alert)
* **Grade Projection Calculator:**
  * `Current Grade = Sum of ((Earned Points / Possible Points) * Category Weight)`

### C. Calendar & iCal Export
* **Interactive Grid:** Client-side grid using Tailwind CSS or FullCalendar consuming `/api/planner/events/`.
* **Dynamic iCal Feed:** Endpoint at `/planner/feed/<uuid:feed_token>.ics` generating a valid RFC 5545 `.ics` file using the `icalendar` Python package for Google Calendar / Apple Calendar subscription.

### D. Semester Education Plan (CSEP / Degree Roadmap)
1. **Multi-Semester Board:** Kanban-style column layout where each column represents a planned semester (e.g., Fall 2026, Spring 2027).
2. **Prerequisite Graph Validator:**
   * When placing a course into Semester N, the system checks that all prerequisites exist in semesters where `order < N`.
   * Unmet prerequisites trigger warning badges on the card.
3. **Unit Load Tracking:** Live unit calculation per semester column (flags overloads >17 units or part-time status <12 units).
4. **Semester Activation:** One-click conversion from a "Planned Semester" into active `academics.Course` records for the current term.

### E. Course Resource Hub
* Course-scoped feed where students share:
  * Lecture summaries, cheatsheets, recommended external links.
  * Upvote mechanism (`ResourceVote` with unique constraint on `(user, post)`).
  * Filter by category tags (`#exam-prep`, `#cheatsheet`, `#project-tips`).

---

## 5. Team Division of Labor (4 Team Members)

    ┌─────────────────────────────────────────────────────────────┐
    │ Team Member 1: Infrastructure & Data Architecture (Backend) │
    │ - accounts, core, and academics data models                 │
    │ - Course CRUD, enrollment logic, grade weighting engine     │
    │ - Superuser/Admin tooling expansions                        │
    └─────────────────────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────────────────────┐
    │ Team Member 2: Syllabus Parsing Engine & Pipeline (Backend) │
    │ - PDF ingestion and raw text extraction                     │
    │ - Date/assignment extraction heuristics                     │
    │ - Verification UI & staging review controller               │
    └─────────────────────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────────────────────┐
    │ Team Member 3: Planner, Workload & Calendar Sync (Fullstack)│
    │ - Calendar view (Tailwind grid / FullCalendar integration)  │
    │ - Weekly workload & crunch-week calculator                  │
    │ - Dynamic .ics export feed view                             │
    └─────────────────────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────────────────────┐
    │ Team Member 4: Course Resource Hub & UI/UX (Frontend/Hub)   │
    │ - Hub models, file uploads, upvotes, and comments           │
    │ - Course community feed, tag filters, search UI             │
    │ - Responsive Tailwind styling & PWA offline enhancements    │
    └─────────────────────────────────────────────────────────────┘


---

## 6. Sprint Plan & Milestones

### Sprint 1: Architecture & Foundation
* [ ] Create `academics`, `degreeplan`, `planner`, and `hub` Django apps via `python manage.py startapp`.
* [ ] Implement `CatalogCourse`, `Course`, `Term`, and `Assignment` models in `academics/models.py`.
* [ ] Add mock catalog courses with prerequisite relationships and assignments to verify database relationships.
* [ ] Gate new routes behind existing `FeatureToggle` keys (e.g., `enable_academic_planner`, `enable_sep`).

### Sprint 2: Core Academic Tracking & UI
* [ ] Build the Multi-Semester CSEP view with unit calculation per column.
* [ ] Implement backend prerequisite validation on course assignment.
* [ ] Build student Course Dashboard (list enrolled courses, grades, upcoming tasks).
* [ ] Implement assignment creation modal (manual entry for non-syllabus items).
* [ ] Build the Grade Weight Calculator on the course detail page.
* [ ] Setup initial calendar layout in `planner/`.

### Sprint 3: Syllabus Parsing & Workload Heuristics
* [ ] Integrate `pdfplumber` for syllabus file uploads.
* [ ] Build the parser verification interface (preview before save).
* [ ] Implement weekly effort calculation and crunch-week alerts.
* [ ] Implement `.ics` calendar subscription endpoint.

### Sprint 4: Community Hub & Final Polish
* [ ] Build `hub/` resource posting, voting, and comment threads.
* [ ] Audit mobile responsiveness and test PWA manifest/offline caching.
* [ ] Run superuser impersonation to test student workflows across accounts.
* [ ] Prepare documentation and presentation slides for class deliverables.

---

## 7. Recommended Initial Tech Stack Dependencies

Add these to your `requirements.txt`:

```text
pdfplumber>=0.11.0
icalendar>=5.0.0
python-dateutil>=2.9.0

---

## 8. Quality Assurance & Course Deliverables

### A. Testing Strategy
* **Prerequisite Engine:** Unit tests verifying valid chains (e.g., CS 46A -> CS 46B -> CS 146) and catching circular prerequisite dependencies.
* **Grade & Workload Calculations:** Unit tests verifying weighted scoring math with zero-point exceptions and edge-case date boundaries.
* **Automated CI:** GitHub Actions workflow executing `python manage.py test` on pull requests to `main`.

### B. Security & Data Protection
* User isolation: All querysets scoped strictly to `request.user` to prevent cross-account grade/assignment leaks.
* File Upload Sanitization: Restrict uploads to `.pdf`, `.docx`, `.png`, `.jpg` with a hard limit of 10 MB.

### C. Seed Fixtures & Demo Readiness
* Create `fixtures/sample_catalog.json` containing foundational courses and prerequisites for quick database initialization:
  `python manage.py loaddata sample_catalog.json`