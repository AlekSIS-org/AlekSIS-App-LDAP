from django.core.management.base import BaseCommand

from ...tasks import ldap_import


class Command(BaseCommand):
    def handle(self, *args, **options):
        ldap_import()
