from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create a superuser'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser('admin', 'admin@example.com', '0711169847')
            self.stdout.write(self.style.SUCCESS('Superuser created.'))
        else:
            self.stdout.write(self.style.WARNING('Superuser already exists.'))

