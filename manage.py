#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from django.core.management.base import CommandError
from django.contrib.auth.management.commands.createsuperuser import Command as CreateSuperUserCommand

def create_superuser():
    """Create a superuser if the environment variable is set."""
    if os.environ.get('CREATE_SUPERUSER', 'False') == 'True':
        try:
            CreateSuperUserCommand().execute(
                username=os.environ.get('DJANGO_SUPERUSER_USERNAME'),
                email=os.environ.get('DJANGO_SUPERUSER_EMAIL'),
                password=os.environ.get('DJANGO_SUPERUSER_PASSWORD'),
                interactive=False
            )
        except CommandError:
            print("Superuser already exists.")

def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gigconnect1.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    create_superuser()  # Call the function to create the superuser
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()























































