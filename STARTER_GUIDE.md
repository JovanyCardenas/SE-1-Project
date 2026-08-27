# Django Team Starter Guide

This guide is for teammates who know Python but are new to Django and web development. It explains how the project is organized, how pages work, how accounts work, and how to make common changes without getting lost.

## What Django Is

Django is a Python web framework. It helps us build websites and web apps by giving us built-in tools for:

- URLs and routing
- HTML templates
- Databases and models
- User accounts and authentication
- Admin pages
- Forms
- Static files like CSS, JavaScript, and images

Instead of writing everything from scratch, Django gives us a structure to follow.

## Big Picture

A normal Django request works like this:

1. A user visits a URL in the browser.
2. Django checks the URL patterns.
3. Django sends the request to a view function.
4. The view function returns a response, usually an HTML template.
5. The browser displays the page.

Example:

```text
User visits /about/
        |
        v
config/urls.py
        |
        v
core/urls.py
        |
        v
core/views.py
        |
        v
templates/pages/about.html
```

## Project Structure

Our starter project will usually look something like this:

```text
project/
  accounts/
    forms.py
    urls.py
    views.py
  core/
    urls.py
    views.py
  config/
    settings.py
    urls.py
  static/
    css/
      style.css
    js/
      main.js
    images/
  templates/
    accounts/
      login.html
      profile.html
      register.html
    pages/
      home.html
      about.html
      dashboard.html
    partials/
      navbar.html
      footer.html
    base.html
  .env
  .env.example
  .gitignore
  Dockerfile
  docker-compose.yml
  manage.py
  requirements.txt
```

## Important Files

### `manage.py`

This is the command file for the Django project.

Common commands:

```bash
python manage.py runserver
python manage.py migrate
python manage.py makemigrations
python manage.py createsuperuser
python manage.py startapp app_name
```

### `config/settings.py`

This controls the main project settings.

It includes things like:

- Installed apps
- Template folders
- Static file settings
- Database settings
- Login/logout redirects
- Environment variables

Important examples:

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "accounts",
]
```

```python
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "home"
LOGIN_URL = "login"
```

### `config/urls.py`

This is the project-level URL file. It connects app URL files to the main project.

Example:

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("core.urls")),
]
```

### Apps

Django projects are split into apps. An app is a section of the project with a specific responsibility.

For this starter project:

- `core` handles basic pages like home, about, and dashboard.
- `accounts` handles register, login, logout, and profile pages.

Later, we might add apps like:

- `posts`
- `tasks`
- `events`
- `inventory`
- `courses`
- `teams`

## Templates

Templates are HTML files that Django can fill with dynamic data.

We use a base template so we do not repeat the same layout on every page.

### `templates/base.html`

This is the main layout used by all pages.

It usually includes:

- The HTML document structure
- The CSS file
- The navbar
- The main content block
- The footer

Example:

```html
{% load static %}

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Student Project{% endblock %}</title>
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
    {% include "partials/navbar.html" %}

    <main class="page">
        {% block content %}
        {% endblock %}
    </main>

    {% include "partials/footer.html" %}
    <script src="{% static 'js/main.js' %}"></script>
</body>
</html>
```

### Pages

A page template extends `base.html`.

Example:

```html
{% extends "base.html" %}

{% block title %}About | Student Project{% endblock %}

{% block content %}
<section class="content-section">
    <h1>About</h1>
    <p>This page explains the project.</p>
</section>
{% endblock %}
```

### Partials

Partials are reusable template pieces.

Examples:

- `templates/partials/navbar.html`
- `templates/partials/footer.html`

Use them when a section appears on multiple pages.

```html
{% include "partials/navbar.html" %}
```

## Views

Views are Python functions that decide what response to send back.

Example from `core/views.py`:

```python
from django.shortcuts import render


def home(request):
    return render(request, "pages/home.html")
```

This means:

- A request comes in.
- Django calls `home`.
- `home` renders the template `pages/home.html`.

## URLs

URLs connect browser paths to view functions.

Example from `core/urls.py`:

```python
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
```

The `name` lets us link to the URL inside templates:

```html
<a href="{% url 'about' %}">About</a>
```

This is better than hardcoding:

```html
<a href="/about/">About</a>
```

## Adding A New Page

To add a new page, do these three steps.

### 1. Add A View

In `core/views.py`:

```python
def contact(request):
    return render(request, "pages/contact.html")
```

### 2. Add A URL

In `core/urls.py`:

```python
path("contact/", views.contact, name="contact"),
```

### 3. Add A Template

Create `templates/pages/contact.html`:

```html
{% extends "base.html" %}

{% block title %}Contact | Student Project{% endblock %}

{% block content %}
<section class="content-section">
    <h1>Contact</h1>
    <p>This is the contact page.</p>
</section>
{% endblock %}
```

Then link to it:

```html
<a href="{% url 'contact' %}">Contact</a>
```

## Authentication

Django includes built-in user account tools.

