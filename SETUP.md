# Beginner Setup Guide

These instructions run Legal Connect on your own computer for development. They do not deploy the application or create any real advocate/client data.

## 1. Check Python

Open PowerShell in this project folder and run:

```powershell
python --version
```

Use Python 3.12 or newer. If the command is not found, install Python from [python.org](https://www.python.org/downloads/) and reopen PowerShell.

## 2. Create and activate a virtual environment

This keeps the project's packages separate from other Python projects.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run the following once for your current terminal, then retry the activation command:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## 3. Install project packages

```powershell
python -m pip install -r requirements.txt
```

## 4. Create your local environment file

```powershell
Copy-Item .env.example .env
```

For local development, leave `DATABASE_URL` blank. Django will use a local SQLite database file that is ignored by Git. Do not put a production secret key or production database password in a shared file.

## 5. Create the local database tables

```powershell
python manage.py migrate
```

## 6. Start the development server

```powershell
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`. Stop the server with `Ctrl+C`.

## 7. Run checks and tests

In a second PowerShell window with the virtual environment activated:

```powershell
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```

## Optional: access Django administration locally

Create an administrator only for your local environment:

```powershell
python manage.py createsuperuser
```

Then visit `http://127.0.0.1:8000/admin/`. This command creates an account in your local database; it does not create a public advocate or client profile.

## Production note

Before deployment, use a managed PostgreSQL database and configure `ENVIRONMENT=production`, `DEBUG=false`, a strong unique `SECRET_KEY`, `DATABASE_URL`, and `ALLOWED_HOSTS`. The approved deployment and security documents contain the required pre-launch controls.
