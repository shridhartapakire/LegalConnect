"""ASGI configuration for Legal Connect."""

import os

from django.core.asgi import get_asgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "legalconnect.settings")
application = get_asgi_application()
