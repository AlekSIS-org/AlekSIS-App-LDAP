from django.apps import apps
from django.contrib.auth import get_user_model

from constance import config

def ldap_create_user(sender, **kwargs):
    Person = apps.get_model("core", "Person")

    if config.ENABLE_LDAP_SYNC:
        if not sender.person:
            if config.LDAP_MATCHING_FIELDS == 'match-email':
                person, created = Person.objects.get_or_create(
                    email=sender.email,
                    defaults={
                        "first_name": sender.first_name,
                        "last_name": sender.last_name,
                    }
                )
            elif config.LDAP_MATCHING_FIELDS == 'match-name':
                person, created = Person.objects.get_or_create(
                    first_name=sender.first_name,
                    last_name=sender.last_name,
                    defaults={
                        "email": sender.email
                    }
                )
            elif config.LDAP_MATCHING_FIELDS == 'match-email-name':
                person, created = Person.objects.get_or_create(
                    first_name=sender.first_name,
                    last_name=sender.last_name,
                    email=sender.email
                )

            if config.LDAP_SYNC_CREATE or not created:
                person.user = sender
                person.save()
