# SE-1-Project
SJSU CMPE 131 - Software Engineering 1

This project is being developed by our Group for CMPE 131. The goal is to build a useful software product as a team while going through the software development process, including planning, requirements, design, implementation, testing, documentation, and deployment.

## Project Status
Current Phase: starter setup and project planning

The final project idea is still being decided. The current direction is a student-focused web application that could be useful for SJSU students.

# Frameworks & Tools Used
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

# Project Description

TBD

# Team Members
* Jovany Cardenas Vargas
* Fawad Afzal
* Terence Aung
* Aman Bose

## Repository Workflow

This repository uses a protected `main` branch.

Team workflow:

1. Pull the latest `main`
2. Create a new branch
3. Make changes
4. Commit changes
5. Push the branch
6. Open a pull request
7. Wait for GitHub Actions to pass
8. Get a teammate review
9. Merge into `main`

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

## Running The Project Locally

Clone the repository:

```bash
git clone https://github.com/JovanyCardenas/SE-1-Project.git
cd SE-1-Project
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
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

Start the server:

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Running With Docker

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

More project documentation can be found in the GitHub Wiki.

Suggested wiki pages:

- Project Overview
- Django Basics
- GitHub Basics
- Git Workflow
- Setup Guide
- Requirements
- User Stories
- Database Design
- Testing Plan
- Meeting Notes

## Deployment

The project is planned to be deployed using Render.

Deployment setup may include:

- Render Python web service
- Render PostgreSQL database
- Gunicorn
- WhiteNoise for static files
- Environment variables for production settings

## License

TBD.
