# Create groups management command or do it in Django admin
# management/commands/create_groups.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

from utils.sidebar import UserRole
# from portal.models import UserRole

class Command(BaseCommand):
    help = 'Create user groups based on UserRole enum'
    
    def handle(self, *args, **options):
        for role in UserRole:
            group, created = Group.objects.get_or_create(name=role.value)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created group: {role.value}'))
            else:
                self.stdout.write(self.style.WARNING(f'Group already exists: {role.value}'))