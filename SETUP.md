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

## Advocate verification workflow in development

1. Create a local advocate account at `/account/register/ADVOCATE/`.
2. Complete the professional profile from the advocate dashboard.
3. Create a local administrator with `python manage.py createsuperuser` and sign in at `/admin/`.
4. In Django administration, configure the verification evidence types required by your approved platform policy. Do not invent or publish a legal policy merely for testing.
5. Return to the advocate dashboard, start the verification application, upload allowed evidence, and submit it.
6. Staff review is available at `/verification/management/` for a signed-in staff user.

The local project deliberately has no malware-scanning provider. Uploaded verification evidence remains quarantined and cannot be downloaded until a real scanning integration marks it safe. Do not use local uploads as real professional evidence.

## 7. Run checks and tests

In a second PowerShell window with the virtual environment activated:

```powershell
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```

## Consultation requests in development

Only an advocate whose profile is complete, verified through the staff workflow, and published appears at `/advocates/`. A signed-in client can submit a minimal consultation request from that advocate's public profile. The advocate can review, accept, or decline it from `/advocate/requests/`.

This is not appointment booking, messaging, payment processing, or a representation agreement. Do not enter real client matter details into a local development database.

## Client profiles in development

Every client registration creates a private client profile. A signed-in client can manage their display name and optional preferred language/locality at `/account/client/profile/` or through the client dashboard. These preferences use the administrator-managed taxonomy records and are not public or automatically shared with advocates.

## Optional: access Django administration locally

Create an administrator only for your local environment:

```powershell
python manage.py createsuperuser
```

Then visit `http://127.0.0.1:8000/admin/`. This command creates an account in your local database; it does not create a public advocate or client profile.

## Production note

Before deployment, use a managed PostgreSQL database and configure `ENVIRONMENT=production`, `DEBUG=false`, a strong unique `SECRET_KEY`, `DATABASE_URL`, and `ALLOWED_HOSTS`. The approved deployment and security documents contain the required pre-launch controls.
