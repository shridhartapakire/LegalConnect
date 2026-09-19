# Legal Connect

Legal Connect is a production-oriented legal-services platform being planned for Chikodi and surrounding areas. It is designed to help clients find advocates and manage consultation workflows with privacy, security, and clear boundaries.

## Current phase

**Phase 1 — project foundation.** This repository currently provides secure account foundations, client/advocate profile shells, role-based dashboard access, a public landing page, Django administration, and health checking.

It does **not** yet implement advocate verification, public advocate discovery, consultations, appointments, messaging, document uploads, payments, video, notification delivery, or AI.

## Technology stack

- Python and Django
- Django templates and forms for the web interface
- Django REST Framework, available for focused future APIs
- PostgreSQL configuration for production; SQLite for simple local development
- `python-dotenv` for local environment variables
- `psycopg` PostgreSQL driver

## Local setup

See [SETUP.md](SETUP.md) for beginner-friendly instructions. In short:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in a browser. The health endpoint is `http://127.0.0.1:8000/health/`.

## Environment configuration

Copy `.env.example` to `.env`; `.env` is ignored by Git. Local development uses SQLite when `DATABASE_URL` is blank. Production requires:

- `ENVIRONMENT=production`
- `DEBUG=false`
- a unique `SECRET_KEY`
- a PostgreSQL `DATABASE_URL`
- explicit `ALLOWED_HOSTS`

Never commit secrets, database URLs containing credentials, or real legal-service data.

## Tests and checks

```powershell
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```

## Project boundaries

The approved planning documents remain the source of truth. This is a modular Django monolith: `apps.accounts` owns identity, roles, and profile foundations; `apps.core` owns public/shared UI and protected dashboard shells. Later approved phases will add domains only when their workflows are implemented.