Our starter account features include:

- Register
- Log in
- Log out
- Profile

### Locking Pages

To make a page only available to logged-in users, use `login_required`.

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard(request):
    return render(request, "pages/dashboard.html")
```

If a logged-out user tries to visit the dashboard, Django sends them to the login page.

### Hiding Navbar Links

In templates, use:

```html
{% if user.is_authenticated %}
    <a href="{% url 'dashboard' %}">Dashboard</a>
    <a href="{% url 'profile' %}">Profile</a>
{% else %}
    <a href="{% url 'login' %}">Log In</a>
    <a href="{% url 'register' %}">Sign Up</a>
{% endif %}
```

This only hides the links visually. To actually protect a page, still use `@login_required`.

## Static Files

Static files are files the browser downloads directly.

Examples:

- CSS
- JavaScript
- Images

Our structure:

```text
static/
  css/
    style.css
  js/
    main.js
  images/
```

To load static files in a template:

```html
{% load static %}
<link rel="stylesheet" href="{% static 'css/style.css' %}">
```

## Environment Variables

Environment variables keep private or changeable settings out of the code.

Examples:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- Email login values
- API keys

The real `.env` file should not be committed to GitHub.

The `.env.example` file should be committed so teammates know what variables they need.

Example `.env.example`:

```env
SECRET_KEY=replace-this
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

## Database Basics

Django uses models to define database tables.

Example:

```python
from django.db import models


class Task(models.Model):
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
```

After creating or changing models, run:

```bash
python manage.py makemigrations
python manage.py migrate
```

What these do:

- `makemigrations` creates migration files based on model changes.
- `migrate` applies those changes to the database.

## Admin Site

Django has a built-in admin site.

Create an admin user:

```bash
python manage.py createsuperuser
```

Start the server:

```bash
python manage.py runserver
```

Then visit:

```text
http://127.0.0.1:8000/admin/
```

To make a model appear in the admin, register it in that app's `admin.py`:

```python
from django.contrib import admin
from .models import Task

admin.site.register(Task)
```

## Docker Basics

Docker lets everyone run the project in a similar environment.

Common commands:

```bash
docker compose up --build
docker compose up
docker compose down
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

If using Docker, the site usually opens at:

```text
http://localhost:8000
```

## Git Team Workflow

Basic recommended workflow:

```bash
git pull
git checkout -b feature/my-feature-name
```

Make your changes, then:

```bash
git add .
git commit -m "Add my feature"
git push
```

Then open a pull request if your team is using GitHub.

Before starting new work, always pull the latest code:

```bash
git pull
```

## Common Development Tasks

### Start The Server Locally

```bash
python manage.py runserver
```

### Run Migrations

```bash
python manage.py migrate
```

### Create A New App

```bash
python manage.py startapp app_name
```

Then add it to `INSTALLED_APPS` in `config/settings.py`:

```python
INSTALLED_APPS = [
    ...
    "app_name",
]
```

### Add A New Page

1. Add a view in `views.py`.
2. Add a URL in `urls.py`.
3. Add a template in `templates/pages/`.
4. Add a navbar link if needed.

### Add A New Database Table

1. Create a model in `models.py`.
2. Run `python manage.py makemigrations`.
3. Run `python manage.py migrate`.
4. Register the model in `admin.py` if needed.

## Helpful Django Template Syntax

Variables:

```html
{{ user.username }}
```

If statements:

```html
{% if user.is_authenticated %}
    <p>You are logged in.</p>
{% endif %}
```

For loops:

```html
{% for item in items %}
    <p>{{ item }}</p>
{% endfor %}
```

Extending a base template:

```html
{% extends "base.html" %}
```

Defining page content:

```html
{% block content %}
    <h1>Hello</h1>
{% endblock %}
```

Including a partial:

```html
{% include "partials/navbar.html" %}
```

Linking to a named URL:

```html
<a href="{% url 'dashboard' %}">Dashboard</a>
```

## Recommended Rules For Our Team

- Keep reusable layout code in `base.html` and `partials/`.
- Put normal pages in `templates/pages/`.
- Put account pages in `templates/accounts/`.
- Use named URLs with `{% url 'name' %}` instead of hardcoded paths.
- Protect private pages with `@login_required`.
- Do not commit `.env`.
- Do not commit `.venv`.
- Run migrations after changing models.
- Keep commits focused and use clear commit messages.
- Pull the latest code before starting work.

## Quick Mental Model

If you are adding a page, think:

```text
URL -> view -> template
```

If you are adding database data, think:

```text
model -> migration -> database -> view -> template
```

If something is private, think:

```text
@login_required on the view
```

If something appears on every page, think:

```text
base.html or partials/
```

## Good First Features To Practice

Before the real project idea is final, teammates can practice by adding:

- A contact page
- A team page
- A user settings page
- A simple model
- A model shown in the admin
- A form that saves data
- A page that lists database records

These are small enough to learn Django without creating a messy project early.

