"""
WSGI config for gigconnect1 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gigconnect1.settings")

application = get_wsgi_application()

# Automatically create superuser if it doesn't exist
from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username=os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')).exists():
    User.objects.create_superuser(
        username=os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin'),
        email=os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com'),
        password=os.getenv('DJANGO_SUPERUSER_PASSWORD', '0711169847')
    )
    print("Superuser created.")
else:
    print("Superuser already exists.")
