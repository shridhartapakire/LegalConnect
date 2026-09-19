#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def main() -> None:
    """Run Django management commands."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "legalconnect.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover - standard Django bootstrap guard
        raise ImportError(
            "Couldn't import Django. Install the project requirements first."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
