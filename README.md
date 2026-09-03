# Spartan Academic Planner

**SJSU CMPE 131 — Software Engineering I**

The **Spartan Academic Planner (SAP)** is a student-focused academic planning and productivity web application. It is designed to help college students organize course information, automatically turn syllabi into actionable assignments and events, manage personal academic planning, synchronize calendars, and connect with classmates.

This project is being developed by Group W01 for CMPE 131 while following the software engineering process, including planning, requirements, design, implementation, testing, documentation, and deployment.

## Project Status

**Current Phase:** project definition, requirements, and architecture planning

The project idea has been selected and the team is now developing the **Spartan Academic Planner**.

## Core Idea

Students often manage academic information across syllabi, LMS pages, calendars, emails, and personal notes. SAP is intended to reduce that manual work by creating a shared course layer and a private student planning layer.

When multiple students are taking the same exact class, they can use the same course record and the same verified syllabus-generated assignments instead of independently recreating the same information.

Each student can then add their own private assignments, events, reminders, notes, completion status, grades, and study planning information.

## Planned Features

### Syllabus Parsing

- Upload a course syllabus.
- Extract assignments, quizzes, exams, projects, deadlines, grading information, and important course events.
- Review and verify parser results before publishing them.
- Automatically create shared course assignments/events from verified syllabus data.
- Reuse the parsed syllabus and shared course items for other students who join the same exact class.

### Shared Courses

A shared course record is planned to include:

- Class name
- Short name/course code
- Course section
- Semester
- Year
- Syllabus file

Students enrolled in the same exact course offering can share course-level information while keeping their personal academic data private.

### Shared vs. Personal Academic Items

**Shared course items** may include:

- Syllabus-generated assignments
- Exams
- Quizzes
- Projects
- Course deadlines
- Shared grading categories

**Personal student items** may include:

- Manually created assignments
- Study sessions
- Personal reminders
- Personal course events
- Completion status
- Personal notes
- Scores/grades
- Estimated effort

Items that were not generated from the syllabus should be clearly marked by their source, such as `MANUAL` or `CALENDAR_SYNC`.

### Calendar Integration

SAP is planned to support calendar importing and **two-way synchronization**, beginning with Google Calendar.

With two-way synchronization:

- Events created or changed in a linked Google Calendar can appear in SAP.
- Events or assignments created or changed in SAP can appear in the selected Google Calendar.
- External event IDs will be tracked to avoid duplicate items.
- Sync conflicts should be detected instead of silently overwriting data.
- Standard `.ics` export/subscription may also be supported for other calendar applications.

### Classmates, Privacy, and Communication

Students should be able to see and communicate with other students enrolled in the same course.

Users can set their account to **private**. In private mode:

- Other classmates do not see the user's identifying profile information in the normal classmate list.
- Other students cannot initiate communication with the private user.
- The private user can choose to message another student first.
- After the private user initiates contact, their identity can be shared with that student within the conversation without making the profile public to everyone else.

### Academic Planning

Additional planned planner features include:

- Calendar and upcoming-deadline views
- Weekly workload summaries
- Estimated study time
- Crunch-week indicators
- Assignment completion tracking
- Grade projections and hypothetical grade scenarios
- Customizable student planning views

## High-Level Data Concept

```text
Shared Course
├── Course information
├── Syllabus
├── Syllabus-generated assignments
├── Syllabus-generated events
└── Shared grading information

Student Enrollment
└── connects each user to the shared course

Private Student Layer
├── Completion status
├── Scores / grades
├── Personal notes
├── Manual assignments
├── Study sessions
├── Personal events
└── Calendar connections
```

The main design principle is:

> **Shared academic information should be created once, while personal planning information remains unique to each student.**

## Frameworks & Tools

Current/planned project tools include:

- Python
- Django
- HTML
- CSS
- JavaScript
- SQLite for local development
- PostgreSQL for deployment
- Docker
- GitHub
- GitHub Actions
- GitHub Wiki
- Render
- Progressive Web App setup

Additional integrations or dependencies may be added as development begins, including syllabus parsing and calendar synchronization libraries/APIs.

## Team Members

- Jovany Cardenas Vargas
- Fawad Afzal
- Terence Aung
- Aman Bose

## Repository Workflow

This repository uses a protected `main` branch.

Team workflow:

1. Pull the latest `main`.
2. Create a new branch.
3. Make changes.
4. Commit changes.
5. Push the branch.
6. Open a pull request.
7. Wait for GitHub Actions to pass.
8. Get a teammate review.
9. Merge into `main`.

Basic commands:

```bash
git checkout main
git pull origin main
git checkout -b feature/example-name

# Make changes

git add .
git commit -m "Describe the change"
git push -u origin feature/example-name
```

See the project's Git Workflow documentation for the full team workflow.

## Running the Project Locally

Clone the repository:

```bash
git clone https://github.com/JovanyCardenas/SE-1-Project.git
cd SE-1-Project
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file using `.env.example` as a guide.

Run migrations:

```bash
python manage.py migrate
```

Start the development server:

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Running with Docker

Build and start the project:

```bash
docker compose up --build
```

Run migrations:

```bash
docker compose exec web python manage.py migrate
```

Create an admin user:

```bash
docker compose exec web python manage.py createsuperuser
```

Stop the containers:

```bash
docker compose down
```

## Documentation

Project documentation can be maintained in the repository and GitHub Wiki.

Suggested documentation areas include:

- Project Overview
- Academic Planner Specification
- Requirements
- User Stories
- Database Design
- Syllabus Parser
- Calendar Synchronization
- Privacy & Messaging
- Testing Plan
- Git Workflow
- Setup Guide
- Meeting Notes

## Deployment

The project is planned to be deployed using Render.

Deployment may include:

- Render Python web service
- Render PostgreSQL database
- Gunicorn
- WhiteNoise for static files
- Environment variables for production settings

## License

TBD
